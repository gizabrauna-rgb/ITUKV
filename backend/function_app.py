import azure.functions as func
import json
import os
import uuid
import hmac
import hashlib
import base64
import secrets
from datetime import datetime, timedelta
from azure.data.tables import TableServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

TABLE_CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Content-Type": "application/json",
}


def ok_(data, status=200):
    return func.HttpResponse(json.dumps(data, default=str), status_code=status, headers=CORS)

def err_(msg, status=400):
    return func.HttpResponse(json.dumps({"error": msg}), status_code=status, headers=CORS)

def opt_():
    return func.HttpResponse("", status_code=204, headers=CORS)

def table_(name):
    svc = TableServiceClient.from_connection_string(TABLE_CONN)
    svc.create_table_if_not_exists(name)
    return svc.get_table_client(name)


# Blacklist-Check: verhindert Import gesperrter E-Mails / Domains
_BLACKLIST_CACHE = None
def is_blacklisted(email):
    global _BLACKLIST_CACHE
    if not email:
        return False
    if _BLACKLIST_CACHE is None:
        _BLACKLIST_CACHE = {"emails": set(), "domains": set()}
        try:
            tc = table_("blacklist")
            for b in tc.list_entities():
                pk = b.get("PartitionKey","")
                if pk == "blacklist":
                    _BLACKLIST_CACHE["emails"].add((b.get("email","") or "").lower())
                elif pk == "blacklist-domain":
                    _BLACKLIST_CACHE["domains"].add((b.get("domain","") or "").lower())
        except Exception:
            pass
    email = email.lower().strip()
    if email in _BLACKLIST_CACHE["emails"]:
        return True
    domain = email.split("@")[1] if "@" in email else ""
    return domain in _BLACKLIST_CACHE["domains"]


_PLZ = None
def get_plz_coords():
    global _PLZ
    if _PLZ is not None:
        return _PLZ
    _PLZ = {}
    try:
        import csv
        csv_path = os.path.join(os.path.dirname(__file__), "plz_geocoord.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                plz = (row.get("plz") or "").strip()
                if not plz:
                    continue
                try:
                    _PLZ[plz] = (float(row["lat"]), float(row["lon"]))
                except Exception:
                    continue
    except Exception:
        pass
    return _PLZ


def _b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode('ascii')


def _b64ud(s):
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def make_jwt(uid, role, name, email):
    payload = {"id": uid, "role": role, "name": name, "email": email,
               "exp": int((datetime.utcnow() + timedelta(days=7)).timestamp())}
    h = _b64u(json.dumps({"alg":"HS256","typ":"JWT"}, separators=(',',':')).encode())
    p = _b64u(json.dumps(payload, separators=(',',':'), default=str).encode())
    sig = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64u(sig)}"


_last_seen_cache = {}  # uid -> unix_ts (throttle DB writes)

def _touch_last_seen(uid):
    if not uid:
        return
    now = datetime.utcnow().timestamp()
    if now - _last_seen_cache.get(uid, 0) < 60:
        return
    _last_seen_cache[uid] = now
    try:
        tc = table_("users")
        ent = tc.get_entity("user", uid)
        ent["lastSeen"] = datetime.utcnow().isoformat()
        tc.update_entity(dict(ent))
    except Exception:
        pass


def auth_user(req):
    a = req.headers.get("Authorization", "")
    if not a.startswith("Bearer "):
        return None
    try:
        h, p, s = a[7:].split('.')
        expected = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64ud(s), expected):
            return None
        payload = json.loads(_b64ud(p))
        _touch_last_seen(payload.get("id"))
        return payload
    except Exception:
        return None


@app.route(route="ping", methods=["GET"])
def ping(req: func.HttpRequest) -> func.HttpResponse:
    return ok_({"status": "ok"})


@app.route(route="auth/resolve", methods=["POST", "OPTIONS"])
def auth_resolve(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json()
    email = body.get("email", "").lower().strip()
    name = body.get("name", "")
    if not email:
        return err_("E-Mail erforderlich", 400)
    tc = table_("users")
    users = list(tc.query_entities(f"email eq '{email}'"))
    if users:
        u = users[0]
        token = make_jwt(u["RowKey"], u["role"], u.get("name", name), email)
        return ok_({"token": token, "role": u["role"], "name": u.get("name", name), "id": u["RowKey"]})

    # Bootstrap: nur wenn noch GAR KEIN User existiert, wird der erste Login zum Admin.
    # Sonst: Zugriff verweigert. Neue Nutzer muessen vom Admin im Dashboard angelegt werden.
    any_user = next(iter(tc.list_entities(results_per_page=1)), None)
    if any_user is not None:
        return err_("Kein Zugang. Bitte wende dich an den Administrator.", 403)

    uid = str(uuid.uuid4())
    tc.create_entity({
        "PartitionKey": "user", "RowKey": uid, "email": email,
        "passwordHash": "", "role": "admin", "name": name,
        "createdAt": datetime.utcnow().isoformat(),
    })
    return ok_({"token": make_jwt(uid, "admin", name, email), "role": "admin", "name": name, "id": uid})


@app.route(route="stats", methods=["GET", "OPTIONS"])
def stats_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    try:
        t = sum(1 for _ in table_("targets").list_entities())
        k = sum(1 for _ in table_("kontakte").list_entities())
        return ok_({"aktiveTargets": t, "offeneNdas": 0, "investorenGesamt": k, "dealsAbgeschlossen": 0})
    except Exception:
        return ok_({"aktiveTargets": 0, "offeneNdas": 0, "investorenGesamt": 0, "dealsAbgeschlossen": 0})


@app.route(route="targets", methods=["GET", "POST", "OPTIONS"])
def targets_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    tc = table_("targets")
    if req.method == "GET":
        items = [dict(i) for i in tc.list_entities()]
        return ok_(items)
    # POST – neues Target
    body = req.get_json()
    tid = str(uuid.uuid4())
    # Minimale Phasen-Vorlage (15 Master-Phasen, ohne Aufgabenliste – die
    # detaillierte Liste setzt PhasenProzess.vue beim ersten Oeffnen)
    phasen_titel = [
        "UVE Start – Vorbereitungs-Checkliste",
        "UVE Abschluss – Verkaufsmandat-Eroeffnung",
        "Marktansprache – Interessenten anschreiben",
        "NDA von Interessenten abholen",
        "Erstes Kennenlernen – Interessent Verkaeufer",
        "Datenraum / Kommunikationsraum in Element",
        "Austausch von Unterlagen",
        "Indikatives Angebot",
        "Verhandlungen",
        "Letter of Intent (LOI)",
        "Due Diligence",
        "Vertragsgestaltung",
        "Notartermin & Closing",
        "Post-Closing – Uebergabe & Kommunikation",
        "Erfolgsmeldung & Abrechnung",
    ]
    init_phasen = [{"id": i+1, "titel": f"{i+1}. {t}", "notiz": "", "aufgaben": []} for i, t in enumerate(phasen_titel)]
    entity = {
        "PartitionKey": "target", "RowKey": tid,
        "mbNr": body.get("mbNr", ""),
        "verkaueferName": body.get("verkaueferName", ""),
        "region": body.get("region", ""),
        "plz": body.get("plz", ""),
        "branche": body.get("branche", ""),
        "mitarbeiter": str(body.get("mitarbeiter", "")),
        "umsatz": body.get("umsatz", ""),
        "beschreibung": body.get("beschreibung", ""),
        "projekttyp": body.get("projekttyp", "Projekt Target"),
        "status": "verfuegbar",
        "createdAt": datetime.utcnow().isoformat(),
        "phasenJson": json.dumps(init_phasen, ensure_ascii=False),
    }
    tc.create_entity(entity)
    return ok_(dict(entity), 201)


@app.route(route="target-get", methods=["POST", "OPTIONS"])
def target_get(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    tid = body.get("id", "")
    if not tid:
        return err_("id erforderlich", 400)
    try:
        entity = table_("targets").get_entity("target", tid)
        return ok_(dict(entity))
    except Exception:
        return err_("Target nicht gefunden", 404)


@app.route(route="target-update", methods=["POST", "OPTIONS"])
def target_update(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    tid = body.pop("id", "")
    if not tid:
        return err_("id erforderlich", 400)
    tc = table_("targets")
    try:
        entity = tc.get_entity("target", tid)
    except Exception:
        return err_("Target nicht gefunden", 404)
    for k, v in body.items():
        if k not in ("PartitionKey", "RowKey"):
            entity[k] = v
    tc.update_entity(dict(entity))
    return ok_(dict(entity))


@app.route(route="kontakt-create", methods=["POST", "OPTIONS"])
def kontakt_create(req: func.HttpRequest) -> func.HttpResponse:
    """Anlegen + Update von Kontakten mit Dedup-Check auf firma."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    firma = (body.get("firma") or "").strip()
    if not firma:
        return err_("Firma erforderlich", 400)
    tc = table_("kontakte")
    # Dedup-Check: existiert Firma schon (case-insensitive)?
    existing = None
    try:
        items = list(tc.list_entities())
        for it in items:
            if (it.get("firma") or "").strip().lower() == firma.lower():
                existing = dict(it)
                break
    except Exception:
        pass
    entity = {
        "PartitionKey": "kontakt",
        "RowKey": (existing or {}).get("RowKey") or str(uuid.uuid4()),
        "firma": firma,
        "name": body.get("name", ""),
        "email": body.get("email", ""),
        "telefon": body.get("telefon", ""),
        "website": body.get("website", ""),
        "plz": body.get("plz", ""),
        "ort": body.get("ort", ""),
        "sucht": body.get("sucht", ""),
        "bietet": body.get("bietet", ""),
        "kommentar": body.get("kommentar", ""),
        "istKunde": bool(body.get("istKunde", False)),
        "istExKunde": bool(body.get("istExKunde", False)),
        "istInvestor": bool(body.get("istInvestor", False)),
        "istTarget": bool(body.get("istTarget", False)),
        "investorTyp": body.get("investorTyp", ""),
        "typ": body.get("investorTyp", "") if body.get("istInvestor") else "",
        "kundenstatus": "Kunde" if body.get("istKunde") else (
            "Ex-Kunde" if body.get("istExKunde") else (
            "Investor" if body.get("istInvestor") else (
            "Target" if body.get("istTarget") else ""))),
        "updatedAt": datetime.utcnow().isoformat(),
    }
    if existing:
        entity["createdAt"] = existing.get("createdAt", datetime.utcnow().isoformat())
        try:
            tc.update_entity(entity, mode="replace")
            return ok_({"updated": True, "id": entity["RowKey"]})
        except Exception as ex:
            return err_(f"Update fehlgeschlagen: {ex}", 500)
    entity["createdAt"] = datetime.utcnow().isoformat()
    try:
        tc.create_entity(entity)
        return ok_({"created": True, "id": entity["RowKey"]}, 201)
    except Exception as ex:
        return err_(f"Anlegen fehlgeschlagen: {ex}", 500)


@app.route(route="kontakte", methods=["GET", "OPTIONS"])
def kontakte_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    items = [dict(i) for i in table_("kontakte").list_entities()]
    return ok_(items)


@app.route(route="users", methods=["GET", "OPTIONS"])
def users_list(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    items = [dict(u) for u in table_("users").list_entities()]
    for u in items:
        u.pop("passwordHash", None)
    return ok_(items)


@app.route(route="user-create", methods=["POST", "OPTIONS"])
def user_create(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    email = body.get("email","").lower().strip()
    if not email:
        return err_("E-Mail erforderlich", 400)
    tc = table_("users")
    existing = list(tc.query_entities(f"email eq '{email}'"))
    if existing:
        return err_("E-Mail bereits registriert", 409)
    import string
    pw = body.get("password") or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    salt = secrets.token_bytes(16)
    pw_hash = "pbkdf2$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 100000)).decode()
    uid = str(uuid.uuid4())
    entity = {
        "PartitionKey": "user", "RowKey": uid, "email": email,
        "passwordHash": pw_hash,
        "role": body.get("role", "target"),
        "name": body.get("name", ""),
        "targetId": body.get("targetId", ""),
        "createdAt": datetime.utcnow().isoformat(),
    }
    tc.create_entity(entity)

    # Begruessungsmail mit Login-Daten an neuen User
    acs_conn = os.environ.get("ACS_CONNECTION_STRING", "")
    acs_sender = os.environ.get("ACS_SENDER_ADDRESS", "DoNotReply@mail.itukv.de")
    frontend = os.environ.get("FRONTEND_BASE_URL", "https://dashboard.itukv.de")
    if acs_conn:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(acs_conn)
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                <h2 style="color:#097e92">Willkommen im ITUKV Dashboard</h2>
                <p>Hallo {entity.get('name') or ''},</p>
                <p>fuer dich wurde ein Zugang zum ITUKV Dashboard angelegt.</p>
                <p><strong>Deine Login-Daten:</strong></p>
                <table cellpadding="6" style="background:#f0fdfa;border-radius:8px;border-collapse:separate">
                  <tr><td>E-Mail:</td><td><strong>{email}</strong></td></tr>
                  <tr><td>Initial-Passwort:</td><td><strong style="font-family:monospace;font-size:15px">{pw}</strong></td></tr>
                </table>
                <p style="margin-top:24px"><a href="{frontend}" style="background:#097e92;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Jetzt einloggen</a></p>
                <p style="font-size:12px;color:#666">Aus Sicherheitsgruenden empfehlen wir, das Passwort nach der ersten Anmeldung zu aendern.</p>
                <p>Bei Fragen melde dich bei deinem mibeca-Ansprechpartner.</p>
                </body></html>"""
            client.begin_send({
                "senderAddress": acs_sender,
                "recipients": {"to": [{"address": email}]},
                "content": {"subject": "Dein Zugang zum ITUKV Dashboard", "plainText": f"Login: {email} / Passwort: {pw} / URL: {frontend}", "html": html},
            })
        except Exception as ex:
            logging.warning(f"Begruessungsmail fehlgeschlagen: {ex}") if 'logging' in dir() else None

    return ok_({"id": uid, "email": email, "role": entity["role"], "name": entity["name"], "initialPassword": pw}, 201)


@app.route(route="login", methods=["POST", "OPTIONS"])
def login_password(req: func.HttpRequest) -> func.HttpResponse:
    """Login mit E-Mail + Passwort (fuer Kunden ohne Microsoft-Konto)."""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    email = (body.get("email") or "").lower().strip()
    pw = body.get("password") or ""
    if not (email and pw):
        return err_("E-Mail und Passwort erforderlich", 400)
    tc = table_("users")
    users = list(tc.query_entities(f"email eq '{email}'"))
    if not users:
        return err_("Login fehlgeschlagen", 401)
    u = dict(users[0])
    stored = u.get("passwordHash", "") or ""
    if not stored.startswith("pbkdf2$"):
        return err_("Kein Passwort-Login fuer diese E-Mail. Bitte ueber Microsoft anmelden.", 401)
    try:
        _, salt_b64, hash_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        actual = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 100000)
        if not hmac.compare_digest(expected, actual):
            return err_("Login fehlgeschlagen", 401)
    except Exception:
        return err_("Login fehlgeschlagen", 401)
    token = make_jwt(u["RowKey"], u.get("role", "target"), u.get("name", ""), email)
    return ok_({
        "token": token,
        "role": u.get("role", "target"),
        "name": u.get("name", ""),
        "id": u["RowKey"],
        "targetId": u.get("targetId", ""),
    })


@app.route(route="user-delete", methods=["POST", "OPTIONS"])
def user_delete(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    uid = body.get("id","")
    if not uid:
        return err_("id erforderlich", 400)
    try:
        table_("users").delete_entity("user", uid)
        return ok_({"deleted": True})
    except Exception:
        return err_("Benutzer nicht gefunden", 404)


@app.route(route="user-reset-password", methods=["POST", "OPTIONS"])
def user_reset_password(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    uid = body.get("id","")
    send_mail = bool(body.get("sendMail", True))
    if not uid:
        return err_("id erforderlich", 400)
    tc = table_("users")
    try:
        entity = tc.get_entity("user", uid)
    except Exception:
        return err_("Benutzer nicht gefunden", 404)
    import string
    pw = body.get("password") or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    salt = secrets.token_bytes(16)
    entity["passwordHash"] = "pbkdf2$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 100000)).decode()
    tc.update_entity(dict(entity))

    mail_sent = False
    if send_mail and ACS_CONN and entity.get("email"):
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                <h2 style="color:#097e92">Neues Passwort fuer das ITUKV Dashboard</h2>
                <p>Hallo {entity.get('name') or ''},</p>
                <p>dein Passwort fuer das ITUKV Dashboard wurde zurueckgesetzt.</p>
                <p><strong>Deine neuen Login-Daten:</strong></p>
                <table cellpadding="6" style="background:#f0fdfa;border-radius:8px;border-collapse:separate">
                  <tr><td>E-Mail:</td><td><strong>{entity.get('email')}</strong></td></tr>
                  <tr><td>Neues Passwort:</td><td><strong style="font-family:monospace;font-size:15px">{pw}</strong></td></tr>
                </table>
                <p style="margin-top:24px"><a href="{FRONTEND_BASE}" style="background:#097e92;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Jetzt einloggen</a></p>
                <p style="font-size:12px;color:#666">Aus Sicherheitsgruenden empfehlen wir, dass du das Passwort nach der ersten Anmeldung aenderst.</p>
                </body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": entity["email"]}]},
                "content": {"subject": "Neues Passwort – ITUKV Dashboard", "plainText": f"Neues Passwort: {pw} / URL: {FRONTEND_BASE}", "html": html},
            })
            mail_sent = True
        except Exception:
            mail_sent = False

    return ok_({"email": entity.get("email"), "newPassword": pw, "mailSent": mail_sent})


@app.route(route="password-forgot", methods=["POST", "OPTIONS"])
def password_forgot(req: func.HttpRequest) -> func.HttpResponse:
    """Self-Service Passwort-Reset: Nutzer gibt E-Mail ein, bekommt neues Passwort per Mail.
    Aus Sicherheitsgruenden geben wir IMMER 200 zurueck, egal ob die E-Mail existiert."""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    email = (body.get("email") or "").lower().strip()
    if not email:
        return err_("E-Mail erforderlich", 400)
    try:
        users = list(table_("users").query_entities(f"email eq '{email}'"))
    except Exception:
        users = []
    if users:
        u = dict(users[0])
        import string
        pw = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        salt = secrets.token_bytes(16)
        u["passwordHash"] = "pbkdf2$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 100000)).decode()
        try:
            table_("users").update_entity(u)
        except Exception:
            return ok_({"ok": True})
        if ACS_CONN:
            try:
                from azure.communication.email import EmailClient
                client = EmailClient.from_connection_string(ACS_CONN)
                html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                    <h2 style="color:#097e92">Passwort zuruecksetzen</h2>
                    <p>Hallo {u.get('name') or ''},</p>
                    <p>du hast ein neues Passwort fuer das ITUKV Dashboard angefordert.</p>
                    <p><strong>Deine neuen Login-Daten:</strong></p>
                    <table cellpadding="6" style="background:#f0fdfa;border-radius:8px;border-collapse:separate">
                      <tr><td>E-Mail:</td><td><strong>{u.get('email')}</strong></td></tr>
                      <tr><td>Neues Passwort:</td><td><strong style="font-family:monospace;font-size:15px">{pw}</strong></td></tr>
                    </table>
                    <p style="margin-top:24px"><a href="{FRONTEND_BASE}" style="background:#097e92;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Jetzt einloggen</a></p>
                    <p style="font-size:12px;color:#666">Falls du dieses Passwort nicht angefordert hast, ignoriere diese Mail. Aenderungen am Account werden nur ueber diesen Link aktiviert.</p>
                    </body></html>"""
                client.begin_send({
                    "senderAddress": ACS_SENDER,
                    "recipients": {"to": [{"address": u["email"]}]},
                    "content": {"subject": "Passwort zuruecksetzen – ITUKV Dashboard", "plainText": f"Neues Passwort: {pw} / URL: {FRONTEND_BASE}", "html": html},
                })
            except Exception:
                pass
    return ok_({"ok": True})


@app.route(route="plz-resolve", methods=["POST", "OPTIONS"])
def plz_resolve(req: func.HttpRequest) -> func.HttpResponse:
    """PLZ -> Koordinaten (für Radius-Filter auf der Karte)."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    plz = str(body.get("plz","")).strip()
    if not plz:
        return err_("plz erforderlich", 400)
    coords = get_plz_coords()
    c = coords.get(plz)
    if c:
        return ok_({"plz": plz, "lat": c[0], "lon": c[1], "exact": True})
    # Prefix-Match (längster zuerst)
    for length in range(len(plz) - 1, 0, -1):
        prefix = plz[:length]
        for cand_plz, latlon in coords.items():
            if cand_plz.startswith(prefix):
                return ok_({"plz": cand_plz, "lat": latlon[0], "lon": latlon[1], "exact": False, "matched": cand_plz})
    return err_("PLZ nicht gefunden", 404)


@app.route(route="kontakte/locations", methods=["GET", "OPTIONS"])
def kontakte_locations_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    coords = get_plz_coords()

    # Kontakte
    kontakte_items = [dict(i) for i in table_("kontakte").list_entities()]
    kontakte_out = []
    without_k = 0
    flag_fields = ['hatUC','hatUCS','hatMC','hatFKE','hatUVE','hatVME','hatKIwerkOne','hatMSQ','hatKMQ','hatKIT']
    for k in kontakte_items:
        plz = str(k.get("plz","")).strip()
        c = coords.get(plz)
        if c:
            entry = {
                "id": k.get("RowKey"),
                "firma": k.get("firma","") or k.get("name",""),
                "name": k.get("name",""),
                "email": k.get("email",""),
                "telefon": k.get("telefon",""),
                "plz": k.get("plz",""),
                "ort": k.get("ort",""),
                "typ": k.get("typ","") or k.get("kundenstatus",""),
                "kundenstatus": k.get("kundenstatus",""),
                "lat": c[0], "lon": c[1],
            }
            # Produkt-Flags
            for f in flag_fields:
                if k.get(f) is True:
                    entry[f] = True
            kontakte_out.append(entry)
        else:
            without_k += 1

    # Targets (Verkäufer)
    targets_items = [dict(i) for i in table_("targets").list_entities()]
    targets_out = []
    for t in targets_items:
        plz = str(t.get("plz","")).strip()
        c = coords.get(plz)
        if c:
            targets_out.append({
                "id": t.get("RowKey"),
                "mbNr": t.get("mbNr",""),
                "verkaueferName": t.get("verkaueferName",""),
                "firma": t.get("firma",""),
                "region": t.get("region",""),
                "ort": t.get("region","") or t.get("ort",""),
                "plz": t.get("plz",""),
                "lat": c[0], "lon": c[1],
                "typ": "TARGET",
            })

    return ok_({
        "kontakte": kontakte_out,
        "targets": targets_out,
        "total": len(kontakte_items),
        "withoutCoords": without_k,
    })


# =========================================================================
# AUSSCHREIBUNGEN — Tender-Verwaltung pro Target
# =========================================================================

@app.route(route="ausschreibungen", methods=["GET", "POST", "OPTIONS"])
def ausschreibungen_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    tc = table_("ausschreibungen")
    if req.method == "GET":
        items = [dict(i) for i in tc.list_entities()]
        return ok_(items)
    # POST – neue Ausschreibung
    if p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    aid = str(uuid.uuid4())
    entity = {
        "PartitionKey": "ausschreibung", "RowKey": aid,
        "targetId": body.get("targetId", ""),
        "mbNr": body.get("mbNr", ""),
        "titel": body.get("titel", ""),
        "region": body.get("region", ""),
        "branche": body.get("branche", ""),
        "mitarbeiter": str(body.get("mitarbeiter", "")),
        "umsatz": body.get("umsatz", ""),
        "kurzprofil": body.get("kurzprofil", ""),
        "status": body.get("status", "aktiv"),
        "createdAt": datetime.utcnow().isoformat(),
    }
    tc.create_entity(entity)
    return ok_(dict(entity), 201)


@app.route(route="ausschreibung-update", methods=["POST", "OPTIONS"])
def ausschreibung_update(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    aid = body.pop("id", "")
    if not aid:
        return err_("id erforderlich", 400)
    tc = table_("ausschreibungen")
    try:
        ent = tc.get_entity("ausschreibung", aid)
    except Exception:
        return err_("Ausschreibung nicht gefunden", 404)
    for k, v in body.items():
        if k not in ("PartitionKey", "RowKey"):
            ent[k] = v
    tc.update_entity(dict(ent))
    return ok_(dict(ent))


@app.route(route="ausschreibung-delete", methods=["POST", "OPTIONS"])
def ausschreibung_delete(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    aid = body.get("id", "")
    if not aid:
        return err_("id erforderlich", 400)
    try:
        table_("ausschreibungen").delete_entity("ausschreibung", aid)
        return ok_({"deleted": True})
    except Exception:
        return err_("Ausschreibung nicht gefunden", 404)


# =========================================================================
# INTERESSENTEN — Pro Target / Pro Ausschreibung
# =========================================================================

@app.route(route="interessenten", methods=["POST", "OPTIONS"])
def interessenten_list(req: func.HttpRequest) -> func.HttpResponse:
    """POST {targetId: "..."} → Liste der Interessenten fuer dieses Target."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    if not target_id:
        return err_("targetId erforderlich", 400)
    # Targets duerfen nur ihre eigenen Interessenten sehen
    if p.get("role") == "target" and p.get("targetId") and p.get("targetId") != target_id:
        return err_("Nicht autorisiert", 403)
    tc = table_("interessenten")
    items = [dict(i) for i in tc.query_entities(f"targetId eq '{target_id}'")]
    return ok_(items)


@app.route(route="interessent-create", methods=["POST", "OPTIONS"])
def interessent_create(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    iid = str(uuid.uuid4())
    entity = {
        "PartitionKey": "interessent", "RowKey": iid,
        "targetId": body.get("targetId", ""),
        "ausschreibungId": body.get("ausschreibungId", ""),
        "firma": body.get("firma", ""),
        "name": body.get("name", ""),
        "email": body.get("email", ""),
        "telefon": body.get("telefon", ""),
        "plz": body.get("plz", ""),
        "ort": body.get("ort", ""),
        "typ": body.get("typ", ""),  # PE / Strategisch / Systemhausgruppe
        "ndaStatus": body.get("ndaStatus", "ausstehend"),
        "rating": int(body.get("rating", 0)),
        "veto": bool(body.get("veto", False)),
        "vetoBegruendung": body.get("vetoBegruendung", ""),
        "freigegebenFuerKontakt": bool(body.get("freigegebenFuerKontakt", False)),
        "notiz": body.get("notiz", ""),
        "createdAt": datetime.utcnow().isoformat(),
    }
    tc = table_("interessenten")
    tc.create_entity(entity)
    return ok_(dict(entity), 201)


@app.route(route="interessent-update", methods=["POST", "OPTIONS"])
def interessent_update(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    iid = body.pop("id", "")
    if not iid:
        return err_("id erforderlich", 400)
    tc = table_("interessenten")
    try:
        ent = tc.get_entity("interessent", iid)
    except Exception:
        return err_("Interessent nicht gefunden", 404)
    # Targets duerfen nur eigene Interessenten aendern (nur rating, veto, freigabe, notiz)
    if p.get("role") == "target":
        if p.get("targetId") != ent.get("targetId"):
            return err_("Nicht autorisiert", 403)
        allowed = {"rating", "veto", "vetoBegruendung", "freigegebenFuerKontakt", "notiz"}
        body = {k: v for k, v in body.items() if k in allowed}
    for k, v in body.items():
        if k not in ("PartitionKey", "RowKey"):
            ent[k] = v
    tc.update_entity(dict(ent))
    return ok_(dict(ent))


@app.route(route="interessent-delete", methods=["POST", "OPTIONS"])
def interessent_delete(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    iid = body.get("id", "")
    if not iid:
        return err_("id erforderlich", 400)
    try:
        table_("interessenten").delete_entity("interessent", iid)
        return ok_({"deleted": True})
    except Exception:
        return err_("Interessent nicht gefunden", 404)



# =========================================================================
# MANDATSVERTRAG — PDF-Generierung + Signatur (PyMuPDF/fitz, lazy imports)
# =========================================================================

SIGNATURE_CODE_EXPIRY_MIN = 30
SIGNATURE_LINK_EXPIRY_DAYS = 30
ACS_CONN = os.environ.get("ACS_CONNECTION_STRING", "")
ACS_SENDER = os.environ.get("ACS_SENDER_ADDRESS", "info@itukv.de")
FRONTEND_BASE = os.environ.get("FRONTEND_BASE_URL", "https://dashboard.itukv.de")


def _blob_container_lazy(name):
    """Container holen – fitz/blob werden erst hier importiert."""
    from azure.storage.blob import BlobServiceClient
    svc = BlobServiceClient.from_connection_string(TABLE_CONN)
    try:
        svc.create_container(name)
    except Exception:
        pass
    return svc.get_container_client(name)


def _hash_code_sig(code, salt):
    return hashlib.sha256((str(code) + "::" + str(salt)).encode("utf-8")).hexdigest()


def _lookup_signature_by_token(token):
    if not token:
        return None
    tc = table_("vertragsignaturen")
    items = list(tc.query_entities(f"token eq '{token}'"))
    return dict(items[0]) if items else None


_VERTRAG_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Mandatsvertrag</title>
<style>
  @page {
    size: A4;
    margin: 32mm 18mm 28mm 18mm;
    @bottom-right { content: "Seite " counter(page) " / " counter(pages); font-size: 9pt; color: #888; }
  }
  html, body {
    font-family: "Helvetica", "Arial", system-ui, sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1f2937;
  }
  h1 { font-size: 22pt; font-weight: 700; color: #0e7c92; margin: 0 0 4pt 0; letter-spacing: -0.5pt; }
  h1 + .subtitle { color: #6b7280; font-size: 11pt; margin: 0 0 22pt 0; }
  h2 { font-size: 14pt; font-weight: 700; color: #0e7c92; margin: 26pt 0 8pt 0; padding-bottom: 4pt; border-bottom: 1pt solid #e5e7eb; }
  h3 { font-size: 11pt; font-weight: 700; margin: 12pt 0 4pt 0; color: #1f2937; }
  p { margin: 0 0 8pt 0; text-align: justify; }
  ul { margin: 4pt 0 12pt 0; padding-left: 14pt; }
  ul li { margin-bottom: 4pt; }
  .meta-grid { display: flex; gap: 20pt; margin-bottom: 18pt; }
  .meta-box { flex: 1; padding: 10pt 12pt; background: #f9fafb; border-left: 3pt solid #0e7c92; border-radius: 2pt; }
  .meta-box .label { font-size: 8.5pt; text-transform: uppercase; letter-spacing: 1pt; color: #6b7280; margin-bottom: 4pt; }
  .meta-box .company { font-weight: 700; font-size: 11.5pt; }
  .meta-box .small { color: #6b7280; font-size: 10pt; }
  .role-suffix { color: #6b7280; font-style: italic; font-size: 9.5pt; }
  .fee-block { background: #f9fafb; border-radius: 4pt; padding: 10pt 12pt; margin-bottom: 10pt; }
  .signature-section { page-break-inside: avoid; margin-top: 60pt; }
  .signature-row { display: flex; justify-content: space-between; gap: 30pt; margin-top: 50pt; }
  .signature-block { flex: 1; }
  .signature-line { border-top: 1pt solid #6b7280; height: 1pt; margin-bottom: 6pt; }
  .signature-label { font-size: 9pt; color: #6b7280; }
  .footer-note { font-size: 8.5pt; color: #9ca3af; margin-top: 60pt; padding-top: 8pt; border-top: 1pt solid #e5e7eb; text-align: center; }
  .ort-datum { margin: 18pt 0 6pt 0; font-size: 10.5pt; }
</style>
</head>
<body>

<h1>Beratungs- und Dienstleistungsvertrag</h1>
<p class="subtitle">Mandatsvertrag zwischen mibeca GmbH und dem Auftraggeber</p>

<div class="meta-grid">
  <div class="meta-box">
    <div class="label">Berater</div>
    <div class="company">mibeca GmbH</div>
    <div class="small">Schillerstraße 1 · 29525 Uelzen</div>
    <div class="small">vertreten durch {{ form.berater or "Jennifer Kaplan" }}</div>
  </div>
  <div class="meta-box">
    <div class="label">Auftraggeber</div>
    <div class="company">{{ form.auftraggeberFirma }}</div>
    <div class="small">{{ form.auftraggeberStrasse }} · {{ form.auftraggeberPlzOrt }}</div>
    <div class="small">vertreten durch {{ form.auftraggeberGf }}</div>
  </div>
</div>

<h2>§1 Vertragsgegenstand</h2>
<p>Der Auftraggeber erteilt hiermit dem Berater den Auftrag, ihn bei folgenden Entscheidungen / Vorhaben zu beraten und zu unterstützen: (Teil-)Veräußerung des Unternehmens <strong>{{ form.verkaufsobjekt }}</strong> (im Folgenden „Verkaufsobjekt" genannt).</p>

<h2>§2 Leistungen des Beraters</h2>
<ul>
  <li>Aufbereitung der Daten für das Verkaufsobjekt</li>
  <li>Erstellung eines anonymen Kurzexposés für das Verkaufsobjekt</li>
  <li>Suche von Interessenten für das Verkaufsobjekt</li>
  <li>Unterstützung bei Gesprächen mit Interessenten</li>
  <li>Begleitung der Verkaufsverhandlungen</li>
  <li>Vermittlung weiterer Berater (Rechtsanwälte, Steuerberater)</li>
  <li>Laufende Beratung und Projektbegleitung (persönlich, telefonisch, per Videokonferenz, per E-Mail)</li>
</ul>

<h2>§3 Pflichten des Auftraggebers</h2>
<p>Der Auftraggeber stellt alle relevanten Unterlagen (Bilanzen, BWA, Statistiken, Kunden-, Lieferanten- und Mitarbeiterlisten) bereit und sichert deren Vollständigkeit und Richtigkeit zu. Der Berater haftet nicht für die inhaltliche Richtigkeit der gelieferten Informationen.</p>

<h2>§4 Pflichten des Beraters / Vertraulichkeit</h2>
<p>Der Berater ist zum Stillschweigen gegenüber Dritten über sämtliche Inhalte des Verkaufsprozesses sowie über vertrauliche Informationen des Auftraggebers verpflichtet. Diese Verpflichtung gilt auch nach Ende des Vertrages. Unterlagen werden vertraulich aufbewahrt und nach Aufforderung an den Auftraggeber zurückgegeben oder vernichtet.</p>

<h2>§5 Vergütung</h2>
<p>Alle Vergütungen verstehen sich netto zzgl. 19 % Mehrwertsteuer.</p>

<div class="fee-block">
  <h3>(1) Eröffnungsvergütung</h3>
  {% if variante == 'mit_uve' %}
    {% if form.eroeffnungsModus == 'einmalig' %}
    <p>Einmalige Eröffnungsvergütung in Höhe von <strong>{{ "{:,.0f}".format(form.eroeffnungsBetrag or 10000).replace(",", ".") }} €</strong> netto für das UVE-Coachingprogramm, Datenaufbereitung und Kurzexposé.</p>
    {% else %}
    <p>Eröffnungsvergütung: <strong>6 Monatsraten zu je 1.800 €</strong> netto für das UVE-Coachingprogramm, Datenaufbereitung und Kurzexposé.</p>
    {% endif %}
  {% elif variante == 'vorhandenes_uve' %}
    <p>Keine Eröffnungsvergütung – der Auftraggeber hat das UVE-Coaching bereits abgeschlossen und bezahlt (ansonsten 3.490 €). Der Berater übernimmt die Datenaufbereitung sowie die Erstellung des Kurzexposés.</p>
  {% else %}
    <p>Eröffnungsvergütung: <strong>{{ "{:,.0f}".format(form.eroeffnungsBetrag or 4950).replace(",", ".") }} €</strong> netto für Datenaufbereitung und Erstellung des anonymen Kurzexposés.</p>
  {% endif %}
</div>

<div class="fee-block">
  <h3>(2) Beratungsvergütung</h3>
  <p>Jennifer Kaplan: <strong>{{ "{:,.0f}".format(form.honorarJennyStunde or 250).replace(",", ".") }} € pro Stunde</strong> bzw. <strong>{{ "{:,.0f}".format(form.honorarJennyTag or 2990).replace(",", ".") }} € pro Tag</strong> vor Ort (zzgl. Reisespesen).</p>
  <p>Mike Bergmann: <strong>{{ "{:,.0f}".format(form.honorarMikeStunde or 250).replace(",", ".") }} € pro Stunde</strong> bzw. <strong>{{ "{:,.0f}".format(form.honorarMikeTag or 2990).replace(",", ".") }} € pro Tag</strong> vor Ort (zzgl. Reisespesen).</p>
  <p>Team-Mitarbeiter: <strong>{{ "{:,.0f}".format(form.honorarTeamStunde or 150).replace(",", ".") }} € pro Stunde</strong> bzw. <strong>{{ "{:,.0f}".format(form.honorarTeamTag or 1500).replace(",", ".") }} € pro Tag</strong> vor Ort (zzgl. Reisespesen).</p>
</div>

<div class="fee-block">
  <h3>(3) Erfolgsvergütung</h3>
  <p>Erfolgsvergütung in Höhe von <strong>{{ form.erfolgsProzent or 5 }} %</strong> des Transaktionsvolumens bei erfolgreichem Vertragsabschluss zwischen Auftraggeber und einem Interessenten. Als Vertragsabschluss gilt jede Form eines Verkaufs-, Kaufs-, Beteiligungs- oder Fusionsvertrages sowie vergleichbare Aktivitäten (z.B. Asset Deals).</p>
</div>

<h2>§6 Vertragsdauer und Vertragsende</h2>
<p>Der Vertrag beginnt mit Vertragsunterzeichnung und wird zunächst für <strong>{{ form.laufzeitMonate or 12 }} Monate</strong> abgeschlossen. Die Laufzeit verlängert sich stillschweigend um jeweils 6 Monate, sofern er nicht mit einer Frist von 2 Monaten vor Ablauf schriftlich gekündigt wird. Die Vertragslaufzeit endet automatisch zum Monatsende, sobald der Auftraggeber das Verkaufsobjekt veräußert hat.</p>

<h2>§7 Haftungsfreistellung</h2>
<p>Der Berater agiert mit der Sorgfalt eines ordentlichen Kaufmannes. Für Schäden aus der Beratung sowie für entgangene Gewinne haftet der Berater nicht. Der Auftraggeber stellt den Berater von jeglicher Haftung frei, die auf Unvollständigkeit oder Unrichtigkeit der gelieferten Informationen beruht.</p>

<h2>§8 Schlussbestimmungen</h2>
<p>Änderungen bedürfen der Schriftform. Mündliche Nebenabreden bestehen nicht. Sind einzelne Bestimmungen unwirksam, bleibt die Gültigkeit der übrigen unberührt. Es gilt deutsches Recht. Gerichtsstand ist Uelzen.</p>

{% if form.notizen %}
<h2>§9 Zusatzklauseln / Notizen</h2>
<p>{{ form.notizen }}</p>
{% endif %}

<div class="signature-section">
  <p class="ort-datum">Uelzen, den {{ form.datum }}</p>

  <div class="signature-row">
    <div class="signature-block">
      <div class="signature-line"></div>
      <div class="signature-label">Unterschrift (mibeca)</div>
    </div>
    <div class="signature-block">
      <div class="signature-line"></div>
      <div class="signature-label">Unterschrift (Auftraggeber)</div>
    </div>
  </div>

  <div class="footer-note">
    Dieser Vertrag wurde elektronisch zwischen mibeca GmbH und {{ form.auftraggeberFirma }} geschlossen.
  </div>
</div>

</body>
</html>"""


def _render_vertrag_pdf_bytes(form, variante):
    """Erzeugt das PDF aus dem Jinja2/HTML-Template mit WeasyPrint.
    Vorteile: echte CSS-Typografie, page-break-inside fuer Signaturen,
    professioneller Look wie DocuSign/PandaDoc."""
    from jinja2 import Template
    from weasyprint import HTML
    html = Template(_VERTRAG_HTML_TEMPLATE).render(form=form, variante=variante)
    return HTML(string=html, base_url="/").write_pdf()


# Fallback: einfacher PyMuPDF-Renderer falls WeasyPrint fehlt
def _render_vertrag_pdf_bytes_fallback(form, variante):
    """Erstellt das PDF mit PyMuPDF (Fallback)."""
    import fitz

    # Helvetica unterstuetzt keine geschweiften Anfuehrungszeichen oder em-dashes,
    # darum normalisieren wir den Text auf safe Zeichen.
    def _safe(s):
        if not s: return ""
        return (str(s)
            .replace("„", '"').replace("“", '"').replace("”", '"')
            .replace("‚", "'").replace("‘", "'").replace("’", "'")
            .replace("–", "-").replace("—", "-")
            .replace("…", "..."))

    doc = fitz.open()
    page = [doc.new_page(width=595, height=842)]  # A4
    margin_x = 56
    page_w = 595
    text_w = page_w - 2 * margin_x  # 483
    y = [70]
    PAGE_BOTTOM = 800

    def _new_page():
        page[0] = doc.new_page(width=595, height=842)
        y[0] = 70

    def _measure_lines(text, fontsize, fontname):
        """Zaehlt wirklich umgebrochene Zeilen via TextWriter / measurement."""
        # Approximation: Helvetica-Breite ist etwa 0.55x fontsize fuer Durchschnitts-char
        avg_char_w = fontsize * 0.51
        chars_per_line = max(20, int(text_w / avg_char_w))
        lines = 0
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines += 1
                continue
            words = paragraph.split(" ")
            cur_len = 0
            line_count = 1
            for w in words:
                wl = len(w) + 1
                if cur_len + wl > chars_per_line:
                    line_count += 1
                    cur_len = wl
                else:
                    cur_len += wl
            lines += line_count
        return max(1, lines)

    def add_para(text, fontsize=10, bold=False, color=(0.13, 0.13, 0.13),
                 space_before=0, space_after=8, lh_factor=1.35):
        text = _safe(text)
        fontname = "hebo" if bold else "helv"
        line_h = fontsize * lh_factor

        if space_before:
            y[0] += space_before
        # Platz fuer alle Zeilen reservieren – sonst Seitenumbruch
        n_lines = _measure_lines(text, fontsize, fontname)
        needed = n_lines * line_h
        if y[0] + needed > PAGE_BOTTOM:
            _new_page()
        box = fitz.Rect(margin_x, y[0], page_w - margin_x, y[0] + needed + 20)
        page[0].insert_textbox(box, text, fontsize=fontsize, fontname=fontname,
                               color=color, align=0)
        y[0] += needed + space_after

    def add_heading(text):
        add_para(text, fontsize=12, bold=True, color=(0.04, 0.49, 0.57),
                 space_before=10, space_after=6, lh_factor=1.25)

    def add_subheading(text):
        add_para(text, fontsize=10.5, bold=True, color=(0.13, 0.13, 0.13),
                 space_before=4, space_after=4)

    def add_spacer(h=6):
        y[0] += h

    # ============ TITEL ============
    add_para("Beratungs- und Dienstleistungsvertrag",
             fontsize=18, bold=True, color=(0.04, 0.49, 0.57),
             space_after=4, lh_factor=1.2)
    add_para("zwischen mibeca GmbH und dem Auftraggeber",
             fontsize=10, color=(0.45, 0.45, 0.45), space_after=20)

    # ============ PARTEIEN ============
    add_subheading("Berater")
    add_para("mibeca GmbH, Schillerstrasse 1, 29525 Uelzen", space_after=2)
    add_para(f"vertreten durch {form.get('berater','Jennifer Kaplan')}", space_after=2)
    add_para('nachfolgend "Berater" genannt', color=(0.5, 0.5, 0.5), space_after=12)

    add_subheading("Auftraggeber")
    add_para(f"{form.get('auftraggeberFirma','')}", bold=True, space_after=2)
    add_para(f"{form.get('auftraggeberStrasse','')}, {form.get('auftraggeberPlzOrt','')}", space_after=2)
    add_para(f"vertreten durch {form.get('auftraggeberGf','')}", space_after=2)
    add_para('nachfolgend "Auftraggeber" genannt', color=(0.5, 0.5, 0.5), space_after=16)

    # ============ §§ ============
    add_heading("§1 Vertragsgegenstand")
    add_para(f'Der Auftraggeber erteilt hiermit dem Berater den Auftrag, ihn bei folgenden Entscheidungen/Vorhaben zu beraten und zu unterstuetzen: (Teil-)Veraeusserung des Unternehmens {form.get("verkaufsobjekt","")} (im Folgenden "Verkaufsobjekt" genannt).')

    add_heading("§2 Leistungen des Beraters")
    leistungen = [
        "Aufbereitung der Daten fuer das Verkaufsobjekt",
        "Erstellung eines anonymen Kurzexposes",
        "Suche von Interessenten fuer das Verkaufsobjekt",
        "Unterstuetzung bei Gespraechen mit Interessenten",
        "Begleitung der Verkaufsverhandlungen",
        "Vermittlung weiterer Berater (Rechtsanwaelte, Steuerberater)",
        "Laufende Beratung und Projektbegleitung (persoenlich, telefonisch, per Videokonferenz, per E-Mail)",
    ]
    for l in leistungen:
        add_para(f"  -  {l}", space_after=2)
    add_spacer(6)

    add_heading("§3 Pflichten des Auftraggebers")
    add_para("Der Auftraggeber stellt alle relevanten Unterlagen (Bilanzen, BWA, Statistiken, Kunden-, Lieferanten-, Mitarbeiterlisten) bereit und sichert deren Vollstaendigkeit und Richtigkeit zu. Der Berater haftet nicht fuer die inhaltliche Richtigkeit der gelieferten Informationen.")

    add_heading("§4 Pflichten des Beraters / Vertraulichkeit")
    add_para("Der Berater ist zum Stillschweigen gegenueber Dritten ueber saemtliche Inhalte des Verkaufsprozesses sowie ueber vertrauliche Informationen des Auftraggebers verpflichtet. Diese Verpflichtung gilt auch nach Ende des Vertrages. Unterlagen werden vertraulich aufbewahrt und nach Aufforderung zurueckgegeben oder vernichtet.")

    # ============ §5 Verguetung ============
    add_heading("§5 Verguetung")
    add_para("Alle Verguetungen verstehen sich netto zzgl. 19 % Mehrwertsteuer.", space_after=8)

    add_subheading("(1) Eroeffnungsverguetung")
    if variante == 'mit_uve':
        modus = form.get('eroeffnungsModus', 'einmalig')
        if modus == 'einmalig':
            txt = f"Einmalige Eroeffnungsverguetung in Hoehe von {form.get('eroeffnungsBetrag', 10000):,.0f} EUR netto fuer das UVE-Coachingprogramm, Datenaufbereitung und Kurzexpose."
        else:
            txt = "Eroeffnungsverguetung: 6 Monatsraten zu je 1.800 EUR netto fuer das UVE-Coachingprogramm, Datenaufbereitung und Kurzexpose."
    elif variante == 'vorhandenes_uve':
        txt = "Keine Eroeffnungsverguetung - der Auftraggeber hat das UVE-Coaching bereits abgeschlossen und bezahlt (ansonsten 3.490 EUR). Der Berater uebernimmt die Datenaufbereitung sowie die Erstellung des Kurzexposes."
    else:
        txt = f"Eroeffnungsverguetung: {form.get('eroeffnungsBetrag', 4950):,.0f} EUR netto fuer Datenaufbereitung und Erstellung des anonymen Kurzexposes."
    add_para(txt.replace(',', '.'), space_after=10)

    add_subheading("(2) Beratungsverguetung")
    add_para(f"Jennifer Kaplan: {form.get('honorarJennyStunde', 250):,.0f} EUR pro Stunde bzw. {form.get('honorarJennyTag', 2990):,.0f} EUR pro Tag vor Ort (zzgl. Reisespesen).".replace(',', '.'), space_after=4)
    add_para(f"Mike Bergmann: {form.get('honorarMikeStunde', 250):,.0f} EUR pro Stunde bzw. {form.get('honorarMikeTag', 2990):,.0f} EUR pro Tag vor Ort (zzgl. Reisespesen).".replace(',', '.'), space_after=4)
    add_para(f"Team-Mitarbeiter: {form.get('honorarTeamStunde', 150):,.0f} EUR pro Stunde bzw. {form.get('honorarTeamTag', 1500):,.0f} EUR pro Tag vor Ort (zzgl. Reisespesen).".replace(',', '.'), space_after=10)

    add_subheading("(3) Erfolgsverguetung")
    add_para(f"Erfolgsverguetung in Hoehe von {form.get('erfolgsProzent', 5)} % des Transaktionsvolumens bei erfolgreichem Vertragsabschluss zwischen Auftraggeber und einem Interessenten. Als Vertragsabschluss gilt jede Form eines Verkaufs-, Kaufs-, Beteiligungs- oder Fusionsvertrages sowie vergleichbare Aktivitaeten (z.B. Asset Deals).", space_after=8)

    add_heading("§6 Vertragsdauer und Vertragsende")
    add_para(f"Der Vertrag beginnt mit Vertragsunterzeichnung und wird zunaechst fuer {form.get('laufzeitMonate', 12)} Monate abgeschlossen. Die Laufzeit verlaengert sich stillschweigend um jeweils 6 Monate, sofern er nicht mit einer Frist von 2 Monaten schriftlich gekuendigt wird. Die Vertragslaufzeit endet automatisch zum Monatsende, sobald der Auftraggeber das Verkaufsobjekt veraeussert hat.")

    add_heading("§7 Haftungsfreistellung")
    add_para("Der Berater agiert mit der Sorgfalt eines ordentlichen Kaufmannes. Fuer Schaeden aus der Beratung sowie fuer entgangene Gewinne haftet der Berater nicht. Der Auftraggeber stellt den Berater von jeglicher Haftung frei, die auf Unvollstaendigkeit oder Unrichtigkeit der gelieferten Informationen beruht.")

    add_heading("§8 Schlussbestimmungen")
    add_para("Aenderungen beduerfen der Schriftform. Muendliche Nebenabreden bestehen nicht. Sind einzelne Bestimmungen unwirksam, bleibt die Gueltigkeit der uebrigen unberuehrt. Es gilt deutsches Recht. Gerichtsstand ist Uelzen.")

    if form.get('notizen'):
        add_heading("§9 Zusatzklauseln / Notizen")
        add_para(form.get('notizen'))

    # ============ SIGNATUR ============
    add_spacer(20)
    add_para(f"Uelzen, den {form.get('datum','')}", fontsize=10, space_after=40)

    # Signatur-Zeilen
    p = page[0]
    line_y = y[0]
    p.draw_line(fitz.Point(margin_x, line_y), fitz.Point(margin_x + 200, line_y),
                color=(0.4, 0.4, 0.4), width=0.5)
    p.draw_line(fitz.Point(page_w - margin_x - 200, line_y),
                fitz.Point(page_w - margin_x, line_y),
                color=(0.4, 0.4, 0.4), width=0.5)
    p.insert_text(fitz.Point(margin_x, line_y + 12),
                  "Ort, Datum, Unterschrift (mibeca)",
                  fontsize=9, color=(0.4, 0.4, 0.4))
    p.insert_text(fitz.Point(page_w - margin_x - 200, line_y + 12),
                  "Ort, Datum, Unterschrift (Auftraggeber)",
                  fontsize=9, color=(0.4, 0.4, 0.4))

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def _embed_signature_in_pdf(unsigned_bytes, sig_img_bytes, signature_name, audit,
                              anchor_keywords=None, audit_trail=True):
    """Bettet Signatur ins PDF an Anker + haengt optional Audit-Trail-Seite an."""
    import fitz
    if anchor_keywords is None:
        anchor_keywords = ["Unterschrift (Auftraggeber)", "Unterschrift", "Datum"]
    doc = fitz.open(stream=unsigned_bytes, filetype="pdf")
    try:
        if doc.page_count > 0 and sig_img_bytes:
            last_page = doc[doc.page_count - 1]
            pw = last_page.rect.width
            ph = last_page.rect.height
            anchor_rect = None
            for needle in anchor_keywords:
                try:
                    hits = last_page.search_for(needle) or []
                except Exception:
                    hits = []
                if hits:
                    anchor_rect = hits[-1]
                    break
            if anchor_rect is not None:
                sig_w = min(150.0, pw * 0.25)
                sig_h = 32.0
                x0 = anchor_rect.x0
                y1 = anchor_rect.y0 - 4
                y0 = y1 - sig_h
            else:
                sig_w = 150.0
                sig_h = 50.0
                x0 = pw - sig_w - 60
                y1 = ph - 80
                y0 = y1 - sig_h
            try:
                last_page.insert_image(fitz.Rect(x0, y0, x0 + sig_w, y1),
                                       stream=sig_img_bytes, keep_proportion=True)
                last_page.insert_text(fitz.Point(x0, y1 + 12),
                                      signature_name, fontsize=8, color=(0.1, 0.1, 0.1))
            except Exception:
                pass

        # Audit-Trail-Seite (kann unterdrueckt werden bei Gegenzeichnung)
        if not audit_trail:
            out = doc.write()
            return out
        audit_page = doc.new_page(width=595, height=842)
        y = 60
        audit_page.insert_text(fitz.Point(50, y),
                               "Audit-Trail – Elektronische Signatur",
                               fontsize=14, color=(0.04, 0.49, 0.57))
        y += 24
        audit_page.insert_text(fitz.Point(50, y),
                               "Einfache elektronische Signatur gemäß eIDAS Art. 25 Abs. 1",
                               fontsize=9, color=(0.4, 0.4, 0.4))
        y += 28
        for label, val in [
            ("Unterzeichner:", signature_name),
            ("E-Mail:", audit.get("email", "")),
            ("Signiert am:", audit.get("signed_at", "")),
            ("IP-Adresse:", audit.get("ip", "")),
            ("User-Agent:", audit.get("ua", "")),
            ("Bestätigungscode-Hash:", audit.get("code_hash", "")),
            ("Token-Hash:", audit.get("token_hash", "")),
        ]:
            audit_page.insert_text(fitz.Point(50, y), label, fontsize=10, color=(0.3, 0.3, 0.3))
            box = fitz.Rect(200, y - 9, 545, y + 30)
            audit_page.insert_textbox(box, str(val or "—"), fontsize=9, color=(0.05, 0.05, 0.05))
            y += 20
        out = doc.write()
        return out
    finally:
        doc.close()


@app.route(route="vertrag-pdf", methods=["POST", "OPTIONS"])
def vertrag_pdf(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    try:
        pdf_bytes = _render_vertrag_pdf_bytes(body.get("form", {}), body.get("variante", "standard"))
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)
    pdf_headers = {k: v for k, v in CORS.items() if k.lower() != "content-type"}
    pdf_headers["Content-Type"] = "application/pdf"
    pdf_headers["Content-Disposition"] = 'attachment; filename="Mandatsvertrag.pdf"'
    return func.HttpResponse(pdf_bytes, status_code=200, headers=pdf_headers)


@app.route(route="vertrag-zur-signatur", methods=["POST", "OPTIONS"])
def vertrag_zur_signatur(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    variante = body.get("variante", "standard")
    form = body.get("form", {})
    if not target_id:
        return err_("targetId erforderlich", 400)

    target_users = list(table_("users").query_entities(f"targetId eq '{target_id}'"))
    if not target_users:
        return err_("Kein Target-Login angelegt. Bitte zuerst Benutzer fuer dieses Target erstellen.", 400)
    target_email = target_users[0].get("email", "")
    target_name = target_users[0].get("name", "")
    if not target_email:
        return err_("Target hat keine E-Mail-Adresse", 400)

    try:
        pdf_bytes = _render_vertrag_pdf_bytes(form, variante)
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)

    pdf_blob_name = f"mandat-{target_id}-{int(datetime.utcnow().timestamp())}.pdf"
    try:
        container = _blob_container_lazy("vertraege")
        container.upload_blob(pdf_blob_name, pdf_bytes, overwrite=True)
    except Exception as ex:
        return err_(f"Blob-Upload fehlgeschlagen: {ex}", 500)

    # Bestehende noch nicht final unterzeichnete Signaturen invalidieren
    tc = table_("vertragsignaturen")
    revision = 1
    try:
        old_sigs = list(tc.query_entities(f"targetId eq '{target_id}'"))
        for old in old_sigs:
            if old.get("status") in ("pending", "awaiting_countersign"):
                old["status"] = "superseded"
                old["superseded_at"] = datetime.utcnow().isoformat()
                tc.update_entity(dict(old))
        revision = len([o for o in old_sigs if o.get("status") not in ("pending",)]) + 1
    except Exception:
        pass

    sig_id = str(uuid.uuid4())
    token = secrets.token_urlsafe(32)
    code_salt = secrets.token_hex(16)
    expires = (datetime.utcnow() + timedelta(days=SIGNATURE_LINK_EXPIRY_DAYS)).isoformat()
    tc.create_entity({
        "PartitionKey": "signatur", "RowKey": sig_id,
        "targetId": target_id, "token": token, "code_salt": code_salt,
        "status": "pending", "lead_email": target_email, "lead_name": target_name,
        "variante": variante, "pdf_blob": pdf_blob_name,
        "form_json": json.dumps(form, ensure_ascii=False),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires,
        "revision": revision,
    })

    # Verlauf-Eintrag anhaengen
    try:
        targets = table_("targets")
        t = targets.get_entity("target", target_id)
        verlauf = []
        try: verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
        except Exception: verlauf = []
        verlauf.insert(0, {
            "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
            "typ": "mail_out",
            "datum": datetime.utcnow().isoformat(),
            "autor": p.get("name", "") or p.get("email", ""),
            "betreff": f"Mandatsvertrag verschickt (Variante: {variante})" + (f" – Revision {revision}" if revision > 1 else ""),
            "beschreibung": f"E-Mail mit Signatur-Link an {target_email} versendet.",
            "beteiligte": target_email,
        })
        t["kommunikationJson"] = json.dumps(verlauf, ensure_ascii=False)
        targets.update_entity(dict(t))
    except Exception:
        pass

    sign_url = f"{FRONTEND_BASE}/sign/{token}"
    if ACS_CONN:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                <h2 style="color:#097e92">Dein Mandatsvertrag liegt zur Unterschrift bereit</h2>
                <p>Hallo {target_name or ''},</p>
                <p>der Mandatsvertrag fuer dein Verkaufsprojekt ist fertig vorbereitet.
                Du kannst ihn online ansehen und mit wenigen Klicks unterschreiben.</p>
                <p style="margin:24px 0"><a href="{sign_url}" style="background:#097e92;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Vertrag ansehen &amp; unterschreiben</a></p>
                <p style="font-size:12px;color:#666">Der Link ist {SIGNATURE_LINK_EXPIRY_DAYS} Tage gueltig.</p>
                <p>Viele Gruesse<br/>Dein mibeca-Team</p>
                </body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": target_email}]},
                "content": {"subject": "Dein Mandatsvertrag zur Unterschrift", "plainText": f"Vertrag unterschreiben: {sign_url}", "html": html},
            })
        except Exception:
            pass

    return ok_({"signId": sig_id, "token": token, "signUrl": sign_url})


@app.route(route="sign-info", methods=["GET", "OPTIONS"])
def sign_info(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    token = req.params.get("token", "").strip()
    sig = _lookup_signature_by_token(token)
    if not sig:
        return err_("Ungueltiger oder abgelaufener Link.", 404)
    now = datetime.utcnow()
    try:
        expires = datetime.fromisoformat(sig.get("expires_at", ""))
    except Exception:
        expires = now
    expired = sig.get("status") == "pending" and now > expires
    return ok_({
        "status": "expired" if expired else sig.get("status", "pending"),
        "lead_email": sig.get("lead_email", ""),
        "lead_name": sig.get("lead_name", ""),
        "variante": sig.get("variante", ""),
        "expires_at": sig.get("expires_at", ""),
        "signed_at": sig.get("signed_at", ""),
        "signed_at_admin": sig.get("signed_at_admin", ""),
        "signed_by_admin_name": sig.get("signed_by_admin_name", ""),
    })


@app.route(route="sign-pdf", methods=["GET", "OPTIONS"])
def sign_pdf_public(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    token = req.params.get("token", "").strip()
    sig = _lookup_signature_by_token(token)
    if not sig:
        return err_("Ungueltiger Link.", 404)
    # Prio: final (beide unterzeichnet) > target-signed > unsigniert
    blob_name = sig.get("final_pdf_blob") or sig.get("signed_pdf_blob") or sig.get("pdf_blob")
    if not blob_name:
        return err_("PDF nicht verfuegbar", 404)
    try:
        data = _blob_container_lazy("vertraege").download_blob(blob_name).readall()
    except Exception as ex:
        return err_(f"PDF nicht abrufbar: {ex}", 500)
    # WICHTIG: kein 'Content-Type' aus CORS mitschicken, sonst ueberschreibt das mimetype
    pdf_headers = {k: v for k, v in CORS.items() if k.lower() != "content-type"}
    pdf_headers["Content-Type"] = "application/pdf"
    pdf_headers["Content-Disposition"] = 'inline; filename="vertrag.pdf"'
    return func.HttpResponse(data, status_code=200, headers=pdf_headers)


@app.route(route="sign-send-code", methods=["POST", "OPTIONS"])
def sign_send_code(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    token = (body.get("token") or "").strip()
    sig = _lookup_signature_by_token(token)
    if not sig:
        return err_("Ungueltiger Link", 404)
    if sig.get("status") != "pending":
        return err_("Vertrag bereits abgeschlossen", 400)
    code = f"{secrets.randbelow(1000000):06d}"
    code_hash = _hash_code_sig(code, sig.get("code_salt", ""))
    now = datetime.utcnow()
    tc = table_("vertragsignaturen")
    ent = tc.get_entity("signatur", sig["RowKey"])
    ent["code_hash"] = code_hash
    ent["code_sent_at"] = now.isoformat()
    tc.update_entity(dict(ent))
    if not ACS_CONN:
        return err_("E-Mail-Service nicht konfiguriert", 500)
    try:
        from azure.communication.email import EmailClient
        client = EmailClient.from_connection_string(ACS_CONN)
        html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a">
            <p>Dein Bestaetigungscode fuer die Unterschrift lautet:</p>
            <p style="font-size:28px;font-weight:700;letter-spacing:6px;background:#f0fdfa;padding:14px 22px;border-radius:10px;display:inline-block;color:#097e92">{code}</p>
            <p>Der Code ist {SIGNATURE_CODE_EXPIRY_MIN} Minuten gueltig.</p>
            </body></html>"""
        client.begin_send({
            "senderAddress": ACS_SENDER,
            "recipients": {"to": [{"address": sig["lead_email"]}]},
            "content": {"subject": "Bestaetigungscode Mandatsvertrag", "plainText": f"Code: {code}", "html": html},
        })
    except Exception as ex:
        return err_(f"Mailversand fehlgeschlagen: {ex}", 500)
    return ok_({"ok": True})


@app.route(route="sign-submit", methods=["POST", "OPTIONS"])
def sign_submit(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    token = (body.get("token") or "").strip()
    code = (body.get("code") or "").strip()
    sig_name = (body.get("signature_name") or "").strip()
    sig_image = (body.get("signature_image") or "").strip()
    accept_agb = bool(body.get("accept_agb"))
    if not (token and code and sig_name and sig_image and accept_agb):
        return err_("Bitte alle Felder ausfuellen.", 400)
    sig = _lookup_signature_by_token(token)
    if not sig:
        return err_("Ungueltiger Link", 404)
    if sig.get("status") != "pending":
        return err_("Vertrag bereits abgeschlossen", 400)
    expected = sig.get("code_hash", "")
    if not expected:
        return err_("Bitte zuerst Code anfordern", 400)
    try:
        code_sent_at = datetime.fromisoformat(sig.get("code_sent_at", ""))
    except Exception:
        return err_("Code abgelaufen", 400)
    if (datetime.utcnow() - code_sent_at).total_seconds() > SIGNATURE_CODE_EXPIRY_MIN * 60:
        return err_("Code abgelaufen", 400)
    if _hash_code_sig(code, sig.get("code_salt", "")) != expected:
        return err_("Code stimmt nicht", 400)

    try:
        original = _blob_container_lazy("vertraege").download_blob(sig["pdf_blob"]).readall()
    except Exception as ex:
        return err_(f"PDF nicht abrufbar: {ex}", 500)

    sig_bytes = b""
    if sig_image.startswith("data:"):
        try:
            sig_bytes = base64.b64decode(sig_image.split(",", 1)[1])
        except Exception:
            sig_bytes = b""

    ip = (req.headers.get("X-Forwarded-For", "") or "").split(",")[0].strip() or req.headers.get("X-Client-IP", "")
    ua = req.headers.get("User-Agent", "")[:200]
    signed_at = datetime.utcnow().isoformat()
    audit = {
        "email": sig.get("lead_email", ""),
        "signed_at": signed_at,
        "ip": ip, "ua": ua,
        "code_hash": expected[:16] + "…",
        "token_hash": hashlib.sha256(token.encode()).hexdigest()[:16] + "…",
    }
    try:
        signed_bytes = _embed_signature_in_pdf(original, sig_bytes, sig_name, audit)
    except Exception as ex:
        return err_(f"Signatur-Einbettung fehlgeschlagen: {ex}", 500)

    signed_blob_name = f"signed-{sig['RowKey']}.pdf"
    try:
        _blob_container_lazy("vertraege").upload_blob(signed_blob_name, signed_bytes, overwrite=True)
    except Exception as ex:
        return err_(f"Signiertes PDF konnte nicht gespeichert werden: {ex}", 500)

    tc = table_("vertragsignaturen")
    ent = tc.get_entity("signatur", sig["RowKey"])
    ent["status"] = "awaiting_countersign"
    ent["signed_at"] = signed_at
    ent["signed_by_name"] = sig_name
    ent["signed_ip"] = ip
    ent["signed_user_agent"] = ua
    ent["signed_pdf_blob"] = signed_blob_name
    tc.update_entity(dict(ent))

    # Target-Akte aktualisieren
    try:
        targets = table_("targets")
        t = targets.get_entity("target", sig["targetId"])
        v = json.loads(t.get("vertragJson", "{}") or "{}")
        v["signiertAm"] = signed_at
        v["signiertVon"] = sig_name
        v["signedPdfBlob"] = signed_blob_name
        v["status"] = "awaiting_countersign"
        v["signId"] = sig["RowKey"]
        v["signToken"] = sig.get("token", "")
        t["vertragJson"] = json.dumps(v, ensure_ascii=False)
        targets.update_entity(dict(t))
    except Exception:
        pass

    # Verlauf: Target hat unterschrieben
    try:
        targets = table_("targets")
        t = targets.get_entity("target", sig["targetId"])
        verlauf = []
        try: verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
        except Exception: verlauf = []
        verlauf.insert(0, {
            "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
            "typ": "wichtig",
            "datum": signed_at,
            "autor": sig_name,
            "betreff": "Mandatsvertrag vom Verkaeufer unterschrieben",
            "beschreibung": f"{sig_name} hat den Vertrag elektronisch signiert. Wartet auf Gegenzeichnung durch mibeca.",
            "beteiligte": sig.get("lead_email", ""),
        })
        t["kommunikationJson"] = json.dumps(verlauf, ensure_ascii=False)
        targets.update_entity(dict(t))
    except Exception:
        pass

    # Mibeca-Team per Mail informieren dass Gegenzeichnung anliegt
    if ACS_CONN:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            mibeca_mail = os.environ.get("MIBECA_NOTIFY_EMAIL", "jk@mike-bergmann.de")
            html = f"""<html><body style="font-family:Arial,sans-serif">
                <p><strong>Vertrag zur Gegenzeichnung bereit</strong></p>
                <p>{sig_name} ({sig.get('lead_email','')}) hat den Mandatsvertrag unterschrieben.</p>
                <p>Bitte oeffne die Akte im Dashboard und zeichne gegen.</p></body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": mibeca_mail}]},
                "content": {"subject": f"Vertrag {sig.get('lead_name','')} – Gegenzeichnung benoetigt", "plainText": "Vertrag wartet auf Gegenzeichnung im Dashboard.", "html": html},
            })
        except Exception:
            pass

    return ok_({"ok": True, "signed_at": signed_at, "status": "awaiting_countersign"})


@app.route(route="vertrag-countersign", methods=["POST", "OPTIONS"])
def vertrag_countersign(req: func.HttpRequest) -> func.HttpResponse:
    """Admin gegenzeichnet ein vom Target signiertes PDF und finalisiert es."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    sig_id = (body.get("signId") or "").strip()
    sig_image = (body.get("signature_image") or "").strip()
    sig_name = (body.get("signature_name") or p.get("name") or "mibeca").strip()
    if not (sig_id and sig_image):
        return err_("signId und signature_image erforderlich", 400)

    tc = table_("vertragsignaturen")
    try:
        sig = dict(tc.get_entity("signatur", sig_id))
    except Exception:
        return err_("Signatur-Record nicht gefunden", 404)
    if sig.get("status") != "awaiting_countersign":
        return err_(f"Vertrag im falschen Status: {sig.get('status')}", 400)

    # Target-signiertes PDF laden
    try:
        target_signed = _blob_container_lazy("vertraege").download_blob(sig["signed_pdf_blob"]).readall()
    except Exception as ex:
        return err_(f"PDF nicht abrufbar: {ex}", 500)

    sig_bytes = b""
    if sig_image.startswith("data:"):
        try:
            sig_bytes = base64.b64decode(sig_image.split(",", 1)[1])
        except Exception:
            sig_bytes = b""

    signed_at_admin = datetime.utcnow().isoformat()
    audit = {
        "email": p.get("email", ""),
        "signed_at": signed_at_admin,
        "ip": (req.headers.get("X-Forwarded-For", "") or "").split(",")[0].strip(),
        "ua": req.headers.get("User-Agent", "")[:200],
        "code_hash": "—",
        "token_hash": "(admin)",
    }
    try:
        # Mibeca-Sig auf der linken Seite einbetten – kein neuer Audit-Trail
        # (wir aktualisieren stattdessen die bestehende Audit-Seite)
        final_bytes = _embed_signature_in_pdf(
            target_signed, sig_bytes, sig_name, audit,
            anchor_keywords=["Unterschrift (mibeca)", "mibeca"],
            audit_trail=False,
        )
    except Exception as ex:
        return err_(f"Gegenzeichnung fehlgeschlagen: {ex}", 500)

    final_blob_name = f"final-{sig_id}.pdf"
    try:
        _blob_container_lazy("vertraege").upload_blob(final_blob_name, final_bytes, overwrite=True)
    except Exception as ex:
        return err_(f"Finales PDF konnte nicht gespeichert werden: {ex}", 500)

    sig["status"] = "signed"
    sig["signed_at_admin"] = signed_at_admin
    sig["signed_by_admin_name"] = sig_name
    sig["signed_by_admin_email"] = p.get("email", "")
    sig["final_pdf_blob"] = final_blob_name
    tc.update_entity(sig)

    # Target-Akte aktualisieren
    try:
        targets = table_("targets")
        t = targets.get_entity("target", sig["targetId"])
        v = json.loads(t.get("vertragJson", "{}") or "{}")
        v["status"] = "signed"
        v["gegengezeichnetAm"] = signed_at_admin
        v["gegengezeichnetVon"] = sig_name
        v["finalPdfBlob"] = final_blob_name
        t["vertragJson"] = json.dumps(v, ensure_ascii=False)
        targets.update_entity(dict(t))
    except Exception:
        pass

    # Verlauf: mibeca gegengezeichnet
    try:
        targets = table_("targets")
        t = targets.get_entity("target", sig["targetId"])
        verlauf = []
        try: verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
        except Exception: verlauf = []
        verlauf.insert(0, {
            "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
            "typ": "wichtig",
            "datum": signed_at_admin,
            "autor": sig_name,
            "betreff": "Mandatsvertrag durch mibeca gegengezeichnet",
            "beschreibung": f"Vertrag final unterzeichnet. Kunde wurde per Mail mit Download-Link informiert.",
            "beteiligte": sig.get("lead_email", ""),
        })
        t["kommunikationJson"] = json.dumps(verlauf, ensure_ascii=False)
        targets.update_entity(dict(t))
    except Exception:
        pass

    # Target informieren dass finaler Vertrag bereitsteht
    if ACS_CONN:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            download_url = f"{FRONTEND_BASE}/sign/{sig.get('token','')}"
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                <h2 style="color:#097e92">Dein Mandatsvertrag ist vollstaendig unterschrieben</h2>
                <p>Hallo {sig.get('lead_name','')},</p>
                <p>{sig_name} hat den Vertrag fuer mibeca gegengezeichnet. Der Vertrag ist damit final unterzeichnet und liegt fuer dich zum Download bereit.</p>
                <p style="margin:24px 0"><a href="{download_url}" style="background:#097e92;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Mein Exemplar herunterladen</a></p>
                <p>Du findest den Vertrag ausserdem jederzeit in deinem Dashboard unter Vertraege.</p>
                <p>Viele Gruesse<br/>Dein mibeca-Team</p>
                </body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": sig.get("lead_email","")}]},
                "content": {"subject": "Mandatsvertrag final unterschrieben", "plainText": f"Vertrag herunterladen: {download_url}", "html": html},
            })
        except Exception:
            pass

    return ok_({"ok": True, "signed_at_admin": signed_at_admin, "status": "signed", "final_pdf_blob": final_blob_name})


# =========================================================================
# VERLAUF — Direkt-Mail-Versand, Inbound (SendGrid), Ungelesen-Zaehler
# =========================================================================

def _replytokens_table():
    return table_("replytokens")


def _get_user_full(user_id):
    try:
        return dict(table_("users").get_entity("user", user_id))
    except Exception:
        return None


def _verlauf_append(target_id, entry):
    """Haengt einen Verlauf-Eintrag an target.kommunikationJson."""
    try:
        targets = table_("targets")
        t = targets.get_entity("target", target_id)
        verlauf = []
        try: verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
        except Exception: verlauf = []
        verlauf.insert(0, entry)
        t["kommunikationJson"] = json.dumps(verlauf, ensure_ascii=False)
        targets.update_entity(dict(t))
        return True
    except Exception as ex:
        logging.warning(f"verlauf_append fehlgeschlagen: {ex}") if 'logging' in globals() else None
        return False


def _notify_new_entry(target_id, entry, sender_user_id=None):
    """Schickt Push-Mail an die andere Partei wenn ein neuer Verlauf-Eintrag kam."""
    if not ACS_CONN:
        return
    try:
        targets = table_("targets")
        t = dict(targets.get_entity("target", target_id))

        # Empfaenger ermitteln: wenn Sender = Admin -> Target-User, sonst mibeca
        recipients = []
        if sender_user_id:
            sender = _get_user_full(sender_user_id)
            if sender and sender.get("role") == "target":
                # Target hat geschrieben -> mibeca informieren
                recipients = [os.environ.get("MIBECA_NOTIFY_EMAIL", "jk@mike-bergmann.de")]
            else:
                # Admin/mibeca hat geschrieben -> Target informieren
                tu = list(table_("users").query_entities(f"targetId eq '{target_id}'"))
                recipients = [u.get("email", "") for u in tu if u.get("email")]
        else:
            tu = list(table_("users").query_entities(f"targetId eq '{target_id}'"))
            recipients = [u.get("email", "") for u in tu if u.get("email")]

        if not recipients:
            return

        from azure.communication.email import EmailClient
        client = EmailClient.from_connection_string(ACS_CONN)
        betreff = entry.get("betreff", "Neuer Eintrag im ITUKV Dashboard")
        beschr = entry.get("beschreibung", "")
        mb = t.get("mbNr", "")
        link = f"{FRONTEND_BASE}/?targetId={target_id}#verlauf"
        for rcpt in recipients:
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                <h3 style="color:#097e92">Neuer Eintrag im ITUKV Dashboard</h3>
                <p><strong>Projekt:</strong> {mb}</p>
                <p><strong>Betreff:</strong> {betreff}</p>
                <p style="background:#f8f9fa;border-left:3px solid #097e92;padding:12px;white-space:pre-wrap">{beschr}</p>
                <p style="margin-top:24px"><a href="{link}" style="background:#097e92;color:white;padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:600">Im Dashboard oeffnen</a></p>
                </body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": rcpt}]},
                "content": {"subject": f"[ITUKV] {betreff}", "plainText": f"{betreff}\n\n{beschr}\n\nDashboard: {link}", "html": html},
            })
    except Exception as ex:
        logging.warning(f"notify_new_entry fehlgeschlagen: {ex}") if 'logging' in globals() else None


@app.route(route="verlauf-send-mail", methods=["POST", "OPTIONS"])
def verlauf_send_mail(req: func.HttpRequest) -> func.HttpResponse:
    """Verschickt eine Mail an den Target/Kunden + erstellt Verlauf-Eintrag.
    Body: { targetId, betreff, body, empfaengerEmail (optional, sonst aus User) }
    """
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    betreff = (body.get("betreff") or "").strip()
    text_body = (body.get("body") or "").strip()
    if not (target_id and betreff and text_body):
        return err_("targetId, betreff, body erforderlich", 400)

    # Empfaenger
    recipient = body.get("empfaengerEmail", "")
    if not recipient:
        if p.get("role") == "target":
            # Target schreibt -> an mibeca
            recipient = os.environ.get("MIBECA_NOTIFY_EMAIL", "jk@mike-bergmann.de")
        else:
            tu = list(table_("users").query_entities(f"targetId eq '{target_id}'"))
            if not tu or not tu[0].get("email"):
                return err_("Kein Empfaenger gefunden – Target hat keinen User-Account", 400)
            recipient = tu[0].get("email")

    if not ACS_CONN:
        return err_("E-Mail-Service nicht konfiguriert", 500)

    # Reply-Token erzeugen + Index speichern
    token = secrets.token_urlsafe(16)
    try:
        _replytokens_table().create_entity({
            "PartitionKey": "token", "RowKey": token,
            "targetId": target_id,
            "originalSender": p.get("email", ""),
            "createdAt": datetime.utcnow().isoformat(),
        })
    except Exception:
        pass
    reply_domain = os.environ.get("REPLY_DOMAIN", "reply.itukv.de")
    reply_to = f"verlauf+{token}@{reply_domain}"

    try:
        from azure.communication.email import EmailClient
        client = EmailClient.from_connection_string(ACS_CONN)
        sender_name = p.get("name", "") or "mibeca"
        html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
            <p>{text_body.replace(chr(10), '<br/>')}</p>
            <hr/>
            <p style="font-size:11px;color:#888">Diese Nachricht wurde aus dem ITUKV Dashboard verschickt von {sender_name}.
            Sie koennen direkt auf diese E-Mail antworten – Ihre Antwort wird automatisch im Dashboard-Verlauf gespeichert.</p>
            </body></html>"""
        client.begin_send({
            "senderAddress": ACS_SENDER,
            "replyTo": [{"address": reply_to, "displayName": sender_name}],
            "recipients": {"to": [{"address": recipient}]},
            "content": {"subject": betreff, "plainText": text_body, "html": html},
        })
    except Exception as ex:
        return err_(f"Mailversand fehlgeschlagen: {ex}", 500)

    # Verlauf-Eintrag
    entry = {
        "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
        "typ": "mail_out",
        "datum": datetime.utcnow().isoformat(),
        "autor": p.get("name", "") or p.get("email", ""),
        "betreff": betreff,
        "beschreibung": text_body,
        "beteiligte": recipient,
        "createdBy": p.get("id", ""),
    }
    _verlauf_append(target_id, entry)
    return ok_({"ok": True, "entry": entry})


@app.route(route="verlauf-add", methods=["POST", "OPTIONS"])
def verlauf_add(req: func.HttpRequest) -> func.HttpResponse:
    """Direkt-Nachricht in App (ohne Mail-Versand). Body: { targetId, betreff, body, typ? }"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    if not target_id:
        return err_("targetId erforderlich", 400)
    entry = {
        "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
        "typ": body.get("typ", "notiz"),
        "datum": datetime.utcnow().isoformat(),
        "autor": p.get("name", "") or p.get("email", ""),
        "betreff": body.get("betreff", ""),
        "beschreibung": body.get("body", ""),
        "beteiligte": body.get("beteiligte", ""),
        "createdBy": p.get("id", ""),
    }
    _verlauf_append(target_id, entry)
    _notify_new_entry(target_id, entry, sender_user_id=p.get("id"))
    return ok_({"ok": True, "entry": entry})


@app.route(route="verlauf-unread-count", methods=["GET", "OPTIONS"])
def verlauf_unread_count(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert pro Target die Anzahl ungelesener Verlauf-Eintraege fuer den aktuellen User."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    user = _get_user_full(p.get("id"))
    if not user:
        return ok_({"perTarget": {}, "total": 0})
    last_seen = {}
    try:
        last_seen = json.loads(user.get("lastSeenVerlauf", "{}") or "{}")
    except Exception:
        last_seen = {}

    # Welche Targets sieht der User? Target sieht nur sein Target, Admin alle.
    target_ids = []
    if user.get("role") == "target" and user.get("targetId"):
        target_ids = [user["targetId"]]
    else:
        try:
            target_ids = [t.get("RowKey") for t in table_("targets").list_entities()]
        except Exception:
            target_ids = []

    per_target = {}
    total = 0
    for tid in target_ids:
        try:
            t = dict(table_("targets").get_entity("target", tid))
            verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
        except Exception:
            verlauf = []
        ls = last_seen.get(tid, "1970-01-01T00:00:00")
        # Nicht eigene Eintraege zaehlen
        unread = sum(1 for e in verlauf
                     if (e.get("datum", "") or "") > ls
                     and e.get("createdBy", "") != p.get("id", ""))
        if unread:
            per_target[tid] = unread
            total += unread
    return ok_({"perTarget": per_target, "total": total})


@app.route(route="verlauf-mark-read", methods=["POST", "OPTIONS"])
def verlauf_mark_read(req: func.HttpRequest) -> func.HttpResponse:
    """Markiert alle Verlauf-Eintraege fuer den User als gelesen.
    Body: { targetId } – wenn fehlt: alle Targets."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    user = _get_user_full(p.get("id"))
    if not user:
        return err_("User nicht gefunden", 404)
    try:
        last_seen = json.loads(user.get("lastSeenVerlauf", "{}") or "{}")
    except Exception:
        last_seen = {}
    now = datetime.utcnow().isoformat()
    if target_id:
        last_seen[target_id] = now
    else:
        try:
            for t in table_("targets").list_entities():
                last_seen[t.get("RowKey")] = now
        except Exception:
            pass
    user["lastSeenVerlauf"] = json.dumps(last_seen, ensure_ascii=False)
    try:
        table_("users").update_entity(user)
    except Exception as ex:
        return err_(f"Update fehlgeschlagen: {ex}", 500)
    return ok_({"ok": True})


@app.route(route="inbound-mail", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def inbound_mail(req: func.HttpRequest) -> func.HttpResponse:
    """SendGrid Inbound Parse Webhook.
    Body: multipart/form-data mit Feldern wie 'to', 'from', 'subject', 'text', 'html', 'envelope'.
    Wir extrahieren das Reply-Token aus der to-Adresse (verlauf+TOKEN@reply.itukv.de),
    schlagen das Token im Index nach und schreiben den Eintrag in den Verlauf.
    """
    try:
        # SendGrid postet multipart/form-data
        form = req.form if hasattr(req, "form") else {}
        # Fallback: req.params/req.get_body()
        if not form:
            try:
                from urllib.parse import parse_qs
                raw = req.get_body().decode("utf-8", "ignore")
                form = {k: v[0] if v else "" for k, v in parse_qs(raw).items()}
            except Exception:
                form = {}

        to_field = form.get("to", "") or form.get("envelope", "")
        from_field = form.get("from", "")
        subject = form.get("subject", "") or "(ohne Betreff)"
        text_body = form.get("text", "") or form.get("html", "")

        # Token aus to-Adresse rausziehen: verlauf+TOKEN@...
        import re
        m = re.search(r"verlauf\+([A-Za-z0-9_\-]+)@", to_field)
        if not m:
            return func.HttpResponse(json.dumps({"error": "Kein Reply-Token in Adresse"}),
                                     status_code=400, headers=CORS)
        token = m.group(1)
        try:
            rec = _replytokens_table().get_entity("token", token)
            target_id = rec.get("targetId", "")
        except Exception:
            return func.HttpResponse(json.dumps({"error": "Token nicht gefunden"}),
                                     status_code=404, headers=CORS)

        # Eintrag anhaengen
        entry = {
            "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
            "typ": "mail_in",
            "datum": datetime.utcnow().isoformat(),
            "autor": from_field,
            "betreff": subject,
            "beschreibung": text_body[:5000],  # max 5k chars
            "beteiligte": from_field,
        }
        _verlauf_append(target_id, entry)
        _notify_new_entry(target_id, entry, sender_user_id=None)  # benachrichtigt Admins
        return func.HttpResponse(json.dumps({"ok": True}), status_code=200, headers=CORS)
    except Exception as ex:
        logging.error(f"inbound-mail Fehler: {ex}") if 'logging' in globals() else None
        return func.HttpResponse(json.dumps({"error": str(ex)}), status_code=500, headers=CORS)
