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
    projekttyp = body.get("projekttyp", "Projekt Target")
    if "Kauf" in projekttyp or "Investor" in projekttyp:
        phasen_titel = [
            "Suchprofil definieren",
            "Markt-Screening (mibeca)",
            "Long-List Uebergabe",
            "Short-List Kaeufer-Auswahl",
            "Anonyme Ansprache durch mibeca",
            "NDA-Austausch",
            "Erstes Kennenlernen",
            "LOI / Indikatives Angebot",
            "Due Diligence",
            "Vertrag & Closing",
        ]
    else:
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

<h1>{% if variante == 'kauf_mandat' %}Beratungsvertrag · Unternehmens-Zukauf{% else %}Beratungs- und Dienstleistungsvertrag{% endif %}</h1>
<p class="subtitle">{% if variante == 'kauf_mandat' %}Kauf-Mandat zwischen mibeca GmbH und dem Auftraggeber{% else %}Mandatsvertrag zwischen mibeca GmbH und dem Auftraggeber{% endif %}</p>

<div class="meta-grid">
  <div class="meta-box">
    <div class="label">Berater</div>
    <div class="company">mibeca GmbH</div>
    <div class="small">Schillerstraße 1 · 29525 Uelzen</div>
    <div class="small">vertreten durch {{ form.berater or "Jennifer Kaplan" }}</div>
  </div>
  <div class="meta-box">
    <div class="label">Auftraggeber (Käufer)</div>
    <div class="company">{{ form.auftraggeberFirma }}</div>
    <div class="small">{{ form.auftraggeberStrasse }} · {{ form.auftraggeberPlzOrt }}</div>
    <div class="small">vertreten durch {{ form.auftraggeberGf }}</div>
  </div>
</div>

{% if variante == 'kauf_mandat' %}
<h2>§1 Vertragsgegenstand</h2>
<p>Der Auftraggeber erteilt hiermit dem Berater den Auftrag, ihn beim Erwerb eines geeigneten IT-Unternehmens (im Folgenden „Zielunternehmen") zu beraten und zu unterstützen. Suchprofil und Auswahlkriterien werden im Rahmen des Mandats gemeinsam definiert.</p>

<h2>§2 Leistungen des Beraters</h2>
<ul>
  <li>Erstellung und Schärfung des Suchprofils gemeinsam mit dem Auftraggeber</li>
  <li>Markt-Screening und Identifikation passender Zielunternehmen (Long-List)</li>
  <li>Anonyme Ansprache der Verkaufsbereitschaft potenzieller Zielunternehmen</li>
  <li>NDA-Abwicklung mit Zielunternehmen</li>
  <li>Vorbereitung und Begleitung der Erstgespräche</li>
  <li>Unterstützung bei Indikativ-Angebot und LOI</li>
  <li>Begleitung der Due Diligence und Verhandlung</li>
  <li>Vermittlung weiterer Berater (Rechtsanwälte, Steuerberater, M&A-Experten)</li>
</ul>

<h2>§3 Pflichten des Auftraggebers</h2>
<p>Der Auftraggeber stellt Suchkriterien, Budget-Rahmen und Entscheidungsbefugnisse zur Verfügung. Er meldet zeitnah zurück, welche von mibeca vorgeschlagenen Zielunternehmen weiter verfolgt werden sollen. Vertraulichkeit der bereitgestellten Informationen ist beidseitig zu wahren.</p>
{% else %}
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
{% endif %}

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
  {% elif variante == 'kauf_mandat' %}
    <p>Eröffnungsvergütung: <strong>{{ "{:,.0f}".format(form.eroeffnungsBetrag or 4950).replace(",", ".") }} €</strong> netto für die Erstellung des Suchprofils und das initiale Markt-Screening (Long-List). Anschließend folgt eine monatliche Retainer-Pauschale, sofern unter Notizen vereinbart.</p>
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


_NDA_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><title>NDA {{ form.mbNr }}</title>
<style>
  @page {
    size: A4;
    margin: 28mm 20mm 28mm 20mm;
    @top-right { content: "Projekt {{ form.mbNr or '' }}"; font-size: 9pt; color: #666; }
    @bottom-right { content: "Seite " counter(page) " von " counter(pages); font-size: 9pt; color: #888; }
    @bottom-left { content: "mibeca GmbH · Schillerstr. 1 · 29525 Uelzen · Gerichtsstand Uelzen"; font-size: 8pt; color: #888; }
  }
  html, body { font-family: "Helvetica", "Arial", system-ui, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1f2937; }
  h1 { font-size: 16pt; font-weight: 700; color: #0e7c92; margin: 0 0 4pt 0; text-align: center; }
  .subtitle { color: #1f2937; font-size: 11pt; margin: 0 0 22pt 0; text-align: center; }
  .parties { background: #f9fafb; padding: 12pt; border-radius: 4pt; margin-bottom: 16pt; }
  .party-line { margin: 3pt 0; }
  .party-blank { border-bottom: 1pt solid #6b7280; min-width: 250pt; display: inline-block; padding-bottom: 1pt; }
  .role-suffix { color: #6b7280; font-style: italic; font-size: 9.5pt; }
  h2 { font-size: 11pt; font-weight: 700; color: #0e7c92; margin: 14pt 0 5pt 0; }
  p { margin: 0 0 7pt 0; text-align: justify; }
  ol { padding-left: 16pt; margin: 4pt 0; } ol li { margin-bottom: 4pt; text-align: justify; }
  .signature-section { page-break-inside: avoid; margin-top: 30pt; }
  .signature-section p { margin-top: 6pt; }
  .signature-row { display: flex; justify-content: space-between; gap: 30pt; margin-top: 40pt; }
  .signature-block { flex: 1; }
  .signature-line { border-top: 1pt solid #6b7280; height: 1pt; margin-bottom: 4pt; }
  .signature-label { font-size: 9pt; color: #6b7280; }
  .schluss { font-size: 9.5pt; color: #4b5563; margin-top: 10pt; padding-top: 8pt; border-top: 1pt solid #e5e7eb; }
</style></head><body>

<h1>Vertraulichkeitsvereinbarung – NDA</h1>
<p class="subtitle">zum Projekt mit der Referenznummer – <strong>{{ form.mbNr or '(noch nicht zugeordnet)' }}</strong></p>

<div class="parties">
  <div class="party-line"><span class="party-blank">{{ form.firma or "&nbsp;" | safe }}</span></div>
  <div class="party-line"><span class="party-blank">{{ form.adresse or "&nbsp;" | safe }}</span></div>
  <div class="party-line"><span class="party-blank">{{ form.plzOrt or "&nbsp;" | safe }}</span></div>
  <div class="party-line">vertreten durch <span class="party-blank">{{ form.vertreten or "&nbsp;" | safe }}</span></div>
  <div class="role-suffix" style="margin-top:6pt">nachfolgend gemeinsam „Investor" genannt</div>
</div>

<p style="margin-bottom:12pt"><strong>und der Firma</strong></p>

<div class="parties">
  <div class="party-line"><strong>mibeca GmbH</strong></div>
  <div class="party-line">Schillerstr. 1</div>
  <div class="party-line">29525 Uelzen</div>
  <div class="party-line">vertreten durch Jennifer Kaplan</div>
  <div class="role-suffix" style="margin-top:6pt">nachfolgend „Transaktionsberater" genannt</div>
</div>

<h2>Präambel</h2>
<p>Der Transaktionsberater unterstützt IT-Unternehmer und deren IT-Unternehmen (nachfolgend „Verkaufsobjekte" genannt) dabei, das eigene Unternehmen zu verkaufen. Der Investor sucht im Rahmen seiner Strategie geeignete Verkaufsobjekte mit dem Ziel des Kaufs dieser Verkaufsobjekte oder einer Beteiligung an diesen (im Folgenden jeweils eine „Transaktion"). Im Hinblick darauf, dass die Parteien über eine mögliche Zusammenarbeit Gespräche führen und/oder die Parteien in diesem Zusammenhang vertrauliche Informationen und Unterlagen über Verkaufsobjekte austauschen wollen und/oder dem Investor vertrauliche Informationen über Verkaufsobjekte zugänglich gemacht werden und die Parteien einen Missbrauch dieser Informationen vermeiden wollen, vereinbaren die Parteien folgendes:</p>

<h2>§1 Projektbeschreibung</h2>
<p>Der Transaktionsberater beabsichtigt, dem Investor vertrauliche Informationen über ein Verkaufsobjekt mit der oben genannten Referenznummer mitzuteilen. Der Investor bestätigt, bisher noch nicht über ein Verkaufsobjekt in Verhandlungen zu stehen, auf das die bisher erhaltenen Informationen zutrifft (z.B. Region, Anzahl Mitarbeiter etc.).</p>

<h2>§2 Geheimhaltungsvereinbarung</h2>
<p>Der Investor verpflichtet sich hiermit alle Informationen, die er direkt oder indirekt im Rahmen dieser Zusammenarbeit vom Transaktionsberater erlangt, vertraulich zu behandeln und nur im Zusammenhang mit dem in §1 beschriebenen Projekt zu verwenden. Der Investor sichert dem Transaktionsberater insbesondere zu, diese Informationen außer den in §3 Abs. 3 zugelassenen Personenkreis, weder an Dritte weiter zu geben noch in anderer Form Dritten zugänglich zu machen und alle angemessenen Vorkehrungen zu treffen, um einen Zugriff Dritter auf diese Informationen zu vermeiden.</p>

<h2>§3 Geheimhaltungsumfang und betroffener Personenkreis</h2>
<ol>
  <li>Die Geheimhaltungsvereinbarung bezieht sich auf alle Informationen, die der Investor oder einer seiner Angestellten im Zusammenhang mit dem in §1 beschriebenen Projekt erlangt oder erlangen wird, insbesondere auf Know-how sowie Ergebnisse, die im Rahmen dieses Projektes erzielt oder verwendet werden, die Beschreibung des Projektes, die in Aussicht genommenen Zeitpläne, Ziele und Ideen für die Ausführung des Projektes und andere nicht öffentlich verfügbare Informationen, die der Investor im Rahmen des Projektes über den Mandanten vom Transaktionsberater für die Prüfung der Transaktion erlangt. Der Investor wird die überlassenen vertraulichen Informationen nicht zu anderen Zwecken, insbesondere nicht zu Wettbewerbszwecken verwerten und auch nicht an Dritte weitergeben oder öffentlich bekannt machen.</li>
  <li>Die Geheimhaltungsvereinbarung erstreckt sich auch auf sämtliche Mitarbeiter und Beauftragte sowie verbundene Unternehmen des Investors, ohne Rücksicht auf die Art und rechtliche Ausgestaltung der Zusammenarbeit. Der Investor verpflichtet sich, diesem Personenkreis entsprechende Geheimhaltungsverpflichtungen aufzuerlegen, soweit dies noch nicht geschehen ist und diese dem Transaktionsberater auf dessen Verlangen hin nachzuweisen.</li>
  <li>Ausgenommen sind solche Personen, wie Steuerberater, Wirtschaftsprüfer und Rechtsanwälte, die aufgrund des Berufsrechts zur Verschwiegenheit verpflichtet sind.</li>
</ol>

<h2>§4 Zeitraum</h2>
<ol>
  <li>Die Geheimhaltungsverpflichtungen nach diesem Vertrag gelten bis zum <strong>31.12.{{ form.gueltigBis or "2027" }}</strong>.</li>
  <li>Die Geheimhaltungsverpflichtungen nach diesem Vertrag bestehen nicht bzw. nicht mehr, wenn die betreffenden Informationen nachweislich allgemein bekannt sind bzw. geworden sind oder ohne Verschulden des Investors allgemein bekannt werden oder rechtmäßig von einem Dritten erlangt wurden oder bei dem Investor bereits vorhanden sind.</li>
</ol>

<h2>§5 Strafbarkeit und Schadensersatz</h2>
<p>Dem Investor ist bekannt, dass die Verletzung von Betriebs- und Geschäftsgeheimnissen nach den §§ 17, 18 UWG strafbar ist und mit Freiheitsstrafe bis zu 5 Jahren geahndet werden kann, und derjenige, der Geschäfts- und Betriebsgeheimnisse verletzt, zum Ersatz des daraus entstandenen Schadens nach § 19 UWG verpflichtet ist.</p>

<h2>Schlussbestimmungen</h2>
<p class="schluss">Die Vertraulichkeitsvereinbarung beginnt mit beidseitiger Unterzeichnung. Änderungen und/oder Ergänzungen dieser Vereinbarung bedürfen zu ihrer Wirksamkeit der Schriftform, ebenso eine etwaige Aufhebung dieser Schriftformklausel. Sollten sich einzelne Bestimmungen dieser Vereinbarung als unwirksam erweisen, so wird die Wirksamkeit der übrigen Bestimmungen hiervon nicht berührt. An die Stelle der unwirksamen Bestimmung tritt eine Regelung, die dem gewollten Zweck am nächsten kommt. Für das Vertragsverhältnis und die sich hieraus ergebenden Ansprüche gilt ausschließlich deutsches Recht. Erfüllungsort und Gerichtsstand ist Uelzen, der Sitz des Unternehmens des Transaktionsberaters.</p>

<p class="schluss" style="margin-top:6pt">Ich, der oben näher spezifizierte Investor, habe diese Vereinbarung zur Kenntnis genommen und bestätige, dass ich berechtigt bin, diese rechtsverbindlich zu unterzeichnen. Ich stimme zu, dass meine Angaben und Daten zur Beantwortung meiner Anfrage elektronisch erhoben und gespeichert werden.</p>

<div class="signature-section">
  <p>{{ form.ort or "Uelzen" }}, den {{ form.datum }}</p>
  <div class="signature-row">
    <div class="signature-block">
      <div class="signature-line"></div>
      <div class="signature-label">Unterschrift Investor</div>
    </div>
    <div class="signature-block">
      <div class="signature-line"></div>
      <div class="signature-label">Unterschrift Transaktionsberater (Jennifer Kaplan)</div>
    </div>
  </div>
</div>

</body></html>"""


def _render_nda_pdf_bytes(form, variante='investor'):
    from jinja2 import Template
    from weasyprint import HTML
    html = Template(_NDA_HTML_TEMPLATE).render(form=form, variante=variante)
    return HTML(string=html, base_url="/").write_pdf()


@app.route(route="nda-pdf", methods=["POST", "OPTIONS"])
def nda_pdf(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    try:
        pdf_bytes = _render_nda_pdf_bytes(body.get("form", {}), body.get("variante", "investor"))
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)
    return func.HttpResponse(pdf_bytes, status_code=200, mimetype="application/pdf",
                             headers={**CORS, "Content-Disposition": 'attachment; filename="NDA.pdf"'})


@app.route(route="nda-zur-signatur", methods=["POST", "OPTIONS"])
def nda_zur_signatur(req: func.HttpRequest) -> func.HttpResponse:
    """NDA-Sign-Link an Investor/Kaeufer per Mail."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    form = body.get("form", {})
    variante = body.get("variante", "investor")
    empfaenger = (body.get("empfaengerEmail") or "").strip()
    if not (target_id and empfaenger and form.get("firma")):
        return err_("targetId, empfaengerEmail, firma erforderlich", 400)
    try:
        pdf_bytes = _render_nda_pdf_bytes(form, variante)
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)
    pdf_blob_name = f"nda-{target_id}-{int(datetime.utcnow().timestamp())}.pdf"
    try:
        _blob_container_lazy("vertraege").upload_blob(pdf_blob_name, pdf_bytes, overwrite=True)
    except Exception as ex:
        return err_(f"Blob-Upload fehlgeschlagen: {ex}", 500)
    sig_id = str(uuid.uuid4())
    token = secrets.token_urlsafe(32)
    code_salt = secrets.token_hex(16)
    expires = (datetime.utcnow() + timedelta(days=SIGNATURE_LINK_EXPIRY_DAYS)).isoformat()
    tc = table_("vertragsignaturen")
    tc.create_entity({
        "PartitionKey": "signatur", "RowKey": sig_id,
        "targetId": target_id, "token": token, "code_salt": code_salt,
        "status": "pending", "lead_email": empfaenger, "lead_name": form.get("vertreten", ""),
        "variante": "nda_" + variante, "pdf_blob": pdf_blob_name,
        "form_json": json.dumps(form, ensure_ascii=False),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires,
        "dokument_typ": "nda",
    })
    sign_url = f"{FRONTEND_BASE}/sign/{token}"
    if ACS_CONN:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                <h2 style="color:#097e92">NDA zur Unterschrift</h2>
                <p>Hallo {form.get('vertreten','')},</p>
                <p>im Rahmen unserer Zusammenarbeit als M&A-Berater bitten wir Sie um Unterzeichnung der beiliegenden Vertraulichkeitsvereinbarung (NDA).</p>
                <p style="margin:24px 0"><a href="{sign_url}" style="background:#097e92;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">NDA ansehen &amp; unterschreiben</a></p>
                <p style="font-size:12px;color:#666">Der Link ist {SIGNATURE_LINK_EXPIRY_DAYS} Tage gueltig.</p>
                </body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": empfaenger}]},
                "content": {"subject": f"NDA zur Unterzeichnung – {form.get('firma','')}", "plainText": f"NDA: {sign_url}", "html": html},
            })
        except Exception:
            pass
    _verlauf_append(target_id, {
        "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
        "typ": "mail_out",
        "datum": datetime.utcnow().isoformat(),
        "autor": p.get("name", ""),
        "betreff": f"NDA verschickt an {form.get('firma','')}",
        "beschreibung": f"NDA-Sign-Link an {empfaenger} versendet.",
        "beteiligte": empfaenger,
    })
    return ok_({"signId": sig_id, "token": token, "signUrl": sign_url})


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
    items = []  # Liste fuer Dropdown
    for tid in target_ids:
        try:
            t = dict(table_("targets").get_entity("target", tid))
            verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
        except Exception:
            t = {}
            verlauf = []
        ls = last_seen.get(tid, "1970-01-01T00:00:00")
        unread_entries = [e for e in verlauf
                          if (e.get("datum", "") or "") > ls
                          and e.get("createdBy", "") != p.get("id", "")]
        if unread_entries:
            per_target[tid] = len(unread_entries)
            total += len(unread_entries)
            # Neuesten Eintrag pro Target rausziehen
            unread_entries.sort(key=lambda x: x.get("datum", ""), reverse=True)
            top = unread_entries[0]
            items.append({
                "targetId": tid,
                "mbNr": t.get("mbNr", ""),
                "firma": t.get("verkaueferName", "") or t.get("firma", ""),
                "unreadCount": len(unread_entries),
                "lastBetreff": top.get("betreff", ""),
                "lastDatum": top.get("datum", ""),
                "lastTyp": top.get("typ", ""),
            })
    items.sort(key=lambda x: x.get("lastDatum", ""), reverse=True)
    return ok_({"perTarget": per_target, "total": total, "items": items[:15]})


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


# =========================================================================
# PRESSE-PROZESS NACH ERFOLGREICHER TRANSAKTION
# =========================================================================

PRESSE_KONTAKTE_DEFAULT = [
    {"id": "p1", "name": "Dr. Ronald Wiltscheck", "rolle": "Chefredakteur", "medium": "ChannelPartner", "email": "rw@channelpartner.de"},
    {"id": "p1b", "name": "Dr. Ronald Wiltscheck", "rolle": "Chefredakteur (privat)", "medium": "ChannelPartner", "email": "ronald.wiltscheck@outlook.de"},
    {"id": "p2", "name": "Martin Fryba", "rolle": "Journalist", "medium": "CRN", "email": "mfryba@thechannelcompany.com"},
    {"id": "p3", "name": "Michael Hase", "rolle": "Chefreporter", "medium": "IT-BUSINESS / Vogel", "email": "michael.hase@vogel-it.de"},
    {"id": "p4", "name": "Margrit Lingner", "rolle": "Leitende Redakteurin", "medium": "IT-BUSINESS / Vogel", "email": "margrit.lingner@vogel.de"},
    {"id": "p5", "name": "Mihriban Dincel", "rolle": "Redakteurin", "medium": "IT-BUSINESS / Vogel", "email": "mihriban.dincel@vogel.de"},
    {"id": "p6", "name": "Sylvia Loesel", "rolle": "Chefredakteurin", "medium": "IT-BUSINESS / Vogel", "email": "sylvia.loesel@vogel.de"},
    {"id": "p7", "name": "Heidi Schuster", "rolle": "Redaktion", "medium": "IT-BUSINESS / Vogel", "email": "heidi.schuster@vogel.de"},
    {"id": "p8", "name": "Heinz Arnold", "rolle": "Chefredakteur", "medium": "connect professional / WEKA", "email": "harnold@weka-fachmedien.de"},
    {"id": "p9", "name": "WEKA Redaktion", "rolle": "Allgemein", "medium": "WEKA Fachmedien", "email": "jschroeper@weka-fachmedien.de"},
    {"id": "p10", "name": "Sebastian Hirsch", "rolle": "Redaktion", "medium": "IT Media Publishing", "email": "shirsch@it-media.de"},
]


def _generate_press_text(data):
    """Erzeugt einen Pressetext aus den Deal-Daten. Nutzt Azure OpenAI wenn konfiguriert,
    sonst template-basiert."""
    aoai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    aoai_key = os.environ.get("AZURE_OPENAI_KEY", "")
    aoai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    if aoai_endpoint and aoai_key:
        try:
            import urllib.request
            prompt = f"""Agiere wie ein erfahrener Presseredakteur fuer eine IT-Fachzeitschrift.

Erstelle eine Pressemeldung (max. 450 Woerter) zu folgendem Unternehmenskauf, den die mibeca GmbH (Mike Bergmann Akademie) begleitet hat:

- Begleitete Seite: {data.get('seite','Verkaeuferseite')}
- Kaeufer-Firma: {data.get('kaeuferFirma','')}, Sitz: {data.get('kaeuferOrt','')}
- Verkaeufer-Firma: {data.get('verkaeuferFirma','')}, Sitz: {data.get('verkaeuferOrt','')}
- Branche/Schwerpunkt: {data.get('schwerpunkt','IT-Systemhaus')}
- Besonderheiten der Transaktion: {data.get('besonderheiten','')}
- Synergien nach Transaktion: {data.get('synergien','')}

Format:
- Knackige Headline + Sub-Headline
- 3-4 inhaltliche Absaetze
- Drei Zitate: Jennifer Kaplan (mibeca), Mike Bergmann (mibeca), Verkaeufer/Kaeufer (je nach Begleitung)
- Neutrale, professionelle Sprache
- Hebt die Kompetenz von mibeca im M&A-Bereich subtil hervor

Schreibe direkt den fertigen Pressetext, ohne weitere Erklaerung."""
            body = json.dumps({"messages": [{"role":"user","content": prompt}], "max_tokens": 1200, "temperature": 0.7}).encode()
            url = f"{aoai_endpoint.rstrip('/')}/openai/deployments/{aoai_deployment}/chat/completions?api-version=2024-02-15-preview"
            req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json","api-key":aoai_key}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as r:
                rj = json.loads(r.read().decode())
                return rj["choices"][0]["message"]["content"]
        except Exception as ex:
            logging.error(f"AI-Gen Fehler, fallback Template: {ex}")

    # Template-Fallback
    kf = data.get("kaeuferFirma", "[Käufer]")
    vf = data.get("verkaeuferFirma", "[Verkäufer]")
    ko = data.get("kaeuferOrt", "")
    vo = data.get("verkaeuferOrt", "")
    schw = data.get("schwerpunkt", "IT-Systemhaus")
    bes = data.get("besonderheiten", "")
    syn = data.get("synergien", "")
    return f"""IT-Systemhaus-Transaktion: {kf} uebernimmt {vf}

In der IT-Branche wurde eine bedeutsame Transaktion abgeschlossen: Die {kf} aus {ko} hat das {schw} {vf} aus {vo} uebernommen. Die mibeca GmbH (Mike Bergmann Akademie) hat den Prozess als M&A-Berater begleitet.

{bes}

"Diese Transaktion zeigt, wie wichtig eine strukturierte Begleitung im M&A-Prozess fuer IT-Unternehmen ist", erklaert Jennifer Kaplan, Transaktionsberaterin der mibeca GmbH. "Beide Seiten konnten wir ueber den gesamten Prozess hinweg sicher zum Abschluss fuehren."

Strategischer Hintergrund und Synergien: {syn}

"Im IT-Markt sehen wir gerade enorme Konsolidierung – und {kf} positioniert sich damit aktiv fuer weiteres Wachstum", ergaenzt Mike Bergmann, Gruender der Mike Bergmann Akademie. "Die Verbindung von gewachsener Mittelstands-Erfahrung und der strategischen Synergiepotenzialen ist genau der Treiber, den der IT-Markt braucht."

Ueber die mibeca GmbH:
Die mibeca GmbH ist als Mike Bergmann Akademie spezialisiert auf M&A-Beratung fuer IT-Unternehmen im deutschsprachigen Raum. Sie begleitet Verkaeufer wie Kaeufer professionell durch den gesamten Transaktionsprozess.
"""


@app.route(route="pr-erstellen", methods=["POST", "OPTIONS"])
def pr_erstellen(req: func.HttpRequest) -> func.HttpResponse:
    """Erzeugt eine Pressemitteilung. Body: { targetId, deal-Daten... }"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    text = _generate_press_text(body)
    return ok_({"text": text})


@app.route(route="pr-versand", methods=["POST", "OPTIONS"])
def pr_versand(req: func.HttpRequest) -> func.HttpResponse:
    """Verschickt die Pressemitteilung an ausgewaehlte Pressekontakte.
    Body: { targetId, betreff, text, empfaengerEmails: [], anrede? }"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    text = body.get("text", "")
    betreff = body.get("betreff", "Pressemitteilung – Unternehmensverkauf")
    empfaenger = body.get("empfaengerEmails", [])
    if not (text and empfaenger):
        return err_("Text und mindestens ein Empfaenger erforderlich", 400)
    if not ACS_CONN:
        return err_("E-Mail-Service nicht konfiguriert", 500)
    try:
        from azure.communication.email import EmailClient
        client = EmailClient.from_connection_string(ACS_CONN)
        html_text = "<p>" + text.replace("\n\n", "</p><p>").replace("\n", "<br/>") + "</p>"
        gesendet = []
        for rcpt in empfaenger:
            try:
                client.begin_send({
                    "senderAddress": ACS_SENDER,
                    "recipients": {"to": [{"address": rcpt}]},
                    "content": {"subject": betreff, "plainText": text, "html": f"<html><body style='font-family:Arial,sans-serif;line-height:1.6'>{html_text}<p style='font-size:11px;color:#888;margin-top:24px;border-top:1px solid #ddd;padding-top:12px'>Diese Mitteilung wurde versendet von der mibeca GmbH (Mike Bergmann Akademie).</p></body></html>"},
                })
                gesendet.append(rcpt)
            except Exception as ex:
                logging.error(f"PR-Versand an {rcpt} fehlgeschlagen: {ex}")
    except Exception as ex:
        return err_(f"Mailversand fehlgeschlagen: {ex}", 500)

    # Status im Target persistieren + Verlauf-Eintrag
    if target_id:
        try:
            targets = table_("targets")
            t = targets.get_entity("target", target_id)
            presse = {}
            try: presse = json.loads(t.get("presseJson", "{}") or "{}")
            except: presse = {}
            presse["versendetAm"] = datetime.utcnow().isoformat()
            presse["versendetVon"] = p.get("name", "")
            presse["empfaenger"] = gesendet
            presse["text"] = text
            t["presseJson"] = json.dumps(presse, ensure_ascii=False)
            targets.update_entity(dict(t))

            _verlauf_append(target_id, {
                "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
                "typ": "wichtig",
                "datum": datetime.utcnow().isoformat(),
                "autor": p.get("name", ""),
                "betreff": f"Pressemitteilung versendet an {len(gesendet)} Fachmedien",
                "beschreibung": f"Pressemitteilung zum Unternehmensverkauf wurde verschickt. Empfaenger: {', '.join(gesendet)}",
                "beteiligte": ", ".join(gesendet),
            })
        except Exception as ex:
            logging.error(f"PR-Status persistieren fehlgeschlagen: {ex}")

    return ok_({"ok": True, "gesendet": gesendet, "count": len(gesendet)})


@app.route(route="pr-zur-freigabe", methods=["POST", "OPTIONS"])
def pr_zur_freigabe(req: func.HttpRequest) -> func.HttpResponse:
    """Schickt den Pressetext an den Verkaeufer/Kaeufer zur Freigabe."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    text = body.get("text", "")
    if not (target_id and text):
        return err_("targetId und text erforderlich", 400)
    target_users = list(table_("users").query_entities(f"targetId eq '{target_id}'"))
    if not target_users:
        return err_("Kein Target-Login fuer dieses Target", 400)
    target_email = target_users[0].get("email", "")
    target_name = target_users[0].get("name", "")
    try:
        targets = table_("targets")
        t = targets.get_entity("target", target_id)
        presse = {}
        try: presse = json.loads(t.get("presseJson", "{}") or "{}")
        except: presse = {}
        presse["text"] = text
        presse["freigabeAngefragtAm"] = datetime.utcnow().isoformat()
        presse["freigabeStatus"] = "pending"
        t["presseJson"] = json.dumps(presse, ensure_ascii=False)
        targets.update_entity(dict(t))
    except Exception as ex:
        return err_(f"Persistierung fehlgeschlagen: {ex}", 500)
    if ACS_CONN and target_email:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            link = f"{FRONTEND_BASE}/?tab=erfolg"
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                <h2 style="color:#097e92">Pressemitteilung zur Freigabe</h2>
                <p>Hallo {target_name or ''},</p>
                <p>wir haben einen Pressetext zu Deinem Unternehmensverkauf vorbereitet. Bitte gib ihn frei
                oder kommentiere gewuenschte Aenderungen direkt im Dashboard.</p>
                <p style="margin:24px 0"><a href="{link}" style="background:#097e92;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Pressetext ansehen &amp; freigeben</a></p>
                </body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": target_email}]},
                "content": {"subject": "Pressetext zur Freigabe – ITUKV Dashboard", "plainText": f"Pressetext ansehen: {link}", "html": html},
            })
        except Exception:
            pass
    _verlauf_append(target_id, {
        "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
        "typ": "mail_out",
        "datum": datetime.utcnow().isoformat(),
        "autor": p.get("name", ""),
        "betreff": "Pressetext zur Freigabe an Kunde geschickt",
        "beschreibung": "Der Pressetext wartet auf Freigabe / Kommentar des Kunden.",
        "beteiligte": target_email,
    })
    return ok_({"ok": True})


@app.route(route="pr-feedback", methods=["POST", "OPTIONS"])
def pr_feedback(req: func.HttpRequest) -> func.HttpResponse:
    """Kunde gibt Feedback (Freigabe oder Aenderungswunsch)."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    freigabe = bool(body.get("freigabe", False))
    kommentar = (body.get("kommentar") or "").strip()
    if not target_id:
        return err_("targetId erforderlich", 400)
    if p.get("role") == "target" and p.get("targetId") and p.get("targetId") != target_id:
        return err_("Nicht autorisiert", 403)
    try:
        targets = table_("targets")
        t = targets.get_entity("target", target_id)
        presse = {}
        try: presse = json.loads(t.get("presseJson", "{}") or "{}")
        except: presse = {}
        presse["freigabeStatus"] = "freigegeben" if freigabe else "aenderung_gewuenscht"
        presse["freigabeAm"] = datetime.utcnow().isoformat()
        presse["freigabeKommentar"] = kommentar
        presse["freigabeVon"] = p.get("name", "") or p.get("email", "")
        t["presseJson"] = json.dumps(presse, ensure_ascii=False)
        targets.update_entity(dict(t))
    except Exception as ex:
        return err_(f"Fehler: {ex}", 500)
    _verlauf_append(target_id, {
        "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
        "typ": "wichtig" if freigabe else "mail_in",
        "datum": datetime.utcnow().isoformat(),
        "autor": p.get("name", ""),
        "betreff": "Pressetext freigegeben" if freigabe else "Aenderungswunsch zum Pressetext",
        "beschreibung": kommentar or ("Pressetext wurde freigegeben." if freigabe else "Kunde wuenscht Aenderungen."),
        "beteiligte": p.get("email", ""),
    })
    if ACS_CONN:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            mibeca_mail = os.environ.get("MIBECA_NOTIFY_EMAIL", "jk@mike-bergmann.de")
            betreff = "Pressetext freigegeben" if freigabe else "Aenderungswunsch zum Pressetext"
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": mibeca_mail}]},
                "content": {"subject": f"[ITUKV] {betreff}", "plainText": f"Kunde {p.get('email','')}: {kommentar or '(kein Kommentar)'}",
                            "html": f"<p><strong>{betreff}</strong></p><p>Von: {p.get('email','')}</p><p>{kommentar}</p>"},
            })
        except Exception:
            pass
    return ok_({"ok": True})


@app.route(route="presse-kontakte", methods=["GET", "OPTIONS"])
def presse_kontakte(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert die Default-Presseliste + Custom-Eintraege aus presse-kontakte-Tabelle."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    items = list(PRESSE_KONTAKTE_DEFAULT)
    try:
        tc = table_("pressekontakte")
        for it in tc.list_entities():
            items.append(dict(it))
    except Exception:
        pass
    return ok_(items)


# =========================================================================
# CONTROLLING / JAHRES-AUSWERTUNG
# =========================================================================

@app.route(route="controlling-stats", methods=["GET", "OPTIONS"])
def controlling_stats(req: func.HttpRequest) -> func.HttpResponse:
    """Aggregierte KPIs aus allen Targets / Mandanten fuer das Controlling-Dashboard."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    year = req.params.get("year", "")
    try:
        year_int = int(year) if year else None
    except Exception:
        year_int = None

    targets = []
    try:
        targets = [dict(t) for t in table_("targets").list_entities()]
    except Exception:
        targets = []

    def get_created(t):
        try: return datetime.fromisoformat((t.get("createdAt") or "").replace("Z",""))
        except: return None
    def get_closed(t):
        try:
            v = json.loads(t.get("vertragJson", "{}") or "{}")
            if v.get("gegengezeichnetAm"):
                return datetime.fromisoformat(v["gegengezeichnetAm"].replace("Z",""))
        except: pass
        # fallback: status=verkauft
        if t.get("status") == "verkauft":
            return get_created(t)
        return None
    def get_current_phase(t):
        try:
            phasen = json.loads(t.get("phasenJson", "[]") or "[]")
            for i, ph in enumerate(phasen):
                aufgaben = ph.get("aufgaben") or []
                if not aufgaben or not all(a.get("done") for a in aufgaben):
                    return i + 1
            return len(phasen) or 0
        except: return 0
    def has_press(t):
        try:
            p_ = json.loads(t.get("presseJson", "{}") or "{}")
            return bool(p_.get("versendetAm"))
        except: return False

    # Year-Filter
    in_year = lambda t: True if not year_int else ((get_created(t) and get_created(t).year == year_int) or (get_closed(t) and get_closed(t).year == year_int))
    filtered = [t for t in targets if in_year(t)]

    closed = [t for t in filtered if get_closed(t)]
    open_ = [t for t in filtered if not get_closed(t)]

    # Deal-Dauer in Tagen (nur abgeschlossene)
    durations = []
    for t in closed:
        c = get_created(t); d = get_closed(t)
        if c and d and d > c:
            durations.append((d - c).days)
    avg_duration = round(sum(durations) / len(durations)) if durations else 0

    # Pipeline-Funnel: aktuelle Phase pro offenes Mandat
    phase_buckets = {"1-3": 0, "4-6": 0, "7-9": 0, "10-12": 0, "13-15": 0}
    for t in open_:
        ph = get_current_phase(t)
        if 1 <= ph <= 3: phase_buckets["1-3"] += 1
        elif 4 <= ph <= 6: phase_buckets["4-6"] += 1
        elif 7 <= ph <= 9: phase_buckets["7-9"] += 1
        elif 10 <= ph <= 12: phase_buckets["10-12"] += 1
        elif ph >= 13: phase_buckets["13-15"] += 1

    # Dauer pro Variante / Projekttyp
    by_typ = {}
    for t in closed:
        c = get_created(t); d = get_closed(t)
        if c and d:
            typ = t.get("projekttyp", "Andere")
            by_typ.setdefault(typ, []).append((d - c).days)
    dauer_pro_typ = {typ: round(sum(v)/len(v)) for typ, v in by_typ.items() if v}

    # Verkaufs- vs Kauf-Mandate
    is_kauf = lambda t: any(k in (t.get("projekttyp","") or "") for k in ("Kauf", "Investor"))
    kauf_anzahl = sum(1 for t in filtered if is_kauf(t))
    verkauf_anzahl = len(filtered) - kauf_anzahl

    # PR-Anteil bei abgeschlossenen Deals
    pr_count = sum(1 for t in closed if has_press(t))
    pr_quote = round(100 * pr_count / len(closed)) if closed else 0

    # Erfolgsquote
    success_rate = round(100 * len(closed) / len(filtered)) if filtered else 0

    # Monthly-Series fuer Chart
    by_month = {}
    for t in filtered:
        d = get_closed(t) or get_created(t)
        if not d: continue
        key = d.strftime("%Y-%m")
        by_month.setdefault(key, {"created": 0, "closed": 0})
        if get_created(t): by_month[key]["created"] += 1 if get_created(t).strftime("%Y-%m") == key else 0
        if get_closed(t) and get_closed(t).strftime("%Y-%m") == key:
            by_month[key]["closed"] += 1
    monthly = [{"month": k, **v} for k, v in sorted(by_month.items())]

    return ok_({
        "year": year_int,
        "total": len(filtered),
        "open": len(open_),
        "closed": len(closed),
        "successRate": success_rate,
        "avgDurationDays": avg_duration,
        "pipelineFunnel": phase_buckets,
        "dauerProTyp": dauer_pro_typ,
        "kaufAnzahl": kauf_anzahl,
        "verkaufAnzahl": verkauf_anzahl,
        "prCount": pr_count,
        "prQuote": pr_quote,
        "monthly": monthly,
        "yearsAvailable": sorted({
            (get_created(t) or get_closed(t)).year for t in targets
            if (get_created(t) or get_closed(t))
        }, reverse=True),
    })


@app.route(route="lessons-learned", methods=["GET", "OPTIONS"])
def lessons_learned_aggregat(req: func.HttpRequest) -> func.HttpResponse:
    """Aggregiert Lessons Learned aller Targets fuer Wissensdatenbank."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    items = []
    try:
        for t in table_("targets").list_entities():
            ll = t.get("lessonsLearnedJson", "")
            if not ll: continue
            try:
                d = json.loads(ll)
                if any([d.get("pro"), d.get("contra"), d.get("anders"), d.get("keyLearning")]):
                    items.append({
                        "targetId": t.get("RowKey"),
                        "mbNr": t.get("mbNr", ""),
                        "verkaueferName": t.get("verkaueferName", ""),
                        "projekttyp": t.get("projekttyp", ""),
                        **d,
                    })
            except Exception:
                pass
    except Exception:
        pass
    return ok_({"items": items})


# =========================================================================
# OEFFENTLICHE LANDING-PAGE & ANFRAGE-WORKFLOW (mb-XXX)
# =========================================================================

@app.route(route="landing-public", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def landing_public(req: func.HttpRequest) -> func.HttpResponse:
    """Public: liefert Landing-Page-Daten fuer eine mb-Nr."""
    if req.method == "OPTIONS":
        return opt_()
    mb_nr = (req.params.get("mbNr") or "").strip().lower()
    if not mb_nr:
        return err_("mbNr erforderlich", 400)
    try:
        items = list(table_("targets").list_entities())
        t = next((x for x in items if (x.get("mbNr", "") or "").lower() == mb_nr), None)
    except Exception:
        t = None
    if not t:
        return err_("Projekt nicht gefunden", 404)
    landing = {}
    try: landing = json.loads(t.get("landingJson", "{}") or "{}")
    except: landing = {}
    if landing.get("status") != "published":
        return err_("Projekt nicht veroeffentlicht", 404)
    # Nur die public-safe Felder
    return ok_({
        "mbNr": t.get("mbNr", ""),
        "targetId": t.get("RowKey", ""),
        "headline": landing.get("headline", ""),
        "subheadline": landing.get("subheadline", ""),
        "description": landing.get("description", ""),
        "keyFacts": landing.get("keyFacts", []),
        "highlights": landing.get("highlights", []),
        "published": True,
    })


@app.route(route="landing-anfrage", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def landing_anfrage(req: func.HttpRequest) -> func.HttpResponse:
    """Public: ein Interessent registriert sich fuer mb-XXX."""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    mb_nr = (body.get("mbNr") or "").strip().lower()
    firma = (body.get("firma") or "").strip()
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    if not (mb_nr and email and (firma or name)):
        return err_("mbNr, email und firma oder name erforderlich", 400)
    # Target finden
    items = list(table_("targets").list_entities())
    t = next((x for x in items if (x.get("mbNr", "") or "").lower() == mb_nr), None)
    if not t:
        return err_("Projekt nicht gefunden", 404)
    target_id = t.get("RowKey", "")
    # Interessent anlegen
    iid = str(uuid.uuid4())
    token = secrets.token_urlsafe(24)
    entity = {
        "PartitionKey": "interessent", "RowKey": iid,
        "targetId": target_id,
        "firma": firma, "name": name, "email": email,
        "telefon": body.get("telefon", ""),
        "plz": body.get("plz", ""), "ort": body.get("ort", ""),
        "ndaStatus": "ausstehend",
        "exposeToken": token,  # fuer expose-mb-XXX/:token Zugriff
        "rating": 0, "veto": False, "freigegebenFuerKontakt": False,
        "kommentar": body.get("kommentar", ""),
        "createdAt": datetime.utcnow().isoformat(),
        "herkunft": f"Landing-Page {mb_nr}",
    }
    table_("interessenten").create_entity(entity)

    # Verlauf-Eintrag im Target
    _verlauf_append(target_id, {
        "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
        "typ": "wichtig",
        "datum": datetime.utcnow().isoformat(),
        "autor": "Landing-Page",
        "betreff": f"Neue Anfrage von {firma or name}",
        "beschreibung": f"Interessent hat sich ueber die Landing-Page {mb_nr} eingetragen. E-Mail: {email}",
        "beteiligte": email,
    })

    # Mail an Interessent: Expose-Link + NDA
    expose_url = f"{FRONTEND_BASE}/expose-{mb_nr}/{token}"
    if ACS_CONN:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            # An Interessent
            html_int = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                <h2 style="color:#097e92">Willkommen bei mibeca · Projekt {mb_nr.upper()}</h2>
                <p>Hallo {name or firma},</p>
                <p>vielen Dank fuer Dein Interesse am Projekt <strong>{mb_nr}</strong>. Hier geht's zu Deinem Exposé-Bereich (Exposé + NDA herunterladen, signiertes NDA hochladen):</p>
                <p style="margin:24px 0"><a href="{expose_url}" style="background:#097e92;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Zum Exposé-Bereich</a></p>
                <p>Nach Eingang Deines unterschriebenen NDAs schalten wir die Termin-Buchung mit unserer M&amp;A-Beraterin Jennifer Kaplan frei.</p>
                <p>Viele Gruesse<br/>Dein mibeca-Team</p>
                </body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": email}]},
                "content": {"subject": f"Dein Exposé zu Projekt {mb_nr.upper()}", "plainText": f"Exposé-Bereich: {expose_url}", "html": html_int},
            })
            # An mibeca-Team + Target-User
            notify_to = [os.environ.get("MIBECA_NOTIFY_EMAIL", "jk@mike-bergmann.de")]
            tu = list(table_("users").query_entities(f"targetId eq '{target_id}'"))
            for u in tu:
                if u.get("email"): notify_to.append(u["email"])
            for rcpt in notify_to:
                client.begin_send({
                    "senderAddress": ACS_SENDER,
                    "recipients": {"to": [{"address": rcpt}]},
                    "content": {"subject": f"[ITUKV] Neue Anfrage zu {mb_nr.upper()}", "plainText": f"{firma or name} ({email}) interessiert sich fuer {mb_nr}.", "html": f"<p><strong>Neue Anfrage zu {mb_nr.upper()}</strong></p><p>Firma: {firma}</p><p>Name: {name}</p><p>E-Mail: {email}</p>"},
                })
        except Exception as ex:
            logging.warning(f"Anfrage-Mail fehlgeschlagen: {ex}") if 'logging' in globals() else None
    return ok_({"ok": True, "exposeUrl": expose_url})


@app.route(route="expose-public", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def expose_public(req: func.HttpRequest) -> func.HttpResponse:
    """Public: liefert Exposé-Bereich-Daten anhand exposeToken."""
    if req.method == "OPTIONS":
        return opt_()
    token = (req.params.get("token") or "").strip()
    if not token:
        return err_("token erforderlich", 400)
    items = list(table_("interessenten").query_entities(f"exposeToken eq '{token}'"))
    if not items:
        return err_("Token ungueltig", 404)
    i = dict(items[0])
    target_id = i.get("targetId", "")
    try:
        t = dict(table_("targets").get_entity("target", target_id))
    except Exception:
        return err_("Target nicht gefunden", 404)
    landing = {}
    try: landing = json.loads(t.get("landingJson", "{}") or "{}")
    except: landing = {}
    return ok_({
        "mbNr": t.get("mbNr", ""),
        "firma": i.get("firma", ""),
        "name": i.get("name", ""),
        "ndaStatus": i.get("ndaStatus", "ausstehend"),
        "ndaUploadedAt": i.get("ndaUploadedAt", ""),
        "exposeUrl": landing.get("exposeUrl", ""),
        "ndaTemplateUrl": landing.get("ndaTemplateUrl", ""),
        "terminBookingUrl": landing.get("terminBookingUrl", ""),
        "headline": landing.get("headline", ""),
    })


@app.route(route="nda-upload", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def nda_upload(req: func.HttpRequest) -> func.HttpResponse:
    """Public: Interessent laedt unterschriebenes NDA hoch.
    Body: { token, fileName, fileData (base64), email-Verifikation? }"""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    token = (body.get("token") or "").strip()
    file_data = body.get("fileData", "")
    file_name = body.get("fileName", "nda.pdf")
    if not (token and file_data):
        return err_("token + fileData erforderlich", 400)
    items = list(table_("interessenten").query_entities(f"exposeToken eq '{token}'"))
    if not items:
        return err_("Token ungueltig", 404)
    i = dict(items[0])
    target_id = i.get("targetId", "")
    # Blob speichern
    try:
        if file_data.startswith("data:"):
            file_data = file_data.split(",", 1)[1]
        pdf_bytes = base64.b64decode(file_data)
        blob_name = f"nda-interessent-{i['RowKey']}.pdf"
        _blob_container_lazy("vertraege").upload_blob(blob_name, pdf_bytes, overwrite=True)
    except Exception as ex:
        return err_(f"Upload fehlgeschlagen: {ex}", 500)
    # Update Interessent
    i["ndaStatus"] = "unterzeichnet"
    i["ndaUploadedAt"] = datetime.utcnow().isoformat()
    i["ndaBlob"] = blob_name
    i["ndaFileName"] = file_name
    try:
        table_("interessenten").update_entity(i)
    except Exception:
        pass
    # Verlauf + Notification
    _verlauf_append(target_id, {
        "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
        "typ": "wichtig",
        "datum": datetime.utcnow().isoformat(),
        "autor": i.get("firma") or i.get("name") or i.get("email", ""),
        "betreff": "NDA-Upload",
        "beschreibung": f"{i.get('firma') or i.get('name')} hat das unterschriebene NDA hochgeladen ({file_name}).",
        "beteiligte": i.get("email", ""),
    })
    # Welcome-Mail nach NDA (deine Vorlage)
    if ACS_CONN:
        try:
            t = dict(table_("targets").get_entity("target", target_id))
            landing = {}
            try: landing = json.loads(t.get("landingJson", "{}") or "{}")
            except: landing = {}
            termin_url = landing.get("terminBookingUrl", "")
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
<p>Hallo {i.get('name') or i.get('firma') or ''},</p>
<p>vielen Dank fuer Dein unterschriebenes NDA zur Projektnummer <strong>{t.get('mbNr','')}</strong> &ndash; damit hast Du den ersten wichtigen Schritt gemacht!</p>
<h3 style="color:#097e92">Wie geht es jetzt weiter?</h3>
<p>Du hast nun Zugang zum Exposé, das Dir einen ersten Ueberblick ueber das Unternehmen gibt. Fuer tiefergehende Informationen und Zahlen ist ein persoenliches Gespraech erforderlich.</p>
<p>Buche hier Deinen Termin mit unserer M&amp;A-Beraterin Jennifer Kaplan:</p>
{(('<p style="margin:24px 0"><a href="' + termin_url + '" style="background:#097e92;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Termin jetzt buchen</a></p>') if termin_url else '<p><em>Termin-Link wird in Kuerze nachgereicht.</em></p>')}
<p>In diesem ca. 15-minuetigen Gespraech klaert Ihr:</p>
<ul>
  <li>Ob das Unternehmen zu Deiner Zukaufstrategie passt</li>
  <li>Deine konkreten Zukaufsvisionen &ndash; damit wir diese mit dem Profil abgleichen koennen</li>
  <li>Den weiteren Ablauf des Prozesses</li>
  <li>Wie die Rolle unserer M&amp;A-Beraterin Dich durch den gesamten Transaktionsprozess begleitet</li>
  <li>Ob ggf. ein Folgegespraech direkt mit dem Verkaeufer sinnvoll ist</li>
</ul>
<p><strong>Wichtig:</strong> Nur wenn die ersten Parameter nach dem Gespraech uebereinstimmen, senden wir Dir im Anschluss weitere Unterlagen &ndash; z.B. detaillierte Unternehmenskennzahlen.</p>
<p>Wir freuen uns auf den Austausch!</p>
<p>Herzliche Gruesse<br/>Dein M&amp;A-Team der Mike Bergmann Akademie</p>
</body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": i.get("email", "")}]},
                "content": {"subject": f"NDA erhalten – naechste Schritte zu {t.get('mbNr','')}", "plainText": f"NDA bestaetigt. Termin buchen: {termin_url}", "html": html},
            })
            # Notification an Jenny
            mibeca_mail = os.environ.get("MIBECA_NOTIFY_EMAIL", "jk@mike-bergmann.de")
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": mibeca_mail}]},
                "content": {"subject": f"[ITUKV] NDA erhalten zu {t.get('mbNr','')}", "plainText": f"{i.get('firma') or i.get('name')} hat NDA hochgeladen.", "html": f"<p><strong>NDA erhalten</strong> – Interessent kann jetzt Termin buchen.</p><p>Projekt: {t.get('mbNr','')}</p><p>Interessent: {i.get('firma','')} / {i.get('name','')} / {i.get('email','')}</p>"},
            })
        except Exception as ex:
            logging.warning(f"NDA-Mail fehlgeschlagen: {ex}") if 'logging' in globals() else None
    return ok_({"ok": True})


# =========================================================================
# DOKUMENTE / DATENRAUM mit Azure Blob Storage
# =========================================================================

@app.route(route="dokument-upload", methods=["POST", "OPTIONS"])
def dokument_upload(req: func.HttpRequest) -> func.HttpResponse:
    """Upload einer Datei in den Datenraum eines Targets.
    Body: { targetId, ordner, fileName, fileData (base64), contentType? }
    Target-User duerfen nur ihren eigenen Datenraum hochladen."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    ordner = (body.get("ordner") or "Allgemein").strip()
    file_name = (body.get("fileName") or "datei").strip()
    file_data = body.get("fileData", "")
    content_type = body.get("contentType", "application/octet-stream")
    if not (target_id and file_data):
        return err_("targetId + fileData erforderlich", 400)
    # Target-User darf nur eigene Dateien hochladen
    if p.get("role") == "target":
        if p.get("targetId") and p.get("targetId") != target_id:
            return err_("Nicht autorisiert", 403)
    try:
        if file_data.startswith("data:"):
            file_data = file_data.split(",", 1)[1]
        binary = base64.b64decode(file_data)
    except Exception as ex:
        return err_(f"Decoding fehlgeschlagen: {ex}", 400)
    # Blob hochladen
    blob_name = f"{target_id}/{ordner}/{uuid.uuid4()}_{file_name}"
    try:
        container = _blob_container_lazy("datenraum")
        from azure.storage.blob import ContentSettings
        container.upload_blob(blob_name, binary, overwrite=False,
                              content_settings=ContentSettings(content_type=content_type))
    except Exception as ex:
        return err_(f"Upload fehlgeschlagen: {ex}", 500)
    # Metadaten in Table
    doc_id = str(uuid.uuid4())
    entity = {
        "PartitionKey": target_id,
        "RowKey": doc_id,
        "ordner": ordner,
        "fileName": file_name,
        "blobName": blob_name,
        "contentType": content_type,
        "size": len(binary),
        "uploadedBy": p.get("name", "") or p.get("email", ""),
        "uploadedByRole": p.get("role", ""),
        "uploadedAt": datetime.utcnow().isoformat(),
    }
    table_("dokumente").create_entity(entity)
    return ok_({"id": doc_id, "fileName": file_name, "ordner": ordner, "size": len(binary), "uploadedAt": entity["uploadedAt"], "uploadedBy": entity["uploadedBy"]}, 201)


@app.route(route="dokument-list", methods=["GET", "POST", "OPTIONS"])
def dokument_list(req: func.HttpRequest) -> func.HttpResponse:
    """Liste der Dokumente eines Targets."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    target_id = req.params.get("targetId") or ""
    if req.method == "POST":
        b = req.get_json() or {}
        target_id = b.get("targetId", "")
    if not target_id:
        return err_("targetId erforderlich", 400)
    if p.get("role") == "target":
        if p.get("targetId") and p.get("targetId") != target_id:
            return err_("Nicht autorisiert", 403)
    try:
        items = [dict(d) for d in table_("dokumente").query_entities(f"PartitionKey eq '{target_id}'")]
    except Exception:
        items = []
    items.sort(key=lambda x: x.get("uploadedAt", ""), reverse=True)
    return ok_({"items": items})


@app.route(route="dokument-download", methods=["GET", "OPTIONS"])
def dokument_download(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert das Dokument als Datei."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    target_id = req.params.get("targetId", "")
    doc_id = req.params.get("id", "")
    if not (target_id and doc_id):
        return err_("targetId + id erforderlich", 400)
    if p.get("role") == "target":
        if p.get("targetId") and p.get("targetId") != target_id:
            return err_("Nicht autorisiert", 403)
    try:
        ent = dict(table_("dokumente").get_entity(target_id, doc_id))
    except Exception:
        return err_("Dokument nicht gefunden", 404)
    try:
        data = _blob_container_lazy("datenraum").download_blob(ent["blobName"]).readall()
    except Exception as ex:
        return err_(f"Download fehlgeschlagen: {ex}", 500)
    return func.HttpResponse(data, status_code=200,
                             mimetype=ent.get("contentType", "application/octet-stream"),
                             headers={**CORS, "Content-Disposition": f'attachment; filename="{ent.get("fileName","file")}"'})


@app.route(route="dokument-delete", methods=["POST", "OPTIONS"])
def dokument_delete(req: func.HttpRequest) -> func.HttpResponse:
    """Loescht ein Dokument – NUR Admin."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nur Admin darf Dokumente loeschen", 403)
    b = req.get_json() or {}
    target_id = b.get("targetId", "")
    doc_id = b.get("id", "")
    if not (target_id and doc_id):
        return err_("targetId + id erforderlich", 400)
    try:
        ent = dict(table_("dokumente").get_entity(target_id, doc_id))
    except Exception:
        return err_("Dokument nicht gefunden", 404)
    # Blob loeschen
    try: _blob_container_lazy("datenraum").delete_blob(ent["blobName"])
    except Exception: pass
    try: table_("dokumente").delete_entity(target_id, doc_id)
    except Exception: pass
    return ok_({"deleted": True})


@app.route(route="dokument-move", methods=["POST", "OPTIONS"])
def dokument_move(req: func.HttpRequest) -> func.HttpResponse:
    """Aendert den Ordner eines Dokuments. Admin oder Target-Owner."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    b = req.get_json() or {}
    target_id = b.get("targetId", "")
    doc_id = b.get("id", "")
    neuer_ordner = (b.get("ordner") or "").strip()
    if not (target_id and doc_id and neuer_ordner):
        return err_("targetId, id, ordner erforderlich", 400)
    if p.get("role") == "target":
        if p.get("targetId") and p.get("targetId") != target_id:
            return err_("Nicht autorisiert", 403)
    try:
        ent = dict(table_("dokumente").get_entity(target_id, doc_id))
        ent["ordner"] = neuer_ordner
        table_("dokumente").update_entity(ent)
    except Exception as ex:
        return err_(f"Move fehlgeschlagen: {ex}", 500)
    return ok_({"ok": True})
