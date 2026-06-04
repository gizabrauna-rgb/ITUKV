import azure.functions as func
import json
import logging
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
JWT_SECRET = os.environ.get("JWT_SECRET", "")
# Sicherheits-Assertion: dev-secret oder leerer JWT_SECRET ist Production verboten.
# Tokens mit "dev-secret" sind trivial faelschbar.
if not JWT_SECRET or JWT_SECRET == "dev-secret":
    # In Azure muss JWT_SECRET als App-Setting gesetzt sein. Lokal:
    # `func start` mit local.settings.json. Falls leer -> harter Fehler beim ersten Auth-Versuch.
    logging.error("[SECURITY] JWT_SECRET ist nicht gesetzt oder == 'dev-secret'. Auth wird verweigert.")
    JWT_SECRET = ""  # erzwingt Auth-Fehlschlag

# Microsoft Entra ID (multi-tenant App Registration) - Audience fuer ID-Token-Verifikation.
# Nicht geheim; identisch mit VITE_APP_REGISTRATION_CLIENTID im Frontend.
MS_CLIENT_ID = os.environ.get("MS_CLIENT_ID", "0e531dfd-9c67-460c-b9f5-c2d57c60cb83")


def odata_quote(s):
    """Escape Single-Quotes fuer OData-Filter (verhindert Injection).
    Azure Table Storage erlaubt nur '' als Escape fuer '."""
    if s is None:
        return ""
    return str(s).replace("'", "''")


def is_valid_public_token(token, min_len=24):
    """Sanity-Check fuer oeffentliche Tokens (Brute-Force-Schutz).
    Tokens unter 24 Zeichen oder mit ungueltigen Zeichen werden ohne DB-Lookup abgewiesen."""
    if not token or not isinstance(token, str):
        return False
    if len(token) < min_len or len(token) > 256:
        return False
    # URL-safe base64 chars: A-Z a-z 0-9 - _ (kein /, +, =)
    return all(c.isalnum() or c in "-_" for c in token)

# Erlaubte Frontend-Origins (kein Wildcard mehr - schuetzt vor cross-site API-Calls).
# Falls weitere Domains noetig werden, FRONTEND_BASE_URL (Komma-Liste) in Azure-App-Settings setzen.
_ALLOWED_ORIGINS = set(filter(None, [
    "https://dashboard.itukv.de",
    "https://www.itukv.de",
    "https://itukv.de",
    "http://localhost:5173",
    "http://localhost:4173",
] + [o.strip().rstrip("/") for o in os.environ.get("FRONTEND_BASE_URL", "").split(",") if o.strip()]))

_DEFAULT_ALLOW_ORIGIN = "https://dashboard.itukv.de"

CORS = {
    "Access-Control-Allow-Origin": _DEFAULT_ALLOW_ORIGIN,
    "Vary": "Origin",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, x-webhook-key",
    "Content-Type": "application/json",
}


def ok_(data, status=200):
    return func.HttpResponse(json.dumps(data, default=str), status_code=status, headers=CORS)

def err_(msg, status=400):
    return func.HttpResponse(json.dumps({"error": msg}), status_code=status, headers=CORS)

def opt_():
    return func.HttpResponse("", status_code=204, headers=CORS)


def pdf_response(pdf_bytes, filename, inline=True):
    """Liefert ein PDF mit korrekten Headern.
    WICHTIG: Setzt Content-Type explizit auf application/pdf, weil das
    globale CORS-Dict den Default 'application/json' enthaelt - sonst
    rendert der Browser die Bytes als Text."""
    safe_name = (filename or "datei.pdf").replace('"', '_')
    disposition = "inline" if inline else "attachment"
    headers = {
        **CORS,
        "Content-Type": "application/pdf",
        "Content-Disposition": f'{disposition}; filename="{safe_name}"',
        "Cache-Control": "private, no-store",
    }
    return func.HttpResponse(pdf_bytes, status_code=200, headers=headers)

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


# PBKDF2-Iterationen (OWASP-Empfehlung 2024+).
# Hash-Format: pbkdf2$ITER$salt_b64$hash_b64 (4 Felder, neu) ODER
#              pbkdf2$salt_b64$hash_b64 (3 Felder, Legacy -> 100000 Iterationen).
PBKDF2_ITER = 600000

def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, PBKDF2_ITER)
    return f"pbkdf2${PBKDF2_ITER}${base64.b64encode(salt).decode()}${base64.b64encode(h).decode()}"

def verify_password(pw: str, stored: str) -> bool:
    """Akzeptiert beide Formate (3- und 4-Felder) damit Bestands-Logins nicht brechen."""
    if not stored or not stored.startswith("pbkdf2$"):
        return False
    try:
        parts = stored.split("$")
        if len(parts) == 4:
            _, iter_s, salt_b64, hash_b64 = parts
            iters = int(iter_s)
        elif len(parts) == 3:
            _, salt_b64, hash_b64 = parts
            iters = 100000  # Legacy
        else:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        actual = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, iters)
        return hmac.compare_digest(expected, actual)
    except Exception:
        return False


def make_jwt(uid, role, name, email, target_id=""):
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET nicht konfiguriert - Token-Erstellung verweigert.")
    payload = {"id": uid, "role": role, "name": name, "email": email,
               "targetId": target_id or "",
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
    if not JWT_SECRET:
        return None
    a = req.headers.get("Authorization", "")
    if not a.startswith("Bearer "):
        return None
    try:
        h, p, s = a[7:].split('.')
        expected = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64ud(s), expected):
            return None
        payload = json.loads(_b64ud(p))
        if int(payload.get("exp", 0)) < int(datetime.utcnow().timestamp()):
            return None
        _touch_last_seen(payload.get("id"))
        return payload
    except Exception:
        return None


# Microsoft Entra ID Token-Verifikation (multi-tenant)
# JWKS-Cache pro Tenant, damit nicht bei jedem Login ein HTTP-Call rausgeht.
_MS_JWKS_CACHE = {}

def _verify_ms_id_token(token):
    """Verifiziert ein Microsoft ID-Token gegen Microsoft JWKS.
    Liefert verifizierte Claims dict oder None bei Fehlschlag.
    NIEMALS die Email/UPN aus unverifizierten Claims uebernehmen."""
    try:
        import jwt as pyjwt
        from jwt import PyJWKClient
    except Exception as ex:
        logging.error(f"[SECURITY] PyJWT nicht installiert: {ex}")
        return None
    if not token or not isinstance(token, str):
        return None
    try:
        # Tenant aus unverifiziertem Header lesen, um den passenden JWKS-Endpunkt zu finden.
        # Signatur wird DANACH verifiziert -> sicher.
        unverified = pyjwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        tid = unverified.get("tid")
        if not tid or not all(c.isalnum() or c == "-" for c in tid):
            return None
        jwks_url = f"https://login.microsoftonline.com/{tid}/discovery/v2.0/keys"
        if jwks_url not in _MS_JWKS_CACHE:
            _MS_JWKS_CACHE[jwks_url] = PyJWKClient(jwks_url, cache_keys=True)
        client = _MS_JWKS_CACHE[jwks_url]
        signing_key = client.get_signing_key_from_jwt(token).key
        issuer = f"https://login.microsoftonline.com/{tid}/v2.0"
        claims = pyjwt.decode(
            token, signing_key, algorithms=["RS256"],
            audience=MS_CLIENT_ID, issuer=issuer,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
        return claims
    except Exception as ex:
        logging.warning(f"[SECURITY] MS-Token-Verifikation fehlgeschlagen: {ex}")
        return None


@app.route(route="ping", methods=["GET"])
def ping(req: func.HttpRequest) -> func.HttpResponse:
    return ok_({"status": "ok"})


@app.route(route="auth/resolve", methods=["POST", "OPTIONS"])
def auth_resolve(req: func.HttpRequest) -> func.HttpResponse:
    """Login via Microsoft Entra ID. Erwartet ein verifiziertes MS-ID-Token
    im Authorization-Header (Bearer). Die Email aus dem Body wird IGNORIERT
    und durch den verifizierten preferred_username/email-Claim ersetzt."""
    if req.method == "OPTIONS":
        return opt_()
    a = req.headers.get("Authorization", "") or ""
    if not a.startswith("Bearer "):
        return err_("Microsoft-Token erforderlich", 401)
    claims = _verify_ms_id_token(a[7:])
    if not claims:
        return err_("Microsoft-Token ungueltig", 401)
    # Email aus VERIFIZIERTEN Claims, nie aus dem Request-Body.
    email = (claims.get("preferred_username") or claims.get("email") or claims.get("upn") or "").lower().strip()
    name = claims.get("name") or email
    if not email:
        return err_("Token enthaelt keine Email", 401)
    tc = table_("users")
    users = list(tc.query_entities("email eq @email", parameters={"email": email}))
    if users:
        u = users[0]
        token = make_jwt(u["RowKey"], u["role"], u.get("name", name), email, u.get("targetId", ""))
        return ok_({"token": token, "role": u["role"], "name": u.get("name", name), "id": u["RowKey"], "targetId": u.get("targetId", "")})
    # Kein Bootstrap mehr - neue User muessen vom Admin angelegt werden.
    return err_("Kein Zugang. Bitte wende dich an den Administrator.", 403)


@app.route(route="health", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def health_route(req: func.HttpRequest) -> func.HttpResponse:
    """Anonymous Health-Check fuer Deploy-Pipeline.
    Liefert 200 wenn Host laeuft + Modul geladen ist. Keine DB-Aufrufe."""
    if req.method == "OPTIONS":
        return opt_()
    return func.HttpResponse(
        json.dumps({"ok": True, "ts": datetime.utcnow().isoformat()}),
        status_code=200, mimetype="application/json",
        headers=CORS,
    )


@app.route(route="stats", methods=["GET", "OPTIONS"])
def stats_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    try:
        aktiv, verkauft = 0, 0
        for t in table_("targets").list_entities():
            s = (t.get("status") or "").lower()
            if s == "verkauft": verkauft += 1
            elif s != "abgebrochen": aktiv += 1
        offene_ndas = 0
        for i in table_("interessenten").list_entities():
            if (i.get("ndaStatus") or "") != "unterzeichnet":
                offene_ndas += 1
        investoren = 0
        for k in table_("kontakte").list_entities():
            if k.get("istInvestor"): investoren += 1
        return ok_({
            "aktiveTargets": aktiv,
            "offeneNdas": offene_ndas,
            "investorenGesamt": investoren,
            "dealsAbgeschlossen": verkauft,
        })
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
        # IDOR-Schutz: target/investor sehen nur die eigene Akte
        role = p.get("role", "")
        if role in ("target", "investor"):
            my_tid = p.get("targetId", "")
            items = [i for i in items if i.get("RowKey") == my_tid]
        elif role != "admin" and role != "ai-agent":
            return err_("Nicht autorisiert", 401)
        return ok_(items)
    # POST – neues Target: nur Admins
    if p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json()
    tid = str(uuid.uuid4())
    # Minimale Phasen-Vorlage (15 Master-Phasen, ohne Aufgabenliste – die
    # detaillierte Liste setzt PhasenProzess.vue beim ersten Oeffnen)
    projekttyp = body.get("projekttyp", "Projekt Target")
    if "Kauf" in projekttyp or "Investor" in projekttyp:
        phasen_titel = [
            "Suchprofil definieren",
            "Markt-Screening (mibeca)",
            "Long-List Übergabe",
            "Short-List Käufer-Auswahl",
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
            "UVE Abschluss – Verkaufsmandat-Eröffnung",
            "Marktansprache – Interessenten anschreiben",
            "NDA von Interessenten abholen",
            "Erstes Kennenlernen – Interessent Verkäufer",
            "Datenraum / Kommunikationsraum in Element",
            "Austausch von Unterlagen",
            "Indikatives Angebot",
            "Verhandlungen",
            "Letter of Intent (LOI)",
            "Due Diligence",
            "Vertragsgestaltung",
            "Notartermin & Closing",
            "Post-Closing – Übergabe & Kommunikation",
            "Erfolgsmeldung & Abrechnung",
        ]
    init_phasen = [{"id": i+1, "titel": f"{i+1}. {t}", "notiz": "", "aufgaben": []} for i, t in enumerate(phasen_titel)]
    entity = {
        "PartitionKey": "target", "RowKey": tid,
        "mbNr": body.get("mbNr", ""),
        "verkaueferName": body.get("verkaueferName", ""),
        "firma": body.get("firma", ""),
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
    # IDOR-Schutz: Nicht-Admins duerfen nur ihre eigene Akte sehen.
    if p.get("role") != "admin" and p.get("targetId") != tid:
        return err_("Nicht autorisiert", 403)
    try:
        entity = table_("targets").get_entity("target", tid)
        return ok_(dict(entity))
    except Exception:
        return err_("Target nicht gefunden", 404)


# Allowlist: nur diese Felder duerfen ueber target-update gesetzt werden.
# Mass-Assignment-Schutz - unbekannte Felder werden ignoriert statt blind durchgereicht.
TARGET_WRITABLE_FIELDS = {
    # Stammdaten
    "mbNr", "verkaueferName", "firma", "region", "plz", "branche", "mitarbeiter",
    "umsatz", "beschreibung", "projekttyp", "status",
    # Persoenliche Kontaktdaten
    "vorname", "name", "privatEmail", "privatHandy",
    # Vorgangsnummern
    "kundennummer", "transaktionsnummer",
    # Mandatslaufzeit
    "mandatStart", "mandatLaufzeitMonate", "wiedervorlage",
    # Workflow-Status
    "fragebogenStatus", "fragebogenAbgegebenAm",
    "kostenInfoBestaetigtAm",
    "zieleMotivationenJson", "akquisitionsstrategieJson",
    "akquisitionenJson",  # Multi-Akquisition (Liste von einzelnen Käufe pro Käufer-Mandate)
    # JSON-Blobs
    "phasenJson", "exposeJson", "fragebogenJson", "bewertungJson", "landingJson",
    "vertragJson", "kommunikationJson", "termineJson", "kaeuferFeedbackJson",
    "lessonsLearnedJson", "loiJson", "suchprofilJson", "fuerKaeuferIdsJson",
    "longListManuellJson", "longListDecisionsJson", "presseJson", "bewertungKIJson",
    "geschaeftsfuehrer", "kommentarKI",
    # Unternehmens-Stammdaten (von KI oder manuell pflegbar)
    "rechtsform", "gruendungsjahr", "ebitMarge", "recurringPct",
    # Compliance-Schalter (pro Akte KI-Freigabe)
    "kiAnalyseErlaubt", "kiAnalyseErlaubtSeit", "kiAnalyseErlaubtVon",
    # Diverse Workflow-Felder
    "exposeToken", "ndaTemplateUrl",
    # Per-Mandat Webhook fuer Landing-Page-Anmeldungen (Zapier o.ae.)
    "zapierWebhookUrl",
}


@app.route(route="target-delete", methods=["POST", "OPTIONS"])
def target_delete(req: func.HttpRequest) -> func.HttpResponse:
    """Loescht ein Target (Verkaufs-/Kauf-Mandat). Admin-only.
    Loescht zugehoerige Interessenten, Dokumente und Signaturen mit."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    tid = (body.get("id") or body.get("RowKey") or "").strip()
    if not tid:
        return err_("id erforderlich", 400)
    # Target selbst loeschen
    try:
        table_("targets").delete_entity("target", tid)
    except Exception as ex:
        return err_(f"Target-Loeschung fehlgeschlagen: {ex}", 500)
    # Aufraeumen: Interessenten dieses Targets
    deleted_int = 0
    try:
        for i in table_("interessenten").query_entities("targetId eq @t", parameters={"t": tid}):
            try:
                table_("interessenten").delete_entity(i["PartitionKey"], i["RowKey"])
                deleted_int += 1
            except Exception:
                pass
    except Exception:
        pass
    # Aufraeumen: Dokumente dieses Targets (PartitionKey == targetId)
    deleted_docs = 0
    try:
        for d in table_("dokumente").query_entities("PartitionKey eq @pk", parameters={"pk": tid}):
            try:
                table_("dokumente").delete_entity(d["PartitionKey"], d["RowKey"])
                deleted_docs += 1
            except Exception:
                pass
    except Exception:
        pass
    log_audit(p, "delete", "target", tid, {
        "interessentenGeloescht": deleted_int, "dokumenteGeloescht": deleted_docs,
    })
    return ok_({"deleted": tid, "interessentenGeloescht": deleted_int, "dokumenteGeloescht": deleted_docs})


@app.route(route="target-update", methods=["POST", "OPTIONS"])
def target_update(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    tid = body.pop("id", "")
    if not tid:
        return err_("id erforderlich", 400)
    # IDOR-Schutz: Nicht-Admins duerfen nur ihre eigene Akte aendern.
    if p.get("role") != "admin" and p.get("targetId") != tid:
        return err_("Nicht autorisiert", 403)
    tc = table_("targets")
    try:
        entity = tc.get_entity("target", tid)
    except Exception:
        return err_("Target nicht gefunden", 404)
    # Mass-Assignment-Schutz: nur Felder aus der Allowlist uebernehmen
    # Admin-only-Felder: Nicht-Admins (target/investor) duerfen diese NIE aendern,
    # auch wenn sie ihr eigenes Target updaten.
    ADMIN_ONLY_TARGET_FIELDS = {
        "mbNr", "transaktionsnummer", "kundennummer",
        "projekttyp", "status", "verkaueferName", "firma",
        "mandatStart", "mandatLaufzeitMonate",
    }
    is_admin = p.get("role") == "admin"
    changed = []
    # Vorherige Werte merken, um Mandant-Aktionen im Verlauf zu loggen
    prev_kosten = entity.get("kostenInfoBestaetigtAm", "")
    prev_ziele = entity.get("zieleMotivationenJson", "") or ""
    prev_akq = entity.get("akquisitionsstrategieJson", "") or ""
    prev_fb_status = entity.get("fragebogenStatus", "") or ""

    for k, v in body.items():
        if k not in TARGET_WRITABLE_FIELDS:
            continue
        if k in ADMIN_ONLY_TARGET_FIELDS and not is_admin:
            continue  # still ignorieren - keine Aenderung erlaubt
        if entity.get(k) != v:
            changed.append(k)
        entity[k] = v

    # Auto-Verlauf-Eintraege fuer Mandanten-Aktionen (nur Nicht-Admin)
    if not is_admin and changed:
        verlauf_eintraege = []
        def _add_eintrag(betreff):
            verlauf_eintraege.append({
                "id": "auto" + str(int(datetime.utcnow().timestamp() * 1000)) + str(len(verlauf_eintraege)),
                "typ": "aufgabe",
                "datum": datetime.utcnow().isoformat(),
                "autor": p.get("name") or p.get("email") or "Mandant",
                "betreff": betreff,
                "beschreibung": "",
                "createdBy": p.get("id", ""),
                "createdByMandant": True,
            })
        # Kosten-Tabelle bestaetigt
        if "kostenInfoBestaetigtAm" in changed and entity.get("kostenInfoBestaetigtAm") and not prev_kosten:
            _add_eintrag("Aufgabe erledigt: Kosten-Tabelle zur Kenntnis genommen")
        # Ziele & Motivationen erstmals oder veraendert
        if "zieleMotivationenJson" in changed and entity.get("zieleMotivationenJson"):
            label = "ausgefüllt" if not prev_ziele or prev_ziele == "{}" else "angepasst"
            _add_eintrag(f"Aufgabe erledigt: Ziele & Motivationen {label}")
        # Akquisitionsstrategie (Kaeufer) erstmals oder veraendert
        if "akquisitionsstrategieJson" in changed and entity.get("akquisitionsstrategieJson"):
            label = "ausgefüllt" if not prev_akq or prev_akq == "{}" else "angepasst"
            _add_eintrag(f"Aufgabe erledigt: Akquisitionsstrategie {label}")
        # Fragebogen abgegeben
        if "fragebogenStatus" in changed and entity.get("fragebogenStatus") == "abgegeben" and prev_fb_status != "abgegeben":
            _add_eintrag("Aufgabe erledigt: Fragebogen abgegeben")

        if verlauf_eintraege:
            try:
                verlauf = json.loads(entity.get("kommunikationJson", "[]") or "[]")
                if not isinstance(verlauf, list):
                    verlauf = []
            except Exception:
                verlauf = []
            verlauf.extend(verlauf_eintraege)
            entity["kommunikationJson"] = json.dumps(verlauf, ensure_ascii=False)

    tc.update_entity(dict(entity))
    if changed:
        log_audit(p, "update", "target", tid, {"fields": changed})
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
        "geschaeftsfuehrer": body.get("geschaeftsfuehrer", ""),
        "branche": body.get("branche", ""),
        "name": body.get("name", ""),
        "email": body.get("email", ""),
        "telefon": body.get("telefon", ""),
        # Zusaetzliche Mail/Telefon-Adressen als JSON-Arrays von Objekten
        # [{"label": "geschaeftlich", "wert": "..."}, ...]
        "weitereEmailsJson": body.get("weitereEmailsJson", ""),
        "weiterePhonesJson": body.get("weiterePhonesJson", ""),
        "website": body.get("website", ""),
        "plz": body.get("plz", ""),
        "ort": body.get("ort", ""),
        "sucht": body.get("sucht", ""),
        "bietet": body.get("bietet", ""),
        "kommentar": body.get("kommentar", ""),
        # Geschäftskennzahlen für Kandidaten-Match
        "mitarbeiter": str(body.get("mitarbeiter", "") or ""),
        "umsatzTeur": str(body.get("umsatzTeur", "") or ""),
        "ebitMarge": str(body.get("ebitMarge", "") or ""),
        "recurringPct": str(body.get("recurringPct", "") or ""),
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


@app.route(route="kontakt-delete", methods=["POST", "OPTIONS"])
def kontakt_delete(req: func.HttpRequest) -> func.HttpResponse:
    """Loescht einen Kontakt aus dem CRM. Admin-only."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    rk = (body.get("id") or body.get("RowKey") or "").strip()
    if not rk:
        return err_("id erforderlich", 400)
    try:
        table_("kontakte").delete_entity("kontakt", rk)
    except Exception as ex:
        return err_(f"Loeschen fehlgeschlagen: {ex}", 500)
    log_audit(p, "delete", "kontakt", rk)
    return ok_({"deleted": rk})


@app.route(route="kontakte", methods=["GET", "OPTIONS"])
def kontakte_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") not in ("admin", "ai-agent"):
        return err_("Nicht autorisiert", 401)
    items = [dict(i) for i in table_("kontakte").list_entities()]
    return ok_(items)


@app.route(route="kontakte-fuer-kaeufer", methods=["POST", "OPTIONS"])
def kontakte_fuer_kaeufer(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert NUR die Kontakte, die mibeca fuer den aufrufenden Kaeufer freigegeben hat.
    IDOR-sicher: der Kaeufer kann nur seine eigene Mandate-ID anfragen."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    tid = body.get("id", "")
    if not tid:
        return err_("id erforderlich", 400)
    if p.get("role") != "admin" and p.get("targetId") != tid:
        return err_("Nicht autorisiert", 403)
    try:
        entity = table_("targets").get_entity("target", tid)
    except Exception:
        return err_("Target nicht gefunden", 404)
    try:
        ids = json.loads(entity.get("fuerKaeuferIdsJson") or "[]")
    except Exception:
        ids = []
    if not isinstance(ids, list) or not ids:
        return ok_([])
    id_set = {str(i) for i in ids if not str(i).startswith("target-")}
    if not id_set:
        return ok_([])
    out = []
    for k in table_("kontakte").list_entities():
        if k.get("RowKey") in id_set:
            out.append(dict(k))
    return ok_(out)


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
    existing = list(tc.query_entities("email eq @email", parameters={"email": email}))
    if existing:
        return err_("E-Mail bereits registriert", 409)
    role = body.get("role", "target")
    # Interne Mitarbeiter (Admin / mibeca-Domain) loggen sich ueber Microsoft Entra ID ein
    # -> kein Passwort generieren, andere Begruessungsmail.
    is_internal = (role == "admin") or email.endswith("@mike-bergmann.de") or email.endswith("@mibeca.de")
    import string
    pw = None
    pw_hash = ""
    if not is_internal:
        pw = body.get("password") or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        pw_hash = hash_password(pw)
    uid = str(uuid.uuid4())
    entity = {
        "PartitionKey": "user", "RowKey": uid, "email": email,
        "passwordHash": pw_hash,
        "role": role,
        "name": body.get("name", ""),
        "targetId": body.get("targetId", ""),
        "createdAt": datetime.utcnow().isoformat(),
    }
    tc.create_entity(entity)

    # Begruessungsmail an neuen User
    acs_conn = os.environ.get("ACS_CONNECTION_STRING", "")
    acs_sender = os.environ.get("ACS_SENDER_ADDRESS", "DoNotReply@mail.itukv.de")
    frontend = os.environ.get("FRONTEND_BASE_URL", "https://dashboard.itukv.de")
    if acs_conn:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(acs_conn)
            if is_internal:
                # Interner Mitarbeiter -> Microsoft-Login Mail (ohne Passwort)
                html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                    <h2 style="color:#0088ba">Willkommen im ITUKV Dashboard</h2>
                    <p>Hallo {entity.get('name') or ''},</p>
                    <p>für dich wurde ein Zugang zum ITUKV Dashboard angelegt.</p>
                    <p>Du meldest dich einfach mit deinem <strong>Microsoft-Konto</strong> ({email}) an – du brauchst <strong>kein zusätzliches Passwort</strong>.</p>
                    <p style="margin-top:24px"><a href="{frontend}" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Mit Microsoft anmelden</a></p>
                    <p style="font-size:12px;color:#666;margin-top:24px">Bei Fragen melde dich bei deinem mibeca-Ansprechpartner.</p>
                    </body></html>"""
                subject = "Dein Zugang zum ITUKV Dashboard"
                plain = f"Login mit deinem Microsoft-Konto ({email}) unter: {frontend}"
            else:
                # Externer Kunde -> Passwort-Login Mail
                html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                    <h2 style="color:#0088ba">Willkommen im ITUKV Dashboard</h2>
                    <p>Hallo {entity.get('name') or ''},</p>
                    <p>für dich wurde ein Zugang zum ITUKV Dashboard angelegt.</p>
                    <p><strong>Deine Login-Daten:</strong></p>
                    <table cellpadding="6" style="background:#f0fdfa;border-radius:8px;border-collapse:separate">
                      <tr><td>E-Mail:</td><td><strong>{email}</strong></td></tr>
                      <tr><td>Initial-Passwort:</td><td><strong style="font-family:monospace;font-size:15px">{pw}</strong></td></tr>
                    </table>
                    <p style="margin-top:24px"><a href="{frontend}" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Jetzt einloggen</a></p>
                    <p style="font-size:12px;color:#666">Aus Sicherheitsgründen empfehlen wir, das Passwort nach der ersten Anmeldung zu aendern.</p>
                    <p>Bei Fragen melde dich bei deinem mibeca-Ansprechpartner.</p>
                    </body></html>"""
                subject = "Dein Zugang zum ITUKV Dashboard"
                plain = f"Login: {email} / Passwort: {pw} / URL: {frontend}"
            client.begin_send({
                "senderAddress": acs_sender,
                "recipients": {"to": [{"address": email}]},
                "content": {"subject": subject, "plainText": plain, "html": html},
            })
        except Exception as ex:
            logging.warning(f"Begruessungsmail fehlgeschlagen: {ex}") if 'logging' in dir() else None

    log_audit(p, "create", "user", uid, {"email": email, "role": entity["role"], "name": entity["name"], "loginMethod": "microsoft" if is_internal else "password"})
    return ok_({"id": uid, "email": email, "role": entity["role"], "name": entity["name"], "initialPassword": pw, "loginMethod": "microsoft" if is_internal else "password"}, 201)


@app.route(route="login", methods=["POST", "OPTIONS"])
def login_password(req: func.HttpRequest) -> func.HttpResponse:
    """Login mit E-Mail + Passwort (für Kunden ohne Microsoft-Konto)."""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    email = (body.get("email") or "").lower().strip()
    pw = body.get("password") or ""
    if not (email and pw):
        return err_("E-Mail und Passwort erforderlich", 400)
    tc = table_("users")
    users = list(tc.query_entities("email eq @email", parameters={"email": email}))
    if not users:
        return err_("Login fehlgeschlagen", 401)
    u = dict(users[0])
    stored = u.get("passwordHash", "") or ""
    if not stored.startswith("pbkdf2$"):
        return err_("Kein Passwort-Login für diese E-Mail. Bitte über Microsoft anmelden.", 401)
    if not verify_password(pw, stored):
        return err_("Login fehlgeschlagen", 401)
    # Opportunistisches Hash-Upgrade: alte Legacy-Hashes (100k) auf aktuellen Standard ziehen.
    if not stored.startswith(f"pbkdf2${PBKDF2_ITER}$"):
        try:
            u["passwordHash"] = hash_password(pw)
            tc.update_entity(dict(u))
        except Exception:
            pass
    token = make_jwt(u["RowKey"], u.get("role", "target"), u.get("name", ""), email, u.get("targetId", ""))
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
        log_audit(p, "delete", "user", uid)
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
    entity["passwordHash"] = hash_password(pw)
    tc.update_entity(dict(entity))

    mail_sent = False
    if send_mail and ACS_CONN and entity.get("email"):
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                <h2 style="color:#0088ba">Neues Passwort für das ITUKV Dashboard</h2>
                <p>Hallo {entity.get('name') or ''},</p>
                <p>dein Passwort für das ITUKV Dashboard wurde zurückgesetzt.</p>
                <p><strong>Deine neuen Login-Daten:</strong></p>
                <table cellpadding="6" style="background:#f0fdfa;border-radius:8px;border-collapse:separate">
                  <tr><td>E-Mail:</td><td><strong>{entity.get('email')}</strong></td></tr>
                  <tr><td>Neues Passwort:</td><td><strong style="font-family:monospace;font-size:15px">{pw}</strong></td></tr>
                </table>
                <p style="margin-top:24px"><a href="{FRONTEND_BASE}" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Jetzt einloggen</a></p>
                <p style="font-size:12px;color:#666">Aus Sicherheitsgründen empfehlen wir, dass du das Passwort nach der ersten Anmeldung aenderst.</p>
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
    """Self-Service Passwort-Reset: Nutzer gibt E-Mail ein, bekommt einen
    Reset-LINK (kein neues Passwort) per Mail. Erst nach Klick + neues
    Passwort eingeben wird das Passwort wirklich gesetzt.

    Aus Sicherheitsgründen geben wir IMMER 200 zurück, egal ob die
    E-Mail existiert (verhindert User-Enumeration).

    Rate-Limit: max 3 aktive Tokens pro User. Aeltere werden ignoriert."""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    email = (body.get("email") or "").lower().strip()
    if not email:
        return err_("E-Mail erforderlich", 400)
    try:
        users = list(table_("users").query_entities("email eq @email", parameters={"email": email}))
    except Exception:
        users = []
    if users:
        u = dict(users[0])
        token = secrets.token_urlsafe(32)
        now_iso = datetime.utcnow().isoformat()
        exp = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        try:
            resets = table_("passwordresets")
            # Rate-Limit: aktuelle aktive Tokens pro User zaehlen
            active = list(resets.query_entities(
                "userId eq @uid and exp gt @now",
                parameters={"uid": u["RowKey"], "now": now_iso},
            ))
            if len(active) >= 3:
                return ok_({"ok": True})  # silent stop - kein Hinweis fuer Angreifer
            resets.create_entity({
                "PartitionKey": "reset", "RowKey": token,
                "userId": u["RowKey"], "email": u.get("email", ""),
                "createdAt": now_iso, "exp": exp,
            })
        except Exception:
            return ok_({"ok": True})
        if ACS_CONN:
            try:
                from azure.communication.email import EmailClient
                client = EmailClient.from_connection_string(ACS_CONN)
                link = f"{FRONTEND_BASE.rstrip('/')}/reset?token={token}"
                html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
                    <h2 style="color:#0088ba">Passwort zurücksetzen</h2>
                    <p>Hallo {u.get('name') or ''},</p>
                    <p>du (oder jemand mit deiner E-Mail) hat einen Passwort-Reset für das ITUKV Dashboard angefordert.</p>
                    <p>Klicke auf den Button, um ein neues Passwort zu setzen. Der Link ist <strong>30 Minuten gültig</strong> und nur einmal verwendbar.</p>
                    <p style="margin:24px 0"><a href="{link}" style="background:#0088ba;color:white;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600">Neues Passwort setzen</a></p>
                    <p style="font-size:12px;color:#666">Wenn der Button nicht funktioniert, kopiere diesen Link in den Browser:<br/><span style="font-family:monospace;font-size:11px;word-break:break-all">{link}</span></p>
                    <p style="font-size:12px;color:#666;margin-top:24px">Falls du dies nicht angefordert hast, kannst du diese Mail ignorieren - dein Passwort bleibt unveraendert.</p>
                    </body></html>"""
                client.begin_send({
                    "senderAddress": ACS_SENDER,
                    "recipients": {"to": [{"address": u["email"]}]},
                    "content": {
                        "subject": "Passwort zurücksetzen – ITUKV Dashboard",
                        "plainText": f"Passwort zuruecksetzen (30 Min gueltig): {link}",
                        "html": html,
                    },
                })
            except Exception:
                pass
    return ok_({"ok": True})


@app.route(route="password-reset-confirm", methods=["POST", "OPTIONS"])
def password_reset_confirm(req: func.HttpRequest) -> func.HttpResponse:
    """Setzt das Passwort nach Klick auf den Reset-Link.
    Erwartet: { token: str, password: str (>= 8 Zeichen) }
    Token-Tabelle: passwordresets, PK='reset', RK=token, Felder userId/exp."""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    token = (body.get("token") or "").strip()
    pw = body.get("password") or ""
    if not token or len(token) < 20:
        return err_("Ungueltiger Token", 400)
    if len(pw) < 8:
        return err_("Passwort muss mindestens 8 Zeichen lang sein", 400)
    try:
        resets = table_("passwordresets")
        rec = resets.get_entity("reset", token)
    except Exception:
        return err_("Token ungueltig oder bereits verbraucht", 400)
    exp = rec.get("exp", "")
    try:
        if datetime.fromisoformat(exp) < datetime.utcnow():
            try: resets.delete_entity("reset", token)
            except Exception: pass
            return err_("Token abgelaufen - bitte neu anfordern", 400)
    except Exception:
        return err_("Token ungueltig", 400)
    uid = rec.get("userId", "")
    if not uid:
        return err_("Token ungueltig", 400)
    try:
        users = table_("users")
        u = users.get_entity("user", uid)
        u["passwordHash"] = hash_password(pw)
        users.update_entity(dict(u))
    except Exception:
        return err_("Reset fehlgeschlagen", 500)
    # Token verbrauchen
    try: resets.delete_entity("reset", token)
    except Exception: pass
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
    if not p or p.get("role") != "admin":
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
                "geschaeftsfuehrer": k.get("geschaeftsfuehrer",""),
                "branche": k.get("branche",""),
                "email": k.get("email",""),
                "telefon": k.get("telefon",""),
                "website": k.get("website",""),
                "plz": k.get("plz",""),
                "ort": k.get("ort",""),
                "typ": k.get("typ","") or k.get("kundenstatus",""),
                "kundenstatus": k.get("kundenstatus",""),
                "istKunde": bool(k.get("istKunde", False)),
                "istExKunde": bool(k.get("istExKunde", False)),
                "istInvestor": bool(k.get("istInvestor", False)),
                "istTarget": bool(k.get("istTarget", False)),
                "istNichtkunde": bool(k.get("istNichtkunde", False)),
                "mitarbeiter": k.get("mitarbeiter",""),
                "umsatzTeur": k.get("umsatzTeur",""),
                "sucht": k.get("sucht",""),
                "bietet": k.get("bietet",""),
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


@app.route(route="ausschreibung-versand", methods=["POST", "OPTIONS"])
def ausschreibung_versand(req: func.HttpRequest) -> func.HttpResponse:
    """Versendet die Ausschreibung als Massen-Mail via ACS — chunk-faehig.
    Body: {
      targetId: str,
      betreff: str (Template),
      text: str (Template),
      recipients: [{ email, firma?, name?, ort? }],
      testEmail: str (optional) — wenn gesetzt: nur 1 Mail an diese Adresse
      skipExisting: bool (optional, default true) — Empfaenger, die fuer dieses
        Mandat schon einen Verlauf-Eintrag haben, werden ausgelassen (Dedup)
      writeMandantInfo: bool (optional, default false) — nur beim ersten Chunk
        senden, sonst kommen mehrere Mandant-Info-Mails
    }
    Antwort: { sent, failed, skipped, errors[] }"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    tid = (body.get("targetId") or "").strip()
    betreff_tpl = body.get("betreff", "") or ""
    text_tpl = body.get("text", "") or ""
    recipients = body.get("recipients") or []
    test_email = (body.get("testEmail") or "").strip()
    if not (tid and betreff_tpl and text_tpl):
        return err_("targetId, betreff und text erforderlich", 400)
    if not ACS_CONN:
        return err_("ACS nicht konfiguriert (ACS_CONNECTION_STRING fehlt)", 500)
    try:
        t = dict(table_("targets").get_entity("target", tid))
    except Exception:
        return err_("Target nicht gefunden", 404)
    mb_nr = t.get("mbNr", "")
    expose_url = f"{LANDING_BASE}/{mb_nr.lower()}" if mb_nr else ""

    def render(tpl, k):
        vorname = _first_name(k.get("name", ""))
        return (tpl or "").replace("{firma}", k.get("firma", "") or "") \
                          .replace("{vorname}", vorname) \
                          .replace("{name}", k.get("name", "") or "") \
                          .replace("{ort}", k.get("ort", "") or "") \
                          .replace("{mbNr}", mb_nr) \
                          .replace("{exposeUrl}", expose_url)

    def text_to_html(txt):
        # einfacher Text->HTML mit Absatz- und Zeilenumbruchen, Links automatisch klickbar
        import html as _html, re as _re
        safe = _html.escape(txt or "")
        safe = _re.sub(r"(https?://[\w./?=&%#\-:+,;@!~$'()*]+)", r'<a href="\1" style="color:#0088ba">\1</a>', safe)
        # Doppelte Newlines = Absatz
        paragraphs = [p.replace("\n", "<br>") for p in safe.split("\n\n")]
        return "".join(f"<p>{p}</p>" for p in paragraphs)

    skip_existing = bool(body.get("skipExisting", True))
    write_mandant_info = bool(body.get("writeMandantInfo", False))
    filter_beschreibung = (body.get("filterBeschreibung") or "alle Kontakte").strip()

    from azure.communication.email import EmailClient
    client = EmailClient.from_connection_string(ACS_CONN)
    sent = 0; failed = 0; skipped = 0; errors = []

    targets_list = []
    if test_email:
        demo = (recipients[0] if recipients else {}) or {"firma": "Test-Firma", "name": "Test-Name", "ort": "Test-Ort"}
        demo = {**demo, "email": test_email}
        targets_list = [demo]
    else:
        targets_list = [r for r in recipients if (r.get("email") or "").strip()]

    if not targets_list:
        return err_("Keine Empfaenger angegeben", 400)

    # === Pre-Load: alle Kontakte einmal als Dict laden (vermeidet O(N*M) Full-Scan pro Empfaenger) ===
    kontakte_by_email = {}
    if not test_email:
        try:
            for k in table_("kontakte").list_entities():
                em = (k.get("email", "") or "").strip().lower()
                if em: kontakte_by_email[em] = dict(k)
        except Exception as ex:
            logging.warning(f"Kontakte-Vorladung fehlgeschlagen: {ex}")

    autor = p.get("name") or p.get("email", "")
    tc = table_("kontakte")

    def already_sent_to(email_lc):
        """Prueft ob der Kontakt schon einen mail_out-Eintrag fuer dieses Mandat hat."""
        k = kontakte_by_email.get(email_lc)
        if not k: return False
        try: v = json.loads(k.get("verlaufJson") or "[]")
        except: return False
        if not isinstance(v, list): return False
        for ev in v:
            if (ev.get("kontextMbNr", "") or "").lower() == mb_nr.lower() and ev.get("typ") == "mail_out":
                return True
        return False

    for r in targets_list:
        rec_email = (r.get("email") or "").strip().lower()
        # Skip-Logik (nur im echten Versand, nicht beim Test)
        if not test_email and skip_existing and rec_email and already_sent_to(rec_email):
            skipped += 1
            continue
        try:
            subj = render(betreff_tpl, r)
            html_body = (
                '<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6;max-width:600px">'
                + text_to_html(render(text_tpl, r))
                + '</body></html>'
            )
            # Pro Empfaenger eindeutigen Reply-Token erzeugen → Antworten landen via
            # SendGrid Inbound Parse automatisch im richtigen Verlauf.
            msg = {
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": r["email"]}]},
                "content": {"subject": subj, "plainText": render(text_tpl, r), "html": html_body},
            }
            try:
                token = secrets.token_urlsafe(12)
                _replytokens_table().create_entity({
                    "PartitionKey": "token", "RowKey": token,
                    "targetId": tid,
                    "kontaktEmail": (r.get("email") or "").lower(),
                    "originalSender": p.get("email", ""),
                    "createdAt": datetime.utcnow().isoformat(),
                })
                reply_domain = os.environ.get("REPLY_DOMAIN", "reply.itukv.de")
                msg["replyTo"] = [{"address": f"verlauf+{token}@{reply_domain}", "displayName": "Jennifer Kaplan"}]
            except Exception as ex:
                logging.warning(f"Reply-Token erzeugen fehlgeschlagen: {ex}")
                # Fallback: globalen Reply-To verwenden
                rt = acs_reply_to()
                if rt: msg["replyTo"] = rt
            client.begin_send(msg)
            sent += 1
            # SOFORT pro Empfaenger den Kontakt-Verlauf-Eintrag schreiben.
            # So weiss man bei Abbruch genau, wer schon eine Mail bekommen hat.
            if not test_email and rec_email and rec_email in kontakte_by_email:
                kontakt = kontakte_by_email[rec_email]
                try: kverlauf = json.loads(kontakt.get("verlaufJson") or "[]")
                except: kverlauf = []
                if not isinstance(kverlauf, list): kverlauf = []
                kverlauf.append({
                    "id": "kv" + str(int(datetime.utcnow().timestamp() * 1000)) + secrets.token_hex(2),
                    "typ": "mail_out",
                    "datum": datetime.utcnow().isoformat(),
                    "autor": autor,
                    "betreff": subj,
                    "beschreibung": render(text_tpl, r),
                    "kontextTargetId": tid,
                    "kontextMbNr": mb_nr,
                })
                kontakt["verlaufJson"] = json.dumps(kverlauf, ensure_ascii=False)
                try: tc.update_entity(kontakt)
                except Exception as ex: logging.warning(f"Kontakt-Verlauf-Write {rec_email}: {ex}")
        except Exception as ex:
            failed += 1
            errors.append({"email": r.get("email", ""), "error": str(ex)})

    # Mandant-Info-Mail + Target-Verlauf nur beim ersten Chunk schreiben (writeMandantInfo=true)
    if not test_email and write_mandant_info:
        now_iso = datetime.utcnow().isoformat()
        mandant_email = (t.get("privatEmail") or "").strip()
        if mandant_email:
            try:
                mandant_vorname = _first_name(t.get("vorname") or t.get("verkaueferName") or "")
                info_html = (
                    '<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">'
                    f'<h2 style="color:#0088ba">Kampagne gestartet — Projekt {mb_nr}</h2>'
                    f'<p>Hallo {mandant_vorname or "zusammen"},</p>'
                    f'<p>kurze Info zu Deinem Projekt <strong>{mb_nr}</strong>: Wir haben soeben die Marktansprache gestartet.</p>'
                    f'<p>Die Ausschreibung läuft an potenzielle Interessenten, die sich über die Landing-Page für das Exposé eintragen können.</p>'
                    f'<p>Sobald die ersten Rückmeldungen kommen, melden wir uns mit den nächsten Schritten.</p>'
                    f'<p>Viele Grüße<br/>Dein M&amp;A-Team der Mike Bergmann Akademie</p>'
                    '</body></html>'
                )
                _acs_dispatch(client, {
                    "senderAddress": ACS_SENDER,
                    "recipients": {"to": [{"address": mandant_email}]},
                    "content": {
                        "subject": f"Kampagne gestartet — Projekt {mb_nr}",
                        "plainText": f"Hallo {mandant_vorname},\n\nKampagne fuer Projekt {mb_nr} ist gestartet.\n\nViele Gruesse\nDein M&A-Team der Mike Bergmann Akademie",
                        "html": info_html,
                    },
                })
            except Exception as ex:
                logging.warning(f"Mandant-Info-Mail fehlgeschlagen: {ex}")
        _verlauf_append(tid, {
            "id": "k" + str(int(datetime.utcnow().timestamp() * 1000)),
            "typ": "mail_out",
            "datum": now_iso,
            "autor": autor,
            "betreff": f"Ausschreibung versendet — Verteiler: {filter_beschreibung}",
            "beschreibung": f'Marktansprache gestartet. Verteiler: {filter_beschreibung}. Betreff der Ausschreibung: „{betreff_tpl[:120]}".',
        })
        # Phase-Auto-Advance: Mandat in der Verkaufs-Pipeline auf "Marktansprache" rutschen.
        # Wir markieren alle Aufgaben in Phase 1+2 als erledigt + den „Anschreiben"-Task in Phase 3.
        try:
            t_fresh = dict(table_("targets").get_entity("target", tid))
            phasen = json.loads(t_fresh.get("phasenJson") or "[]")
            if isinstance(phasen, list) and phasen:
                dirty = False
                for ph in phasen:
                    pid = ph.get("id", 0)
                    if pid <= 2:
                        for a in (ph.get("aufgaben") or []):
                            if not a.get("done"):
                                a["done"] = True; a["datum"] = a.get("datum") or now_iso
                                dirty = True
                    elif pid == 3:
                        for a in (ph.get("aufgaben") or []):
                            if a.get("auto") in ("anschreibenVerschickt", "interessentenAngelegt", "landingPublished"):
                                if not a.get("done"):
                                    a["done"] = True; a["datum"] = a.get("datum") or now_iso
                                    dirty = True
                if dirty:
                    t_fresh["phasenJson"] = json.dumps(phasen, ensure_ascii=False)
                    table_("targets").update_entity(t_fresh)
        except Exception as ex:
            logging.warning(f"Phase-Auto-Advance fehlgeschlagen: {ex}")

    return ok_({"sent": sent, "failed": failed, "skipped": skipped, "errors": errors[:10]})


@app.route(route="kontakt-verlauf-add", methods=["POST", "OPTIONS"])
def kontakt_verlauf_add(req: func.HttpRequest) -> func.HttpResponse:
    """Fuegt einem Kontakt (per E-Mail identifiziert) einen Verlauf-Eintrag hinzu.
    Body: { email, eintrag: { typ, betreff, beschreibung, datum? } }
    Admin-only."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    email = (body.get("email") or "").strip().lower()
    eintrag = body.get("eintrag") or {}
    if not (email and (eintrag.get("betreff") or eintrag.get("beschreibung"))):
        return err_("email und eintrag mit betreff/beschreibung erforderlich", 400)
    tc = table_("kontakte")
    kontakt = None
    for k in tc.list_entities():
        if (k.get("email", "") or "").strip().lower() == email:
            kontakt = dict(k); break
    if not kontakt:
        return err_("Kontakt nicht gefunden", 404)
    try: kverlauf = json.loads(kontakt.get("verlaufJson") or "[]")
    except: kverlauf = []
    if not isinstance(kverlauf, list): kverlauf = []
    neu = {
        "id": "kv" + str(int(datetime.utcnow().timestamp() * 1000)) + secrets.token_hex(2),
        "typ": eintrag.get("typ") or "notiz",
        "datum": eintrag.get("datum") or datetime.utcnow().isoformat(),
        "autor": p.get("name") or p.get("email", ""),
        "betreff": eintrag.get("betreff", ""),
        "beschreibung": eintrag.get("beschreibung", ""),
        "manuell": True,
    }
    kverlauf.append(neu)
    kontakt["verlaufJson"] = json.dumps(kverlauf, ensure_ascii=False)
    tc.update_entity(kontakt)
    return ok_({"entry": neu})




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
# BACKFILL — Verlauf-Eintraege fuer historische Landing-Page-Eintragungen
# =========================================================================

@app.route(route="backfill-kontakt-verlauf", methods=["POST", "OPTIONS"])
def backfill_kontakt_verlauf(req: func.HttpRequest) -> func.HttpResponse:
    """Einmaliger Backfill: fuer jede historische Interessenten-Anmeldung
    werden zwei Verlauf-Eintraege im passenden Kontakt erzeugt, falls sie
    noch nicht existieren:
      1) mail_out  — „Ausschreibung mb-XXX erhalten"  (zeit: Interessent.createdAt - 1h)
      2) wichtig   — „Ueber Landing-Page eingetragen" (zeit: Interessent.createdAt)
    Body: optional { dryRun: bool }
    """
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    dry = bool(body.get("dryRun"))

    tc = table_("kontakte")
    kt = table_("targets")
    it = table_("interessenten")

    # mb-Nr je targetId vorab laden
    mb_by_tid = {}
    for t in kt.list_entities():
        mb_by_tid[t.get("RowKey", "")] = (t.get("mbNr", "") or "")

    # Pro E-Mail koennen MEHRERE kontakte existieren (Duplikate). Wir wollen
    # ALLE Treffer aktualisieren, damit die Verlauf-Eintraege ueberall sichtbar sind.
    kontakte_by_email = {}
    for k in tc.list_entities():
        em = (k.get("email", "") or "").strip().lower()
        if em:
            kontakte_by_email.setdefault(em, []).append(dict(k))

    created_mail_out = 0
    created_wichtig = 0
    skipped = 0
    touched_kontakte = set()
    debug_log = []

    for inter in it.list_entities():
        em = (inter.get("email", "") or "").strip().lower()
        if not em: continue
        matches = kontakte_by_email.get(em, [])
        if not matches:
            skipped += 1
            debug_log.append(f"NO_KONTAKT_FOR {em}")
            continue
        mb_nr = mb_by_tid.get(inter.get("targetId", ""), "")
        if not mb_nr:
            skipped += 1
            debug_log.append(f"NO_MBNR_FOR_INTERESSENT {em} tid={inter.get('targetId','')}")
            continue

        created_at = inter.get("createdAt") or datetime.utcnow().isoformat()
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", ""))
            mail_dt = (dt - timedelta(hours=1)).isoformat()
        except Exception:
            mail_dt = created_at

        for kontakt in matches:
            try: kverlauf = json.loads(kontakt.get("verlaufJson") or "[]")
            except: kverlauf = []
            if not isinstance(kverlauf, list): kverlauf = []

            has_mail_out = any(
                (e.get("kontextMbNr", "") or "").lower() == mb_nr.lower() and e.get("typ") == "mail_out"
                for e in kverlauf
            )
            has_wichtig = any(
                (e.get("kontextMbNr", "") or "").lower() == mb_nr.lower() and e.get("typ") == "wichtig"
                for e in kverlauf
            )

            changed = False
            if not has_mail_out:
                kverlauf.append({
                    "id": "kv" + str(int(datetime.utcnow().timestamp() * 1000)) + secrets.token_hex(2),
                    "typ": "mail_out",
                    "datum": mail_dt,
                    "autor": "Versand (nachgetragen)",
                    "betreff": f"Ausschreibung {mb_nr} versendet",
                    "beschreibung": f"Ausschreibung zum Projekt {mb_nr} wurde an diesen Kontakt versendet (nachgetragen via Backfill).",
                    "kontextMbNr": mb_nr,
                    "kontextTargetId": inter.get("targetId", ""),
                })
                created_mail_out += 1
                changed = True
            if not has_wichtig:
                kverlauf.append({
                    "id": "kv" + str(int(datetime.utcnow().timestamp() * 1000)) + secrets.token_hex(2),
                    "typ": "wichtig",
                    "datum": created_at,
                    "autor": "Landing-Page",
                    "betreff": f"Eintragung über Landing-Page {mb_nr}",
                    "beschreibung": f"Kontakt hat sich über die Landing-Page zur Ausschreibung {mb_nr} eingetragen und ein Exposé angefordert.",
                    "kontextMbNr": mb_nr,
                    "kontextTargetId": inter.get("targetId", ""),
                })
                created_wichtig += 1
                changed = True
            if changed and not dry:
                kontakt["verlaufJson"] = json.dumps(kverlauf, ensure_ascii=False)
                try:
                    tc.update_entity(kontakt)
                    touched_kontakte.add(kontakt.get("RowKey", ""))
                    debug_log.append(f"OK {em} rk={kontakt.get('RowKey','')[:8]} mb={mb_nr}")
                except Exception as ex:
                    logging.warning(f"Backfill update fehlgeschlagen {em}: {ex}")
                    debug_log.append(f"UPDATE_FAIL {em}: {ex}")

    return ok_({
        "dryRun": dry,
        "createdMailOut": created_mail_out,
        "createdWichtig": created_wichtig,
        "skipped": skipped,
        "touchedKontakte": len(touched_kontakte),
        "debug": debug_log[:30],
    })


@app.route(route="versand-preview", methods=["POST", "OPTIONS"])
def versand_preview(req: func.HttpRequest) -> func.HttpResponse:
    """Prueft VOR dem Versand, wie viele der Empfaenger die Ausschreibung
    fuer dieses Mandat bereits bekommen haben (basierend auf mail_out-
    Eintraegen im Kontakt mit passender kontextMbNr).
    Body: { targetId, recipients: [{email}, ...] }
    Antwort: { total, alreadySent, neu, alreadySentEmails[max 50] }"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    tid = (body.get("targetId") or "").strip()
    recipients = body.get("recipients") or []
    if not (tid and recipients):
        return err_("targetId und recipients erforderlich", 400)
    try:
        t = dict(table_("targets").get_entity("target", tid))
    except Exception:
        return err_("Target nicht gefunden", 404)
    mb_nr = (t.get("mbNr", "") or "").lower()

    # Alle Kontakte laden und prüfen, ob sie eine mail_out-Spur für diese mb-Nr haben
    already = set()
    for k in table_("kontakte").list_entities():
        em = (k.get("email", "") or "").strip().lower()
        if not em: continue
        try: v = json.loads(k.get("verlaufJson") or "[]")
        except: continue
        if not isinstance(v, list): continue
        for ev in v:
            if ev.get("typ") == "mail_out" and (ev.get("kontextMbNr", "") or "").lower() == mb_nr:
                already.add(em)
                break

    rec_emails = [(r.get("email") or "").strip().lower() for r in recipients]
    rec_emails = [e for e in rec_emails if e]
    duplicates = sorted({e for e in rec_emails if e in already})
    total = len(rec_emails)
    n_dup = len(duplicates)
    return ok_({
        "total": total,
        "alreadySent": n_dup,
        "neu": total - n_dup,
        "alreadySentEmails": duplicates[:50],
        "mbNr": t.get("mbNr", ""),
    })


@app.route(route="interessenten-fuer-kontakt", methods=["POST", "OPTIONS"])
def interessenten_fuer_kontakt(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert fuer eine E-Mail (oder Firma) ALLE passenden Interessenten-
    Eintraege ueber alle Mandate hinweg — inkl. deren Verlauf-Eintraegen.
    Wird in der CRM-Akte als zusaetzliche Verlauf-Quelle gemerged.
    Body: { email?: str, firma?: str }"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    email = (body.get("email") or "").strip().lower()
    firma = (body.get("firma") or "").strip().lower()
    if not email and not firma:
        return ok_({"interessenten": []})

    mb_by_tid = {}
    firma_by_tid = {}
    for t in table_("targets").list_entities():
        mb_by_tid[t.get("RowKey", "")] = t.get("mbNr", "") or ""
        firma_by_tid[t.get("RowKey", "")] = t.get("firma", "") or t.get("verkaueferName", "") or ""

    out = []
    for inter in table_("interessenten").list_entities():
        em = (inter.get("email", "") or "").strip().lower()
        fi = (inter.get("firma", "") or "").strip().lower()
        if email and em != email and not (firma and fi == firma):
            continue
        if not email and firma and fi != firma:
            continue
        tid = inter.get("targetId", "")
        # Eigene Verlauf-Eintraege des Interessenten parsen
        try: vlog = json.loads(inter.get("verlaufJson") or "[]")
        except: vlog = []
        if not isinstance(vlog, list): vlog = []
        out.append({
            "id": inter.get("RowKey", ""),
            "mbNr": mb_by_tid.get(tid, ""),
            "targetId": tid,
            "mandantFirma": firma_by_tid.get(tid, ""),
            "firma": inter.get("firma", "") or "",
            "name": inter.get("name", "") or "",
            "email": inter.get("email", "") or "",
            "createdAt": inter.get("createdAt", "") or "",
            "ndaStatus": inter.get("ndaStatus", "") or "",
            "rating": inter.get("rating", 0) or 0,
            "veto": bool(inter.get("veto", False)),
            "verlauf": vlog,
        })
    return ok_({"interessenten": out})


@app.route(route="versand-stats", methods=["POST", "OPTIONS"])
def versand_stats(req: func.HttpRequest) -> func.HttpResponse:
    """Recherche: zaehlt fuer ein Mandat, an wie viele Kontakte tatsaechlich
    die Ausschreibung versendet wurde — basierend auf den mail_out-Eintraegen
    in kontakte.verlaufJson mit passender kontextMbNr.
    Body: { mbNr: 'mb-250' }
    Antwort: { mbNr, total, kontakte: [{firma, email, datum}] (max 20 als Preview) }
    """
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    mb_nr = (body.get("mbNr") or "").strip().lower()
    if not mb_nr:
        return err_("mbNr erforderlich", 400)
    tc = table_("kontakte")
    total = 0
    preview = []
    first_datum = None
    last_datum = None
    for k in tc.list_entities():
        try: v = json.loads(k.get("verlaufJson") or "[]")
        except: continue
        if not isinstance(v, list): continue
        for ev in v:
            if ev.get("typ") == "mail_out" and (ev.get("kontextMbNr", "") or "").lower() == mb_nr:
                total += 1
                d = ev.get("datum", "") or ""
                if not first_datum or d < first_datum: first_datum = d
                if not last_datum or d > last_datum: last_datum = d
                if len(preview) < 20:
                    preview.append({
                        "firma": k.get("firma", "") or "",
                        "email": k.get("email", "") or "",
                        "datum": d,
                    })
                break  # nur 1x pro Kontakt zaehlen
    return ok_({
        "mbNr": mb_nr,
        "total": total,
        "ersterVersand": first_datum,
        "letzterVersand": last_datum,
        "preview": preview,
    })


# =========================================================================
# INTERESSENTEN — Pro Target / Pro Ausschreibung
# =========================================================================

@app.route(route="interessenten", methods=["POST", "OPTIONS"])
def interessenten_list(req: func.HttpRequest) -> func.HttpResponse:
    """POST {targetId: "..."} → Liste der Interessenten für dieses Target."""
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
    items = [dict(i) for i in tc.query_entities("targetId eq @t", parameters={"t": target_id})]
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
ACS_REPLY_TO = os.environ.get("ACS_REPLY_TO", "")
ACS_REPLY_TO_NAME = os.environ.get("ACS_REPLY_TO_NAME", "Jennifer Kaplan")

def acs_reply_to():
    """Liefert die replyTo-Liste fuer ACS begin_send(), wenn ACS_REPLY_TO gesetzt ist."""
    if not ACS_REPLY_TO:
        return None
    return [{"address": ACS_REPLY_TO, "displayName": ACS_REPLY_TO_NAME}]

def _acs_dispatch(client, message):
    """ACS begin_send() Wrapper: setzt Reply-To automatisch, falls konfiguriert."""
    rt = acs_reply_to()
    if rt:
        message.setdefault("replyTo", rt)
    return client.begin_send(message)

def _first_name(name_or_full):
    """Extrahiert den Vornamen aus einem vollen Namen (erstes Wort).
    Verwendung: in Mail-Anreden 'Hallo Anna,' statt 'Hallo Anna Giza-Braun,'."""
    if not name_or_full:
        return ""
    return str(name_or_full).strip().split(" ")[0]
FRONTEND_BASE = os.environ.get("FRONTEND_BASE_URL", "https://dashboard.itukv.de")
LANDING_BASE = os.environ.get("LANDING_BASE_URL", "https://targets.itukv.de")
DEFAULT_BOOKINGS_URL = os.environ.get(
    "DEFAULT_BOOKINGS_URL",
    "https://outlook.office.com/owa/calendar/MikeBergmannUmsetzungscoachingfrITUnternehmer@visoma.de/bookings/s/JTBnZ631-k-f7jiaO9JDsw2?ismsaljsauthenabled",
)


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
    if not is_valid_public_token(token):
        return None
    tc = table_("vertragsignaturen")
    items = list(tc.query_entities("token eq @t", parameters={"t": token}))
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
    Vorteile: echte CSS-Typografie, page-break-inside für Signaturen,
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
        # Approximation: Helvetica-Breite ist etwa 0.55x fontsize für Durchschnitts-char
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
        # Platz für alle Zeilen reservieren – sonst Seitenumbruch
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
        "Aufbereitung der Daten für das Verkaufsobjekt",
        "Erstellung eines anonymen Kurzexposes",
        "Suche von Interessenten für das Verkaufsobjekt",
        "Unterstuetzung bei Gesprächen mit Interessenten",
        "Begleitung der Verkaufsverhandlungen",
        "Vermittlung weiterer Berater (Rechtsanwaelte, Steuerberater)",
        "Laufende Beratung und Projektbegleitung (persönlich, telefonisch, per Videokonferenz, per E-Mail)",
    ]
    for l in leistungen:
        add_para(f"  -  {l}", space_after=2)
    add_spacer(6)

    add_heading("§3 Pflichten des Auftraggebers")
    add_para("Der Auftraggeber stellt alle relevanten Unterlagen (Bilanzen, BWA, Statistiken, Kunden-, Lieferanten-, Mitarbeiterlisten) bereit und sichert deren Vollständigkeit und Richtigkeit zu. Der Berater haftet nicht für die inhaltliche Richtigkeit der gelieferten Informationen.")

    add_heading("§4 Pflichten des Beraters / Vertraulichkeit")
    add_para("Der Berater ist zum Stillschweigen gegenüber Dritten über sämtliche Inhalte des Verkaufsprozesses sowie über vertrauliche Informationen des Auftraggebers verpflichtet. Diese Verpflichtung gilt auch nach Ende des Vertrages. Unterlagen werden vertraulich aufbewahrt und nach Aufforderung zurückgegeben oder vernichtet.")

    # ============ §5 Verguetung ============
    add_heading("§5 Verguetung")
    add_para("Alle Verguetungen verstehen sich netto zzgl. 19 % Mehrwertsteuer.", space_after=8)

    add_subheading("(1) Eroeffnungsverguetung")
    if variante == 'mit_uve':
        modus = form.get('eroeffnungsModus', 'einmalig')
        if modus == 'einmalig':
            txt = f"Einmalige Eroeffnungsverguetung in Hoehe von {form.get('eroeffnungsBetrag', 10000):,.0f} EUR netto für das UVE-Coachingprogramm, Datenaufbereitung und Kurzexpose."
        else:
            txt = "Eroeffnungsverguetung: 6 Monatsraten zu je 1.800 EUR netto für das UVE-Coachingprogramm, Datenaufbereitung und Kurzexpose."
    elif variante == 'vorhandenes_uve':
        txt = "Keine Eroeffnungsverguetung - der Auftraggeber hat das UVE-Coaching bereits abgeschlossen und bezahlt (ansonsten 3.490 EUR). Der Berater übernimmt die Datenaufbereitung sowie die Erstellung des Kurzexposes."
    else:
        txt = f"Eroeffnungsverguetung: {form.get('eroeffnungsBetrag', 4950):,.0f} EUR netto für Datenaufbereitung und Erstellung des anonymen Kurzexposes."
    add_para(txt.replace(',', '.'), space_after=10)

    add_subheading("(2) Beratungsverguetung")
    add_para(f"Jennifer Kaplan: {form.get('honorarJennyStunde', 250):,.0f} EUR pro Stunde bzw. {form.get('honorarJennyTag', 2990):,.0f} EUR pro Tag vor Ort (zzgl. Reisespesen).".replace(',', '.'), space_after=4)
    add_para(f"Mike Bergmann: {form.get('honorarMikeStunde', 250):,.0f} EUR pro Stunde bzw. {form.get('honorarMikeTag', 2990):,.0f} EUR pro Tag vor Ort (zzgl. Reisespesen).".replace(',', '.'), space_after=4)
    add_para(f"Team-Mitarbeiter: {form.get('honorarTeamStunde', 150):,.0f} EUR pro Stunde bzw. {form.get('honorarTeamTag', 1500):,.0f} EUR pro Tag vor Ort (zzgl. Reisespesen).".replace(',', '.'), space_after=10)

    add_subheading("(3) Erfolgsverguetung")
    add_para(f"Erfolgsverguetung in Hoehe von {form.get('erfolgsProzent', 5)} % des Transaktionsvolumens bei erfolgreichem Vertragsabschluss zwischen Auftraggeber und einem Interessenten. Als Vertragsabschluss gilt jede Form eines Verkaufs-, Kaufs-, Beteiligungs- oder Fusionsvertrages sowie vergleichbare Aktivitaeten (z.B. Asset Deals).", space_after=8)

    add_heading("§6 Vertragsdauer und Vertragsende")
    add_para(f"Der Vertrag beginnt mit Vertragsunterzeichnung und wird zunaechst für {form.get('laufzeitMonate', 12)} Monate abgeschlossen. Die Laufzeit verlaengert sich stillschweigend um jeweils 6 Monate, sofern er nicht mit einer Frist von 2 Monaten schriftlich gekündigt wird. Die Vertragslaufzeit endet automatisch zum Monatsende, sobald der Auftraggeber das Verkaufsobjekt veraeussert hat.")

    add_heading("§7 Haftungsfreistellung")
    add_para("Der Berater agiert mit der Sorgfalt eines ordentlichen Kaufmannes. Für Schäden aus der Beratung sowie für entgangene Gewinne haftet der Berater nicht. Der Auftraggeber stellt den Berater von jeglicher Haftung frei, die auf Unvollständigkeit oder Unrichtigkeit der gelieferten Informationen beruht.")

    add_heading("§8 Schlussbestimmungen")
    add_para("Änderungen beduerfen der Schriftform. Muendliche Nebenabreden bestehen nicht. Sind einzelne Bestimmungen unwirksam, bleibt die Gueltigkeit der uebrigen unberuehrt. Es gilt deutsches Recht. Gerichtsstand ist Uelzen.")

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
    pdf_headers["Content-Disposition"] = 'inline; filename="Mandatsvertrag.pdf"'
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


def _load_mibeca_nda_signature():
    """Holt die hinterlegte mibeca-NDA-Signatur aus dem Blob. Gibt bytes oder None zurueck."""
    try:
        blob = _blob_container_lazy("vertraege").get_blob_client("mibeca-nda-signature.png")
        return blob.download_blob().readall()
    except Exception:
        return None


def _render_nda_pdf_bytes(form, variante='investor'):
    from jinja2 import Template
    from weasyprint import HTML
    html = Template(_NDA_HTML_TEMPLATE).render(form=form, variante=variante)
    pdf_bytes = HTML(string=html, base_url="/").write_pdf()
    # mibeca-Vorsignatur (Jennys handgezeichnete Unterschrift) automatisch einbetten,
    # falls hinterlegt. Damit hat das NDA bereits beim Download durch den Interessenten
    # die Berater-Signatur.
    sig = _load_mibeca_nda_signature()
    if sig:
        try:
            pdf_bytes = _embed_signature_in_pdf(
                pdf_bytes, sig, "Jennifer Kaplan", {},
                anchor_keywords=["Unterschrift Transaktionsberater", "Transaktionsberater", "Jennifer Kaplan"],
                audit_trail=False,
            )
        except Exception:
            pass
    return pdf_bytes


@app.route(route="mibeca-nda-signature", methods=["GET", "POST", "DELETE", "OPTIONS"])
def mibeca_nda_signature_route(req: func.HttpRequest) -> func.HttpResponse:
    """Hinterlegt die globale mibeca-NDA-Vorsignatur (Jennys handschriftliche Unterschrift)
    als PNG im Blob. Admin-only.
    GET    -> { exists: bool, dataUrl?: str }
    POST   -> Body { signatureDataUrl }
    DELETE -> entfernt die hinterlegte Signatur"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    cont = _blob_container_lazy("vertraege")
    if req.method == "GET":
        sig = _load_mibeca_nda_signature()
        if sig:
            return ok_({"exists": True, "dataUrl": "data:image/png;base64," + base64.b64encode(sig).decode()})
        return ok_({"exists": False})
    if req.method == "DELETE":
        try:
            cont.delete_blob("mibeca-nda-signature.png")
        except Exception:
            pass
        return ok_({"deleted": True})
    # POST
    body = req.get_json() or {}
    sig_data = body.get("signatureDataUrl", "")
    if not sig_data:
        return err_("signatureDataUrl erforderlich", 400)
    if sig_data.startswith("data:"):
        sig_data = sig_data.split(",", 1)[1]
    try:
        sig_bytes = base64.b64decode(sig_data)
    except Exception:
        return err_("Ungueltige Signatur", 400)
    try:
        cont.upload_blob("mibeca-nda-signature.png", sig_bytes, overwrite=True)
    except Exception as ex:
        return err_(f"Speichern fehlgeschlagen: {ex}", 500)
    return ok_({"saved": True})


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
    return pdf_response(pdf_bytes, "NDA.pdf")


@app.route(route="nda-zur-signatur", methods=["POST", "OPTIONS"])
def nda_zur_signatur(req: func.HttpRequest) -> func.HttpResponse:
    """NDA-Sign-Link an Investor/Käufer per Mail."""
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
                <h2 style="color:#0088ba">NDA zur Unterschrift</h2>
                <p>Hallo {form.get('vertreten','')},</p>
                <p>im Rahmen unserer Zusammenarbeit als M&A-Berater bitten wir Sie um Unterzeichnung der beiliegenden Vertraulichkeitsvereinbarung (NDA).</p>
                <p style="margin:24px 0"><a href="{sign_url}" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">NDA ansehen &amp; unterschreiben</a></p>
                <p style="font-size:12px;color:#666">Der Link ist {SIGNATURE_LINK_EXPIRY_DAYS} Tage gültig.</p>
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

    target_users = list(table_("users").query_entities("targetId eq @t", parameters={"t": target_id}))
    if not target_users:
        return err_("Kein Target-Login angelegt. Bitte zuerst Benutzer für dieses Target erstellen.", 400)
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
        old_sigs = list(tc.query_entities("targetId eq @t", parameters={"t": target_id}))
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
                <h2 style="color:#0088ba">Dein Mandatsvertrag liegt zur Unterschrift bereit</h2>
                <p>Hallo {target_name or ''},</p>
                <p>der Mandatsvertrag für dein Verkaufsprojekt ist fertig vorbereitet.
                Du kannst ihn online ansehen und mit wenigen Klicks unterschreiben.</p>
                <p style="margin:24px 0"><a href="{sign_url}" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Vertrag ansehen &amp; unterschreiben</a></p>
                <p style="font-size:12px;color:#666">Der Link ist {SIGNATURE_LINK_EXPIRY_DAYS} Tage gültig.</p>
                <p>Viele Grüße<br/>Dein mibeca-Team</p>
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
    # WICHTIG: kein 'Content-Type' aus CORS mitschicken, sonst überschreibt das mimetype
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
            <p>Dein Bestätigungscode für die Unterschrift lautet:</p>
            <p style="font-size:28px;font-weight:700;letter-spacing:6px;background:#f0fdfa;padding:14px 22px;border-radius:10px;display:inline-block;color:#0088ba">{code}</p>
            <p>Der Code ist {SIGNATURE_CODE_EXPIRY_MIN} Minuten gültig.</p>
            </body></html>"""
        client.begin_send({
            "senderAddress": ACS_SENDER,
            "recipients": {"to": [{"address": sig["lead_email"]}]},
            "content": {"subject": "Bestätigungscode Mandatsvertrag", "plainText": f"Code: {code}", "html": html},
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

    # Auch im Verträge-Ordner des Datenraums ablegen (vorlaeufig: nur Kunden-signiert)
    try:
        target_id = sig.get("targetId", "")
        variante = sig.get("variante", "vertrag")
        doc_blob_name = f"{target_id}/Verträge/Mandatsvertrag_{variante}_kunden-signiert.pdf"
        _blob_container_lazy("datenraum").upload_blob(doc_blob_name, signed_bytes, overwrite=True)
        doc_id = "vertrag-" + sig["RowKey"]
        table_("dokumente").upsert_entity({
            "PartitionKey": target_id, "RowKey": doc_id,
            "fileName": f"Mandatsvertrag_{variante}_kunden-signiert.pdf",
            "ordner": "Verträge", "blobName": doc_blob_name, "container": "datenraum",
            "size": len(signed_bytes), "contentType": "application/pdf",
            "uploadedAt": signed_at,
            "uploadedBy": sig.get("lead_email", ""),
            "quelle": "Kunden-Signatur (wartet auf Gegenzeichnung)",
        })
    except Exception as ex:
        logging.warning(f"Vertrag (Kunden-Signatur) als Datenraum-Dokument speichern fehlgeschlagen: {ex}")

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
            "betreff": "Mandatsvertrag vom Verkäufer unterschrieben",
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
                <p>Bitte öffne die Akte im Dashboard und zeichne gegen.</p></body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": mibeca_mail}]},
                "content": {"subject": f"Vertrag {sig.get('lead_name','')} – Gegenzeichnung benötigt", "plainText": "Vertrag wartet auf Gegenzeichnung im Dashboard.", "html": html},
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

    # Final unterzeichneten Vertrag auch in den Verträge-Ordner des Targets ablegen
    try:
        target_id = sig.get("targetId", "")
        variante = sig.get("variante", "vertrag")
        # Verträge-Ordner Datenraum
        doc_blob_name = f"{target_id}/Verträge/Mandatsvertrag_{variante}_{datetime.utcnow().strftime('%Y%m%d')}.pdf".replace(" ", "_")
        _blob_container_lazy("datenraum").upload_blob(doc_blob_name, final_bytes, overwrite=True)
        doc_id = "vertrag-" + sig["RowKey"]
        table_("dokumente").upsert_entity({
            "PartitionKey": target_id, "RowKey": doc_id,
            "fileName": f"Mandatsvertrag_{variante}_unterzeichnet.pdf",
            "ordner": "Verträge", "blobName": doc_blob_name, "container": "datenraum",
            "size": len(final_bytes), "contentType": "application/pdf",
            "uploadedAt": signed_at_admin,
            "uploadedBy": p.get("email", ""),
            "quelle": "Mandatsvertrag-Gegenzeichnung",
        })
    except Exception as ex:
        logging.warning(f"Vertrag als Target-Dokument speichern fehlgeschlagen: {ex}")

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
                <h2 style="color:#0088ba">Dein Mandatsvertrag ist vollständig unterschrieben</h2>
                <p>Hallo {sig.get('lead_name','')},</p>
                <p>{sig_name} hat den Vertrag für mibeca gegengezeichnet. Der Vertrag ist damit final unterzeichnet und liegt für dich zum Download bereit.</p>
                <p style="margin:24px 0"><a href="{download_url}" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Mein Exemplar herunterladen</a></p>
                <p>Du findest den Vertrag ausserdem jederzeit in deinem Dashboard unter Vertraege.</p>
                <p>Viele Grüße<br/>Dein mibeca-Team</p>
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
                tu = list(table_("users").query_entities("targetId eq @t", parameters={"t": target_id}))
                recipients = [u.get("email", "") for u in tu if u.get("email")]
        else:
            tu = list(table_("users").query_entities("targetId eq @t", parameters={"t": target_id}))
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
                <h3 style="color:#0088ba">Neuer Eintrag im ITUKV Dashboard</h3>
                <p><strong>Projekt:</strong> {mb}</p>
                <p><strong>Betreff:</strong> {betreff}</p>
                <p style="background:#f8f9fa;border-left:3px solid #0088ba;padding:12px;white-space:pre-wrap">{beschr}</p>
                <p style="margin-top:24px"><a href="{link}" style="background:#0088ba;color:white;padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:600">Im Dashboard öffnen</a></p>
                </body></html>"""
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": rcpt}]},
                "content": {"subject": f"[ITUKV] {betreff}", "plainText": f"{betreff}\n\n{beschr}\n\nDashboard: {link}", "html": html},
            })
    except Exception as ex:
        logging.warning(f"notify_new_entry fehlgeschlagen: {ex}") if 'logging' in globals() else None
    # Browser-Push zusaetzlich (an alle Subscriptions der Empfaenger-User)
    try:
        _send_push_to_target(target_id, entry, sender_user_id)
    except Exception:
        pass


# ===== Browser-Push (VAPID) =====
def _send_webpush(subscription, payload_dict):
    """Sendet eine WebPush-Nachricht an eine Subscription."""
    vapid_priv = os.environ.get("VAPID_PRIVATE_KEY", "")
    vapid_sub = os.environ.get("VAPID_SUBJECT", "mailto:ab@mike-bergmann.de")
    if not vapid_priv:
        return False
    try:
        from pywebpush import webpush
        webpush(
            subscription_info=subscription,
            data=json.dumps(payload_dict, ensure_ascii=False),
            vapid_private_key=vapid_priv,
            vapid_claims={"sub": vapid_sub},
        )
        return True
    except Exception as ex:
        return False


def _send_push_to_target(target_id, entry, sender_user_id=None):
    """Schickt Web-Push an User, die zu einem Target gehoeren und Subscriptions haben."""
    try:
        subs_tc = table_("pushsubs")
    except Exception:
        return
    # Empfaenger ermitteln (wie bei Mail)
    sender_role = None
    sender_uid = sender_user_id or ""
    if sender_uid:
        s = _get_user_full(sender_uid)
        sender_role = s.get("role") if s else None
    if sender_role == "target":
        # Mandant hat geschrieben -> Push an alle Admins
        try:
            admin_users = list(table_("users").query_entities("role eq 'admin'"))
            recipient_uids = [u["RowKey"] for u in admin_users]
        except Exception:
            recipient_uids = []
    else:
        # Admin hat geschrieben -> Push an Target-User
        try:
            tu = list(table_("users").query_entities("targetId eq @t", parameters={"t": target_id}))
            recipient_uids = [u["RowKey"] for u in tu]
        except Exception:
            recipient_uids = []
    # Subscriptions je User laden
    title = f"[ITUKV] {entry.get('betreff', 'Neuer Eintrag')[:80]}"
    body = (entry.get('beschreibung', '') or '')[:200]
    url = f"{FRONTEND_BASE}/?targetId={target_id}#verlauf"
    payload = {"title": title, "body": body, "url": url, "icon": "/Logo_mibeca_Start.png"}
    for uid in recipient_uids:
        try:
            for s in subs_tc.query_entities("userId eq @u", parameters={"u": uid}):
                sub = {
                    "endpoint": s.get("endpoint", ""),
                    "keys": {"p256dh": s.get("p256dh", ""), "auth": s.get("auth", "")},
                }
                ok = _send_webpush(sub, payload)
                if not ok:
                    # Tote Subscription bereinigen
                    try: subs_tc.delete_entity(s["PartitionKey"], s["RowKey"])
                    except Exception: pass
        except Exception:
            continue


@app.route(route="push-config", methods=["GET", "OPTIONS"])
def push_config(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert den VAPID-Public-Key (oeffentlich, nicht geheim)."""
    if req.method == "OPTIONS":
        return opt_()
    return ok_({"publicKey": os.environ.get("VAPID_PUBLIC_KEY", "")})


@app.route(route="push-subscribe", methods=["POST", "OPTIONS"])
def push_subscribe(req: func.HttpRequest) -> func.HttpResponse:
    """User registriert eine Browser-Push-Subscription.
    Body: { endpoint, keys: { p256dh, auth } }"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    endpoint = (body.get("endpoint") or "").strip()
    keys = body.get("keys") or {}
    if not endpoint:
        return err_("endpoint erforderlich", 400)
    uid = p.get("id", "")
    # Stable RowKey aus endpoint-Hash
    import hashlib
    rk = hashlib.sha256(endpoint.encode()).hexdigest()[:32]
    try:
        tc = table_("pushsubs")
        tc.upsert_entity({
            "PartitionKey": "sub",
            "RowKey": rk,
            "userId": uid,
            "userName": p.get("name", "") or p.get("email", ""),
            "endpoint": endpoint,
            "p256dh": keys.get("p256dh", ""),
            "auth": keys.get("auth", ""),
            "createdAt": datetime.utcnow().isoformat(),
        })
    except Exception as ex:
        return err_(f"Speichern fehlgeschlagen: {ex}", 500)
    return ok_({"ok": True, "rk": rk})


@app.route(route="push-unsubscribe", methods=["POST", "OPTIONS"])
def push_unsubscribe(req: func.HttpRequest) -> func.HttpResponse:
    """User entfernt seine Subscription. Body: { endpoint }"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    endpoint = (body.get("endpoint") or "").strip()
    if not endpoint:
        return err_("endpoint erforderlich", 400)
    import hashlib
    rk = hashlib.sha256(endpoint.encode()).hexdigest()[:32]
    try:
        table_("pushsubs").delete_entity("sub", rk)
    except Exception:
        pass
    return ok_({"ok": True})


@app.route(route="push-test", methods=["POST", "OPTIONS"])
def push_test(req: func.HttpRequest) -> func.HttpResponse:
    """Sendet eine Test-Push an die eigene User-ID."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    uid = p.get("id", "")
    sent = 0
    try:
        subs_tc = table_("pushsubs")
        for s in subs_tc.query_entities("userId eq @u", parameters={"u": uid}):
            sub = {"endpoint": s.get("endpoint", ""), "keys": {"p256dh": s.get("p256dh", ""), "auth": s.get("auth", "")}}
            if _send_webpush(sub, {"title": "ITUKV Test-Benachrichtigung", "body": "Push-Notifications funktionieren ✓", "url": FRONTEND_BASE}):
                sent += 1
    except Exception as ex:
        return err_(f"Test fehlgeschlagen: {ex}", 500)
    return ok_({"sent": sent})


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
            tu = list(table_("users").query_entities("targetId eq @t", parameters={"t": target_id}))
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
    """Liefert pro Target die Anzahl ungelesener Verlauf-Eintraege für den aktuellen User."""
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
    items = []  # Liste für Dropdown
    for tid in target_ids:
        try:
            t = dict(table_("targets").get_entity("target", tid))
            verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
        except Exception:
            t = {}
            verlauf = []
        ls = last_seen.get(tid, "1970-01-01T00:00:00")
        my_id = p.get("id", "")
        my_name = (p.get("name", "") or "").strip().lower()
        unread_entries = [e for e in verlauf
                          if (e.get("datum", "") or "") > ls
                          and e.get("createdBy", "") != my_id
                          # Fallback fuer Alt-Eintraege ohne createdBy: per Autor-Name pruefen
                          and (my_name == "" or (e.get("autor", "") or "").strip().lower() != my_name)]
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
    """Markiert alle Verlauf-Eintraege für den User als gelesen.
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

    Schutz: erfordert ?key=<INBOUND_WEBHOOK_SECRET> in der URL.
    SendGrid-Webhook-URL muss diesen Key enthalten.
    """
    # Webhook-Authentifizierung per Shared Secret (verhindert dass Fremde Verlaufseintraege faelschen)
    expected = os.environ.get("INBOUND_WEBHOOK_SECRET", "")
    given = req.params.get("key", "") or req.headers.get("x-webhook-key", "")
    if not expected or not hmac.compare_digest(expected, given):
        return func.HttpResponse(
            json.dumps({"error": "Webhook nicht autorisiert"}),
            status_code=401, headers=CORS,
        )
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

        # Absender-E-Mail aus from_field extrahieren (oft "Name <addr>")
        m_from = re.search(r"<([^>]+)>", from_field)
        from_email = (m_from.group(1) if m_from else from_field).strip().lower()
        kontakt_email = (rec.get("kontaktEmail") or from_email or "").lower()

        # Eintrag in Target-Verlauf (existierende Logik beibehalten)
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

        # Zusaetzlich: Eintrag in Kontakt-Verlauf (CRM-Sicht)
        try:
            if kontakt_email:
                tc = table_("kontakte")
                kontakt = None
                for k in tc.list_entities():
                    if (k.get("email", "") or "").strip().lower() == kontakt_email:
                        kontakt = dict(k); break
                if kontakt:
                    try: kverlauf = json.loads(kontakt.get("verlaufJson") or "[]")
                    except: kverlauf = []
                    if not isinstance(kverlauf, list): kverlauf = []
                    kverlauf.append({
                        "id": "kv" + str(int(datetime.utcnow().timestamp() * 1000)),
                        "typ": "mail_in",
                        "datum": datetime.utcnow().isoformat(),
                        "autor": from_field,
                        "betreff": subject,
                        "beschreibung": text_body[:5000],
                        "kontextTargetId": target_id,
                    })
                    kontakt["verlaufJson"] = json.dumps(kverlauf, ensure_ascii=False)
                    tc.update_entity(kontakt)
        except Exception as ex:
            logging.warning(f"Kontakt-Verlauf-Inbound fehlgeschlagen: {ex}")

        # Forward an Jenny (Reply-To = Original-Absender)
        if ACS_CONN:
            try:
                from azure.communication.email import EmailClient
                client = EmailClient.from_connection_string(ACS_CONN)
                fwd_to = os.environ.get("ACS_REPLY_TO", "") or "jk@mike-bergmann.de"
                fwd_msg = {
                    "senderAddress": ACS_SENDER,
                    "recipients": {"to": [{"address": fwd_to}]},
                    "content": {
                        "subject": f"[ITUKV] Antwort: {subject}",
                        "plainText": f"Antwort von {from_field}\n\nBetreff: {subject}\n\n{text_body}",
                        "html": f'<p style="background:#eaf6fa;padding:10px;border-radius:6px;font-size:12px;color:#0088ba"><strong>Antwort auf Ausschreibung</strong> — automatisch ins Dashboard übernommen.<br/>Von: <strong>{from_field}</strong></p><pre style="white-space:pre-wrap;font-family:Arial">{text_body}</pre>',
                    },
                }
                if from_email:
                    fwd_msg["replyTo"] = [{"address": from_email}]
                client.begin_send(fwd_msg)
            except Exception as ex:
                logging.warning(f"Inbound-Forward an Jenny fehlgeschlagen: {ex}")

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
            prompt = f"""Agiere wie ein erfahrener Presseredakteur für eine IT-Fachzeitschrift.

Erstelle eine Pressemeldung (max. 450 Woerter) zu folgendem Unternehmenskauf, den die mibeca GmbH (Mike Bergmann Akademie) begleitet hat:

- Begleitete Seite: {data.get('seite','Verkaeuferseite')}
- Käufer-Firma: {data.get('kaeuferFirma','')}, Sitz: {data.get('kaeuferOrt','')}
- Verkäufer-Firma: {data.get('verkaeuferFirma','')}, Sitz: {data.get('verkaeuferOrt','')}
- Branche/Schwerpunkt: {data.get('schwerpunkt','IT-Systemhaus')}
- Besonderheiten der Transaktion: {data.get('besonderheiten','')}
- Synergien nach Transaktion: {data.get('synergien','')}

Format:
- Knackige Headline + Sub-Headline
- 3-4 inhaltliche Absaetze
- Drei Zitate: Jennifer Kaplan (mibeca), Mike Bergmann (mibeca), Verkäufer/Käufer (je nach Begleitung)
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
    return f"""IT-Systemhaus-Transaktion: {kf} übernimmt {vf}

In der IT-Branche wurde eine bedeutsame Transaktion abgeschlossen: Die {kf} aus {ko} hat das {schw} {vf} aus {vo} übernommen. Die mibeca GmbH (Mike Bergmann Akademie) hat den Prozess als M&A-Berater begleitet.

{bes}

"Diese Transaktion zeigt, wie wichtig eine strukturierte Begleitung im M&A-Prozess für IT-Unternehmen ist", erklaert Jennifer Kaplan, Transaktionsberaterin der mibeca GmbH. "Beide Seiten konnten wir über den gesamten Prozess hinweg sicher zum Abschluss fuehren."

Strategischer Hintergrund und Synergien: {syn}

"Im IT-Markt sehen wir gerade enorme Konsolidierung – und {kf} positioniert sich damit aktiv für weiteres Wachstum", ergaenzt Mike Bergmann, Gruender der Mike Bergmann Akademie. "Die Verbindung von gewachsener Mittelstands-Erfahrung und der strategischen Synergiepotenzialen ist genau der Treiber, den der IT-Markt braucht."

Über die mibeca GmbH:
Die mibeca GmbH ist als Mike Bergmann Akademie spezialisiert auf M&A-Beratung für IT-Unternehmen im deutschsprachigen Raum. Sie begleitet Verkäufer wie Käufer professionell durch den gesamten Transaktionsprozess.
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
    """Schickt den Pressetext an den Verkäufer/Käufer zur Freigabe."""
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
    target_users = list(table_("users").query_entities("targetId eq @t", parameters={"t": target_id}))
    if not target_users:
        return err_("Kein Target-Login für dieses Target", 400)
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
                <h2 style="color:#0088ba">Pressemitteilung zur Freigabe</h2>
                <p>Hallo {target_name or ''},</p>
                <p>wir haben einen Pressetext zu Deinem Unternehmensverkauf vorbereitet. Bitte gib ihn frei
                oder kommentiere gewuenschte Änderungen direkt im Dashboard.</p>
                <p style="margin:24px 0"><a href="{link}" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Pressetext ansehen &amp; freigeben</a></p>
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
        "beschreibung": kommentar or ("Pressetext wurde freigegeben." if freigabe else "Kunde wuenscht Änderungen."),
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
    """Aggregierte KPIs aus allen Targets / Mandanten für das Controlling-Dashboard."""
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

    # Pipeline-Funnel: aktuelle Phase pro offenes Mandat (grobe Buckets fuer Vergleich)
    phase_buckets = {"1-3": 0, "4-6": 0, "7-9": 0, "10-12": 0, "13-15": 0}
    # Detailliertes Phasen-Mapping pro Mandat-Typ + Mandat-Liste je Phase
    phase_detail_verkauf: dict = {}  # phase_idx -> {count, mandate: [{mbNr, firma}]}
    phase_detail_kauf: dict = {}
    is_kauf_t = lambda t: any(k in (t.get("projekttyp","") or "") for k in ("Kauf", "Investor"))
    for t in open_:
        ph = get_current_phase(t)
        if 1 <= ph <= 3: phase_buckets["1-3"] += 1
        elif 4 <= ph <= 6: phase_buckets["4-6"] += 1
        elif 7 <= ph <= 9: phase_buckets["7-9"] += 1
        elif 10 <= ph <= 12: phase_buckets["10-12"] += 1
        elif ph >= 13: phase_buckets["13-15"] += 1
        # Phasen-Titel aus phasenJson auslesen (falls vorhanden)
        try:
            ph_arr = json.loads(t.get("phasenJson") or "[]")
            titel = ph_arr[ph - 1].get("titel", "") if 1 <= ph <= len(ph_arr) else ""
        except Exception:
            titel = ""
        target_dict = phase_detail_kauf if is_kauf_t(t) else phase_detail_verkauf
        entry = target_dict.setdefault(ph, {"phase": ph, "titel": titel, "count": 0, "mandate": []})
        entry["count"] += 1
        entry["titel"] = entry["titel"] or titel
        if len(entry["mandate"]) < 10:
            entry["mandate"].append({
                "targetId": t.get("RowKey", ""),
                "mbNr": t.get("mbNr", ""),
                "firma": t.get("firma", "") or t.get("verkaueferName", ""),
            })
    phase_detail_verkauf_list = sorted(phase_detail_verkauf.values(), key=lambda x: x["phase"])
    phase_detail_kauf_list = sorted(phase_detail_kauf.values(), key=lambda x: x["phase"])

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

    # Monthly-Series für Chart
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

    # Pipeline-Wert + Provisions-Forecast (Schaetzung aus umsatz-Freitext)
    import re as _re
    def parse_umsatz_teur(s):
        if not s: return 0
        s = str(s).lower()
        # "2,5 mio" -> 2500, "850 teur" -> 850, "12 mio €" -> 12000
        m = _re.search(r'([\d.,]+)\s*mio', s)
        if m:
            try: return float(m.group(1).replace('.', '').replace(',', '.')) * 1000
            except: pass
        m = _re.search(r'([\d.,]+)\s*(teur|t€|k€)', s)
        if m:
            try: return float(m.group(1).replace('.', '').replace(',', '.'))
            except: pass
        # nur Zahl ohne Einheit: vermute TEUR
        m = _re.search(r'([\d.,]+)', s)
        if m:
            try: return float(m.group(1).replace('.', '').replace(',', '.'))
            except: pass
        return 0

    pipeline_wert = sum(parse_umsatz_teur(t.get("umsatz", "")) for t in open_)
    closed_wert = sum(parse_umsatz_teur(t.get("umsatz", "")) for t in closed)
    # Provisions-Forecast: 4% Erfolgshonorar als Faustregel
    prov_quote_pct = 4.0
    provision_offen = pipeline_wert * (prov_quote_pct / 100)
    provision_realisiert = closed_wert * (prov_quote_pct / 100)

    # Top-Mandate nach Umsatz
    top_mandate = sorted(
        [{"mbNr": t.get("mbNr",""), "verkaueferName": t.get("verkaueferName",""),
          "umsatz": t.get("umsatz",""), "umsatzTeur": parse_umsatz_teur(t.get("umsatz","")),
          "status": t.get("status",""), "phase": get_current_phase(t)}
         for t in filtered],
        key=lambda x: -x["umsatzTeur"]
    )[:10]

    # Quartals-Vergleich (innerhalb Jahres oder ueber alle Jahre)
    by_quarter = {}
    for t in filtered:
        d = get_closed(t) or get_created(t)
        if not d: continue
        q = f"{d.year}-Q{(d.month - 1) // 3 + 1}"
        by_quarter.setdefault(q, {"created": 0, "closed": 0})
        if get_created(t) and ((get_created(t).year * 100 + get_created(t).month - 1) // 3 + 1) == ((d.year * 100 + d.month - 1) // 3 + 1):
            by_quarter[q]["created"] += 1
        if get_closed(t) and ((get_closed(t).year * 100 + get_closed(t).month - 1) // 3 + 1) == ((d.year * 100 + d.month - 1) // 3 + 1):
            by_quarter[q]["closed"] += 1
    quarterly = [{"quarter": k, **v} for k, v in sorted(by_quarter.items())]

    return ok_({
        "year": year_int,
        "total": len(filtered),
        "open": len(open_),
        "closed": len(closed),
        "successRate": success_rate,
        "avgDurationDays": avg_duration,
        "pipelineFunnel": phase_buckets,
        "pipelineByPhaseVerkauf": phase_detail_verkauf_list,
        "pipelineByPhaseKauf": phase_detail_kauf_list,
        "dauerProTyp": dauer_pro_typ,
        "kaufAnzahl": kauf_anzahl,
        "verkaufAnzahl": verkauf_anzahl,
        "prCount": pr_count,
        "prQuote": pr_quote,
        "monthly": monthly,
        "quarterly": quarterly,
        # Pipeline + Provision (Schaetzwerte)
        "pipelineWertTeur": round(pipeline_wert),
        "closedWertTeur": round(closed_wert),
        "provisionForecastTeur": round(provision_offen),
        "provisionRealisiertTeur": round(provision_realisiert),
        "provisionQuotePct": prov_quote_pct,
        "topMandate": top_mandate,
        "yearsAvailable": sorted({
            (get_created(t) or get_closed(t)).year for t in targets
            if (get_created(t) or get_closed(t))
        }, reverse=True),
    })


@app.route(route="controlling-pdf", methods=["GET", "POST", "OPTIONS"])
def controlling_pdf(req: func.HttpRequest) -> func.HttpResponse:
    """Erstellt einen schicken Beirats-Bericht als PDF aus den Controlling-KPIs."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    # Stats holen via interner Aufruf (vereinfacht: wir simulieren ein GET)
    class _ReqStub:
        method = "GET"
        params = {"year": req.params.get("year", "")}
        headers = req.headers
        def get_json(self): return {}
    try:
        stats_resp = controlling_stats(_ReqStub())  # type: ignore
        stats = json.loads(stats_resp.get_body().decode())
    except Exception as ex:
        return err_(f"Statistik nicht ladbar: {ex}", 500)

    year = stats.get("year") or datetime.utcnow().year
    now_str = datetime.utcnow().strftime("%d.%m.%Y")
    from html import escape as _esc

    funnel = stats.get("pipelineFunnel", {})
    top_html = "<p style='color:#999'>Keine Daten</p>" if not stats.get("topMandate") else (
        "<table style='width:100%;border-collapse:collapse'><thead><tr style='border-bottom:1px solid #ddd'>"
        "<th style='text-align:left;padding:6px'>mb-Nr</th><th style='text-align:left;padding:6px'>Verkäufer</th>"
        "<th style='text-align:right;padding:6px'>Umsatz (TEUR)</th><th style='text-align:left;padding:6px'>Phase</th>"
        "<th style='text-align:left;padding:6px'>Status</th></tr></thead><tbody>"
        + "".join(
            f"<tr style='border-bottom:1px solid #eee'><td style='padding:6px;font-family:monospace'>{_esc(m.get('mbNr',''))}</td>"
            f"<td style='padding:6px'>{_esc(m.get('verkaueferName',''))}</td>"
            f"<td style='padding:6px;text-align:right'>{int(m.get('umsatzTeur', 0)):,}</td>"
            f"<td style='padding:6px'>Phase {m.get('phase','-')}</td>"
            f"<td style='padding:6px'>{_esc(m.get('status',''))}</td></tr>"
            for m in stats.get("topMandate", [])
        ) + "</tbody></table>"
    )

    html = f"""<!doctype html><html><head><meta charset='utf-8'>
<style>
@page {{ size: A4; margin: 18mm 16mm; }}
body {{ font-family: Helvetica, Arial, sans-serif; color: #161e2a; font-size: 11pt; line-height: 1.5; }}
h1 {{ color: #0088ba; font-size: 22pt; margin: 0 0 4px; }}
h2 {{ color: #0088ba; font-size: 14pt; margin: 22px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #0088ba33; }}
.meta {{ color: #666; font-size: 10pt; margin-bottom: 24px; }}
.grid {{ display: flex; flex-wrap: wrap; gap: 14px; margin: 10px 0; }}
.kpi {{ flex: 1 1 30%; min-width: 30%; background: #f0fdfa; border-left: 4px solid #0088ba; padding: 12px 14px; }}
.kpi .v {{ font-size: 22pt; font-weight: bold; color: #0088ba; }}
.kpi .l {{ font-size: 10pt; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
.kpi .s {{ font-size: 9pt; color: #999; margin-top: 4px; }}
.funnel {{ background: #fafafa; border-radius: 6px; padding: 12px; }}
.funnel-row {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; font-size: 10pt; }}
.funnel-row .bar {{ background: #0088ba; height: 18px; border-radius: 3px; }}
.funnel-row .lbl {{ width: 100px; }}
.footer {{ color: #999; font-size: 9pt; margin-top: 36px; border-top: 1px solid #eee; padding-top: 10px; }}
</style></head><body>
  <h1>Beirats-Bericht M&amp;A {year}</h1>
  <div class='meta'>Stand: {now_str} &middot; mibeca GmbH &middot; ITUKV Dashboard</div>

  <h2>Auf einen Blick</h2>
  <div class='grid'>
    <div class='kpi'><div class='l'>Mandate gesamt</div><div class='v'>{stats.get('total', 0)}</div><div class='s'>{stats.get('verkaufAnzahl',0)} Verkauf · {stats.get('kaufAnzahl',0)} Kauf</div></div>
    <div class='kpi'><div class='l'>Aktiv in der Pipeline</div><div class='v'>{stats.get('open', 0)}</div><div class='s'>laufende Mandate</div></div>
    <div class='kpi'><div class='l'>Erfolgreich abgeschlossen</div><div class='v'>{stats.get('closed', 0)}</div><div class='s'>{stats.get('successRate',0)}% Erfolgsquote</div></div>
    <div class='kpi'><div class='l'>Ø Deal-Dauer</div><div class='v'>{stats.get('avgDurationDays', 0)} T</div><div class='s'>vom Mandat zur Closing</div></div>
    <div class='kpi'><div class='l'>Pipeline-Wert</div><div class='v'>{int(stats.get('pipelineWertTeur', 0)):,} T€</div><div class='s'>Summe Umsätze offener Mandate</div></div>
    <div class='kpi'><div class='l'>Provisions-Forecast</div><div class='v'>{int(stats.get('provisionForecastTeur', 0)):,} T€</div><div class='s'>bei {stats.get('provisionQuotePct',4)}% Erfolgshonorar</div></div>
  </div>

  <h2>Pipeline-Funnel (offene Mandate nach Phase)</h2>
  <div class='funnel'>
    <div class='funnel-row'><span class='lbl'>Phase 1-3 (UVE):</span><span class='bar' style='width:{(funnel.get('1-3',0)*20)}px'></span><span>{funnel.get('1-3',0)}</span></div>
    <div class='funnel-row'><span class='lbl'>Phase 4-6 (NDA):</span><span class='bar' style='width:{(funnel.get('4-6',0)*20)}px'></span><span>{funnel.get('4-6',0)}</span></div>
    <div class='funnel-row'><span class='lbl'>Phase 7-9 (Angebot):</span><span class='bar' style='width:{(funnel.get('7-9',0)*20)}px'></span><span>{funnel.get('7-9',0)}</span></div>
    <div class='funnel-row'><span class='lbl'>Phase 10-12 (LOI/DD):</span><span class='bar' style='width:{(funnel.get('10-12',0)*20)}px'></span><span>{funnel.get('10-12',0)}</span></div>
    <div class='funnel-row'><span class='lbl'>Phase 13-15 (Closing):</span><span class='bar' style='width:{(funnel.get('13-15',0)*20)}px'></span><span>{funnel.get('13-15',0)}</span></div>
  </div>

  <h2>Top-10 Mandate nach Umsatz</h2>
  {top_html}

  <h2>Realisierte Provision {year}</h2>
  <p><strong>{int(stats.get('provisionRealisiertTeur', 0)):,} T€</strong> realisiertes Erfolgshonorar aus {stats.get('closed',0)} abgeschlossenen Mandaten (geschätzt mit {stats.get('provisionQuotePct',4)}%).</p>
  <p>Marktansprache-Quote: {stats.get('prQuote', 0)}% der abgeschlossenen Mandate hatten eine Presse-Erfolgsmeldung.</p>

  <div class='footer'>
    Automatisch erstellt durch das ITUKV Dashboard &middot; nur für den internen Gebrauch / Beirat
  </div>
</body></html>"""

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html, base_url="/").write_pdf()
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)
    return pdf_response(pdf_bytes, f"Beiratsbericht_{year}.pdf")


@app.route(route="lessons-learned", methods=["GET", "OPTIONS"])
def lessons_learned_aggregat(req: func.HttpRequest) -> func.HttpResponse:
    """Aggregiert Lessons Learned aller Targets für Wissensdatenbank."""
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
    """Public: liefert Landing-Page-Daten für eine mb-Nr."""
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
        "seoTitle": landing.get("seoTitle", ""),
        "seoDescription": landing.get("seoDescription", ""),
        "published": True,
    })


@app.route(route="landing-anfrage", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def landing_anfrage(req: func.HttpRequest) -> func.HttpResponse:
    """Public: ein Interessent registriert sich für mb-XXX."""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    mb_nr = (body.get("mbNr") or "").strip().lower()
    firma = (body.get("firma") or "").strip()
    # Name: kombiniert aus vorname+nachname ODER altes "name"-Feld (Abwärtskompat)
    vorname = (body.get("vorname") or "").strip()
    nachname = (body.get("nachname") or "").strip()
    name = (vorname + " " + nachname).strip() or (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    website = (body.get("website") or "").strip()
    plz_ort = (body.get("plzOrt") or "").strip()
    # PLZ/Ort splitten falls zusammen eingegeben
    plz, ort = (body.get("plz", "") or "").strip(), (body.get("ort", "") or "").strip()
    if plz_ort:
        import re as _re
        m = _re.match(r"(\d{4,5})\s+(.+)", plz_ort)
        if m: plz, ort = m.group(1), m.group(2).strip()
        else: ort = plz_ort
    if not (mb_nr and email and (firma or name)):
        return err_("mbNr, email und firma oder name erforderlich", 400)
    # Target finden
    items = list(table_("targets").list_entities())
    t = next((x for x in items if (x.get("mbNr", "") or "").lower() == mb_nr), None)
    if not t:
        return err_("Projekt nicht gefunden", 404)
    target_id = t.get("RowKey", "")

    # Lead-Anreicherung versuchen (Impressum-Crawl + AI)
    enrich = {}
    try:
        enrich = enrich_lead_data(website, email)
    except Exception as ex:
        logging.warning(f"Anreicherung fehlgeschlagen: {ex}")

    # Interessent anlegen
    iid = str(uuid.uuid4())
    token = secrets.token_urlsafe(24)
    entity = {
        "PartitionKey": "interessent", "RowKey": iid,
        "targetId": target_id,
        "firma": firma, "name": name, "vorname": vorname, "nachname": nachname,
        "email": email, "telefon": body.get("telefon", ""), "website": website,
        "plz": plz, "ort": ort,
        "ndaStatus": "ausstehend",
        "exposeToken": token,  # für expose-mb-XXX/:token Zugriff
        "rating": 0, "veto": False, "freigegebenFuerKontakt": False,
        "kommentar": body.get("kommentar", ""),
        "createdAt": datetime.utcnow().isoformat(),
        "herkunft": f"Landing-Page {mb_nr}",
        # Angereicherte Felder
        "enrichDomain": enrich.get("_domain", ""),
        "enrichImpressum": bool(enrich.get("_impressum", False)),
        "enrichFirmenname": enrich.get("firmenname", "") or "",
        "enrichGeschaeftsfuehrer": ", ".join(enrich.get("geschaeftsfuehrer", []) or []) if isinstance(enrich.get("geschaeftsfuehrer"), list) else (enrich.get("geschaeftsfuehrer", "") or ""),
        "enrichStrasse": enrich.get("strasse", "") or "",
        "enrichPLZ": str(enrich.get("postleitzahl", "") or ""),
        "enrichOrt": enrich.get("ort", "") or "",
        "enrichTelefon": enrich.get("telefon", "") or "",
        "enrichEmailImpressum": enrich.get("email_impressum", "") or "",
        "enrichUstId": enrich.get("umsatzsteuer_id", "") or "",
    }
    table_("interessenten").create_entity(entity)

    # CRM-Eintrag: als Kauf-Interessent anlegen oder bestehenden anreichern (dedupe per email)
    try:
        tc = table_("kontakte")
        existing = None
        if email:
            for k in tc.list_entities():
                if (k.get("email", "") or "").strip().lower() == email.lower():
                    existing = dict(k); break
        # Bevorzugt korrekter Firmenname aus Impressum
        firma_final = enrich.get("firmenname") or firma
        ort_final = enrich.get("ort") or ort
        plz_final = str(enrich.get("postleitzahl") or "") or plz
        if existing:
            updates = {**existing, "istInvestor": True, "updatedAt": datetime.utcnow().isoformat()}
            herk = (existing.get("herkunft", "") or "")
            new_herk = f"Landing-Page {mb_nr}"
            updates["herkunft"] = (herk + " · " + new_herk).strip(" ·") if new_herk not in herk else herk
            for fld, val in [("firma", firma_final), ("name", name), ("telefon", body.get("telefon", "")),
                             ("website", website), ("plz", plz_final), ("ort", ort_final)]:
                if val and not existing.get(fld):
                    updates[fld] = val
            if body.get("kommentar"):
                kom = existing.get("kommentar", "")
                addon = f"[{mb_nr}] {body.get('kommentar')}"
                updates["kommentar"] = (kom + "\n" + addon).strip() if kom else addon
            try: tc.update_entity(updates, mode="replace")
            except Exception as ex: logging.warning(f"CRM-Anreicherung fehlgeschlagen: {ex}")
        else:
            tc.create_entity({
                "PartitionKey": "kontakt", "RowKey": str(uuid.uuid4()),
                "firma": firma_final, "name": name, "email": email,
                "telefon": body.get("telefon", ""), "website": website,
                "plz": plz_final, "ort": ort_final,
                "sucht": f"Zukauf · Profil {mb_nr}", "bietet": "",
                "kommentar": body.get("kommentar", ""),
                "istInvestor": True, "istKunde": False, "istExKunde": False, "istTarget": False,
                "investorTyp": "Strategisch", "typ": "Strategisch",
                "kundenstatus": "Investor",
                "herkunft": f"Landing-Page {mb_nr}",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat(),
            })
    except Exception as ex:
        logging.warning(f"CRM-Eintrag fehlgeschlagen: {ex}")

    # Eintrag im Kontakt-Verlauf (kontakte.verlaufJson) — fuer CRM-Akten-Ansicht
    # (KEIN Eintrag im Target-Verlauf — das ist nur Mandanten-Kommunikation.
    #  Interessenten-Anmeldungen sieht mibeca im Interessenten-Tab.)
    try:
        tc = table_("kontakte")
        kontakt = None
        for k in tc.list_entities():
            if (k.get("email", "") or "").strip().lower() == (email or "").lower():
                kontakt = dict(k); break
        if kontakt:
            try: kverlauf = json.loads(kontakt.get("verlaufJson") or "[]")
            except: kverlauf = []
            if not isinstance(kverlauf, list): kverlauf = []
            kverlauf.append({
                "id": "kv" + str(int(datetime.utcnow().timestamp() * 1000)),
                "typ": "wichtig",
                "datum": datetime.utcnow().isoformat(),
                "autor": "Landing-Page",
                "betreff": f"Für Exposé angemeldet ({mb_nr})",
                "beschreibung": f"Hat sich über die Landing-Page für das Exposé eingetragen.{(' Kommentar: ' + body.get('kommentar')) if body.get('kommentar') else ''}",
                "kontextTargetId": target_id,
                "kontextMbNr": mb_nr,
            })
            kontakt["verlaufJson"] = json.dumps(kverlauf, ensure_ascii=False)
            tc.update_entity(kontakt)
    except Exception as ex:
        logging.warning(f"Kontakt-Verlauf-Eintrag (Anmeldung) fehlgeschlagen: {ex}")

    # Zapier-Webhook (Google Sheets-Sync) — PRO Mandat individuell konfigurierbar.
    # Das Feld `zapierWebhookUrl` am Target steuert, ob/wohin die Anmeldedaten
    # weitergeleitet werden. Leer = keine Weiterleitung.
    zap_url = (t.get("zapierWebhookUrl") or "").strip()
    if zap_url:
        try:
            import urllib.request
            payload = json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "mbNr": mb_nr,
                "firma": firma_final if 'firma_final' in dir() else firma,
                "name": name,
                "vorname": vorname,
                "nachname": nachname,
                "email": email,
                "telefon": body.get("telefon", ""),
                "website": website,
                "plz": plz_final if 'plz_final' in dir() else plz,
                "ort": ort_final if 'ort_final' in dir() else ort,
                "kommentar": body.get("kommentar", ""),
                "herkunft": f"Landing-Page {mb_nr}",
                "ndaStatus": "ausstehend",
                "interessentId": iid,
                "exposeUrl": f"{LANDING_BASE}/expose-{mb_nr}/{token}",
                # Aus Impressum-Anreicherung (optional)
                "enrichFirmenname": enrich.get("firmenname", "") or "",
                "enrichGeschaeftsfuehrer": entity.get("enrichGeschaeftsfuehrer", ""),
                "enrichStrasse": enrich.get("strasse", "") or "",
            }).encode("utf-8")
            req = urllib.request.Request(zap_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=5).read()
        except Exception as ex:
            logging.warning(f"Zapier-Webhook fehlgeschlagen: {ex}")

    # Mail an Interessent: Expose-Link + NDA
    expose_url = f"{LANDING_BASE}/expose-{mb_nr}/{token}"
    if ACS_CONN:
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            # An Interessent — Vorname aus name extrahieren
            vorname = (name or firma or "").split(" ")[0]
            html_int = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6;max-width:600px">
<h2 style="color:#0088ba">Dein Exposé zu Projekt {mb_nr.upper()}</h2>
<p>Hallo {vorname},</p>
<p>vielen Dank für Dein Interesse am Projekt <strong>{mb_nr.upper()}</strong>.</p>
<p>Über den nachfolgenden Link erreichst Du Deinen persönlichen Projektbereich. Dort kannst Du das Exposé herunterladen, die Vertraulichkeitsvereinbarung (NDA) herunterladen und das unterschriebene NDA direkt wieder hochladen.</p>
<p style="margin:24px 0"><a href="{expose_url}" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Zum Exposé-Bereich</a></p>

<h3 style="color:#0088ba;margin-top:32px">Das Unternehmen hat Dein Interesse geweckt – wie geht es jetzt weiter?</h3>

<p><strong>1. NDA herunterladen und unterschreiben</strong><br/>
Um die Vertraulichkeit des Verkaufsprozesses zu gewährleisten, benötigen wir zunächst eine unterzeichnete Vertraulichkeitsvereinbarung (NDA).</p>

<p><strong>2. NDA hochladen</strong><br/>
Lade das unterschriebene NDA anschließend bequem über die Upload-Funktion in Deinem Projektbereich hoch.</p>

<p><strong>3. Termin mit unserer M&amp;A-Beraterin vereinbaren</strong><br/>
Sobald Dein NDA bei uns eingegangen ist, schalten wir die Terminbuchung mit unserer M&amp;A-Beraterin Jennifer Kaplan frei.</p>

<p>In diesem Gespräch besprechen wir:</p>
<ul>
  <li>Deine Kaufabsichten und Zielsetzungen</li>
  <li>Offene Fragen zum Unternehmen</li>
  <li>Den weiteren Ablauf des Kaufprozesses</li>
  <li>Die nächsten Schritte mit dem Verkäufer</li>
</ul>

<p><strong>4. Kontakt zum Unternehmen</strong><br/>
Wenn die Rahmenbedingungen für beide Seiten grundsätzlich passen, stimmen wir die nächsten Schritte mit dem Verkäufer ab. Nach dessen Freigabe erhältst Du die Kontaktdaten des Unternehmens und kannst in die vertiefte Prüfung einsteigen.</p>

<div style="background:#f7f8fa;border-left:4px solid #0088ba;padding:12px 16px;margin:24px 0;border-radius:4px">
  <p style="margin:0"><strong>Wichtiger Hinweis</strong><br/>
  Aus Gründen der Vertraulichkeit können weiterführende Informationen sowie Rückfragen zum Unternehmen erst nach Eingang des unterschriebenen NDA beantwortet werden.</p>
</div>

<p>Bei Fragen zum Ablauf erreichst Du Jennifer Kaplan unter:<br/>
<a href="mailto:jk@mike-bergmann.de" style="color:#0088ba">jk@mike-bergmann.de</a></p>

<p>Wir freuen uns darauf, Dich durch den weiteren Kaufprozess zu begleiten.</p>

<p>Viele Grüße<br/>
<strong>Dein M&amp;A-Team der Mike Bergmann Akademie</strong></p>

<p style="font-size:13px;color:#666;margin-top:24px"><em>P.S.: Je schneller das unterschriebene NDA bei uns eingeht, desto schneller können wir den nächsten Schritt im Transaktionsprozess gemeinsam angehen.</em></p>
</body></html>"""
            plain_int = (f"Hallo {vorname},\n\n"
                         f"vielen Dank für Dein Interesse am Projekt {mb_nr.upper()}.\n\n"
                         f"Zum Projektbereich: {expose_url}\n\n"
                         f"Nächste Schritte: NDA herunterladen & unterschreiben → hochladen → Termin mit Jennifer Kaplan buchen.\n\n"
                         f"Fragen? jk@mike-bergmann.de\n\nViele Grüße\nDein M&A-Team der Mike Bergmann Akademie")
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": email}]},
                "content": {"subject": f"Dein Exposé zu Projekt {mb_nr.upper()}", "plainText": plain_int, "html": html_int},
            })
            # An mibeca-Team + Target-User
            notify_to = [os.environ.get("MIBECA_NOTIFY_EMAIL", "jk@mike-bergmann.de")]
            tu = list(table_("users").query_entities("targetId eq @t", parameters={"t": target_id}))
            for u in tu:
                if u.get("email"): notify_to.append(u["email"])
            for rcpt in notify_to:
                client.begin_send({
                    "senderAddress": ACS_SENDER,
                    "recipients": {"to": [{"address": rcpt}]},
                    "content": {"subject": f"[ITUKV] Neue Anfrage zu {mb_nr.upper()}", "plainText": f"{firma or name} ({email}) interessiert sich für {mb_nr}.", "html": f"<p><strong>Neue Anfrage zu {mb_nr.upper()}</strong></p><p>Firma: {firma}</p><p>Name: {name}</p><p>E-Mail: {email}</p>"},
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
    if not is_valid_public_token(token):
        return err_("Token ungueltig", 400)
    items = list(table_("interessenten").query_entities("exposeToken eq @t", parameters={"t": token}))
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
        "terminBookingUrl": landing.get("terminBookingUrl") or DEFAULT_BOOKINGS_URL,
        "headline": landing.get("headline", ""),
        # Auto-PDFs aus System (immer verfuegbar, auch wenn keine externen URLs gepflegt sind)
        "autoExposePdfUrl": f"/api/expose-public-pdf?token={token}",
        "autoNdaPdfUrl": f"/api/nda-public-pdf?token={token}",
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
    if not file_data:
        return err_("fileData erforderlich", 400)
    if not is_valid_public_token(token):
        return err_("Token ungueltig", 400)
    items = list(table_("interessenten").query_entities("exposeToken eq @t", parameters={"t": token}))
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
    # Auch im NDA-Ordner des Targets (Datenraum) ablegen
    try:
        doc_blob_name = f"{target_id}/NDA/NDA_{i.get('firma') or i.get('name','interessent')}_{datetime.utcnow().strftime('%Y%m%d')}.pdf".replace(" ", "_")
        _blob_container_lazy("datenraum").upload_blob(doc_blob_name, pdf_bytes, overwrite=True)
        doc_id = "nda-" + i["RowKey"]
        table_("dokumente").upsert_entity({
            "PartitionKey": target_id, "RowKey": doc_id,
            "fileName": f"NDA_{i.get('firma') or i.get('name','interessent')}_signiert.pdf",
            "ordner": "NDA", "blobName": doc_blob_name, "container": "datenraum",
            "size": len(pdf_bytes), "contentType": "application/pdf",
            "uploadedAt": datetime.utcnow().isoformat(),
            "uploadedBy": i.get("email", ""),
            "quelle": "Upload Interessent",
        })
    except Exception as ex:
        logging.warning(f"NDA als Target-Dokument speichern fehlgeschlagen: {ex}")
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
            termin_url = landing.get("terminBookingUrl") or DEFAULT_BOOKINGS_URL
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
<p>Hallo {_first_name(i.get('name')) or i.get('firma') or ''},</p>
<p>vielen Dank für Dein unterschriebenes NDA zur Projektnummer <strong>{t.get('mbNr','')}</strong> &ndash; damit hast Du den ersten wichtigen Schritt gemacht!</p>
<h3 style="color:#0088ba">Wie geht es jetzt weiter?</h3>
<p>Du hast nun Zugang zum Exposé, das Dir einen ersten Überblick über das Unternehmen gibt. Für tiefergehende Informationen und Zahlen ist ein persönliches Gespräch erforderlich.</p>
<p>Buche hier Deinen Termin mit unserer M&amp;A-Beraterin Jennifer Kaplan:</p>
{(('<p style="margin:24px 0"><a href="' + termin_url + '" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Termin jetzt buchen</a></p>') if termin_url else '<p><em>Termin-Link wird in Kuerze nachgereicht.</em></p>')}
<p>In diesem ca. 15-minuetigen Gespräch klaert Ihr:</p>
<ul>
  <li>Ob das Unternehmen zu Deiner Zukaufstrategie passt</li>
  <li>Deine konkreten Zukaufsvisionen &ndash; damit wir diese mit dem Profil abgleichen koennen</li>
  <li>Den weiteren Ablauf des Prozesses</li>
  <li>Wie die Rolle unserer M&amp;A-Beraterin Dich durch den gesamten Transaktionsprozess begleitet</li>
  <li>Ob ggf. ein Folgegespraech direkt mit dem Verkäufer sinnvoll ist</li>
</ul>
<p><strong>Wichtig:</strong> Nur wenn die ersten Parameter nach dem Gespräch übereinstimmen, senden wir Dir im Anschluss weitere Unterlagen &ndash; z.B. detaillierte Unternehmenskennzahlen.</p>
<p>Wir freuen uns auf den Austausch!</p>
<p>Herzliche Grüße<br/>Dein M&amp;A-Team der Mike Bergmann Akademie</p>
</body></html>"""
            nda_attachment = {
                "name": f"NDA_{t.get('mbNr','')}_unterzeichnet.pdf",
                "contentType": "application/pdf",
                "contentInBase64": base64.b64encode(pdf_bytes).decode(),
            }
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": i.get("email", "")}]},
                "content": {"subject": f"NDA erhalten – nächste Schritte zu {t.get('mbNr','')}", "plainText": f"NDA bestätigt. Termin buchen: {termin_url}", "html": html},
                "attachments": [nda_attachment],
            })
            # Notification an Jenny
            mibeca_mail = os.environ.get("MIBECA_NOTIFY_EMAIL", "jk@mike-bergmann.de")
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": mibeca_mail}]},
                "content": {"subject": f"[ITUKV] NDA erhalten zu {t.get('mbNr','')}", "plainText": f"{i.get('firma') or i.get('name')} hat NDA hochgeladen.", "html": f"<p><strong>NDA erhalten</strong> – Interessent kann jetzt Termin buchen.</p><p>Projekt: {t.get('mbNr','')}</p><p>Interessent: {i.get('firma','')} / {i.get('name','')} / {i.get('email','')}</p><p>Das unterschriebene NDA liegt im NDA-Ordner der Projekt-Akte und ist im Anhang.</p>"},
                "attachments": [nda_attachment],
            })
        except Exception as ex:
            logging.warning(f"NDA-Mail fehlgeschlagen: {ex}") if 'logging' in globals() else None
    return ok_({"ok": True})


# =========================================================================
# LEAD-ANREICHERUNG (Impressum-Crawl + Azure-OpenAI-Extraktion)
# =========================================================================

_IMPRESSUM_PATHS = ["/impressum", "/impressum.html", "/impressum/", "/legal/impressum",
                    "/de/impressum", "/kontakt", "/über-uns", "/about", "/legal"]
_PRIVATE_DOMAINS = {"gmail.com", "googlemail.com", "gmx.de", "gmx.net", "gmx.com", "web.de",
                    "hotmail.com", "hotmail.de", "outlook.com", "outlook.de", "live.com",
                    "yahoo.com", "yahoo.de", "icloud.com", "t-online.de", "aol.com",
                    "freenet.de", "mail.de", "posteo.de", "mailbox.org", "arcor.de"}

def _domain_from(website_or_email: str) -> str:
    if not website_or_email: return ""
    s = website_or_email.strip()
    if "@" in s and "/" not in s:
        return s.split("@", 1)[1].lower()
    s = s.lower().replace("https://", "").replace("http://", "").split("/")[0]
    if s.startswith("www."): s = s[4:]
    return s.split("?")[0].split("#")[0]

def _fetch_impressum(domain: str):
    """Returns (impressum_text, website_url) or ('','')"""
    try:
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
    except Exception:
        return "", ""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; mibeca-enricher/1.0)"}
    for scheme in ("https", "http"):
        base = f"{scheme}://{domain}"
        try:
            resp = requests.get(base, headers=headers, timeout=6, allow_redirects=True)
            if resp.status_code >= 400: continue
            final_base = f"https://{resp.url.split('/')[2]}"
            soup = BeautifulSoup(resp.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href_low = link["href"].lower()
                if "impressum" in href_low or "legal" in href_low:
                    full = urljoin(final_base + "/", link["href"])
                    try:
                        imp = requests.get(full, headers=headers, timeout=6)
                        if imp.status_code == 200:
                            text = BeautifulSoup(imp.text, "html.parser").get_text(" ", strip=True)
                            if len(text) > 100:
                                return text[:6000], final_base
                    except Exception:
                        continue
        except Exception:
            pass
        for path in _IMPRESSUM_PATHS:
            try:
                resp = requests.get(f"{base}{path}", headers=headers, timeout=6, allow_redirects=True)
                if resp.status_code == 200:
                    text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)
                    if len(text) > 100:
                        final_base = f"https://{resp.url.split('/')[2]}"
                        return text[:6000], final_base
            except Exception:
                continue
    return "", ""

_ENRICH_PROMPT = """Du analysierst den Text einer deutschen Firmen-Impressum-Seite.
Extrahiere folgende Felder als JSON. Wenn ein Feld nicht gefunden wird, setze es auf null.
Gib NUR das JSON zurück, keinen anderen Text, keine Erklaerungen, kein Markdown.

Felder:
- firmenname: Vollständiger Firmenname inkl. Rechtsform (z.B. "Muster GmbH")
- geschaeftsfuehrer: Geschäftsführer als Liste (z.B. ["Max Mustermann"])
- strasse: Strasse und Hausnummer
- postleitzahl: PLZ
- ort: Stadt/Ort
- land: Land
- umsatzsteuer_id: USt-ID (z.B. "DE123456789")
- telefon: Festnetz-Telefonnummer (im internationalen Format wenn möglich)
- email_impressum: Kontakt-E-Mail aus dem Impressum

Impressum-Text:
{text}"""

def _enrich_via_ai(impressum_text: str) -> dict:
    if not impressum_text or len(impressum_text) < 100:
        return {}
    endpoint = os.environ.get("AZURE_AI_ENDPOINT", "")
    api_key = os.environ.get("AZURE_AI_KEY", "")
    deployment = os.environ.get("AZURE_AI_DEPLOYMENT", "gpt-4o-mini")
    if not endpoint or not api_key:
        return {}
    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version="2024-10-21")
        resp = client.chat.completions.create(
            model=deployment, temperature=0, max_tokens=800,
            messages=[{"role": "user", "content": _ENRICH_PROMPT.format(text=impressum_text)}],
        )
        raw = resp.choices[0].message.content.strip()
        import re as _re
        m = _re.search(r"\{.*\}", raw, _re.DOTALL)
        if m: return json.loads(m.group())
    except Exception as ex:
        logging.warning(f"AI-Anreicherung fehlgeschlagen: {ex}")
    return {}

def enrich_lead_data(website: str, email: str) -> dict:
    """Versucht Domain → Impressum → AI-Extraktion. Liefert dict oder {}."""
    domain = _domain_from(website) or _domain_from(email)
    if not domain or domain in _PRIVATE_DOMAINS:
        return {"_domain": domain, "_skipped": "private oder leer"}
    text, base = _fetch_impressum(domain)
    if not text:
        return {"_domain": domain, "_impressum": False}
    data = _enrich_via_ai(text) or {}
    data["_domain"] = domain
    data["_website"] = base
    data["_impressum"] = True
    return data


# =========================================================================
# PUBLIC: NDA + Exposé PDFs für Käufer (via exposeToken)
# =========================================================================

def _build_nda_form_for_interessent(i, t):
    """Baut das NDA-Form-Dict aus Interessent + Target zusammen."""
    return {
        "firma": i.get("firma", ""),
        "vertreten": i.get("name", ""),
        "adresse": i.get("strasse", "") or i.get("adresse", ""),
        "plzOrt": (i.get("plz", "") + " " + i.get("ort", "")).strip(),
        "email": i.get("email", ""),
        "ort": i.get("ort", "") or "Uelzen",
        "datum": datetime.utcnow().strftime("%d.%m.%Y"),
        "mbNr": t.get("mbNr", ""),
        "gueltigBis": str(datetime.utcnow().year + 2),
    }


@app.route(route="nda-public-pdf", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def nda_public_pdf(req: func.HttpRequest) -> func.HttpResponse:
    """Public: liefert NDA-PDF mit Interessenten-Daten vorbefuellt (zur Unterschrift)."""
    if req.method == "OPTIONS":
        return opt_()
    token = (req.params.get("token") or "").strip()
    if not is_valid_public_token(token):
        return err_("Token ungueltig", 400)
    items = list(table_("interessenten").query_entities("exposeToken eq @t", parameters={"t": token}))
    if not items:
        return err_("Token ungueltig", 404)
    i = dict(items[0])
    try:
        t = dict(table_("targets").get_entity("target", i.get("targetId", "")))
    except Exception:
        return err_("Target nicht gefunden", 404)
    form = _build_nda_form_for_interessent(i, t)
    try:
        pdf_bytes = _render_nda_pdf_bytes(form, "investor")
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)
    return pdf_response(pdf_bytes, f'NDA_{t.get("mbNr","")}.pdf')


@app.route(route="expose-public-pdf", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def expose_public_pdf(req: func.HttpRequest) -> func.HttpResponse:
    """Public: liefert das volle Exposé-PDF (aus target.exposeJson) via Token."""
    if req.method == "OPTIONS":
        return opt_()
    token = (req.params.get("token") or "").strip()
    if not is_valid_public_token(token):
        return err_("Token ungueltig", 400)
    items = list(table_("interessenten").query_entities("exposeToken eq @t", parameters={"t": token}))
    if not items:
        return err_("Token ungueltig", 404)
    i = dict(items[0])
    try:
        t = dict(table_("targets").get_entity("target", i.get("targetId", "")))
    except Exception:
        return err_("Target nicht gefunden", 404)
    expose_data = {}
    try: expose_data = json.loads(t.get("exposeJson", "{}") or "{}")
    except: expose_data = {}
    expose_data["mbNr"] = t.get("mbNr", "")
    try:
        pdf_bytes = _render_expose_pdf_bytes(expose_data)
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)
    return pdf_response(pdf_bytes, f'Expose_{t.get("mbNr","")}.pdf')


@app.route(route="nda-public-send-code", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def nda_public_send_code(req: func.HttpRequest) -> func.HttpResponse:
    """Public: 6-stelligen Bestätigungscode an die hinterlegte E-Mail schicken (vor Online-Signatur)."""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    token = (body.get("token") or "").strip()
    if not is_valid_public_token(token):
        return err_("Token ungueltig", 400)
    items = list(table_("interessenten").query_entities("exposeToken eq @t", parameters={"t": token}))
    if not items:
        return err_("Token ungültig", 404)
    i = dict(items[0])
    if i.get("ndaStatus") == "unterzeichnet":
        return err_("NDA bereits unterzeichnet", 400)
    # Code + Salt + Hash + Timestamp am Interessent speichern
    code = f"{secrets.randbelow(1000000):06d}"
    salt = i.get("ndaCodeSalt") or secrets.token_hex(16)
    i["ndaCodeSalt"] = salt
    i["ndaCodeHash"] = _hash_code_sig(code, salt)
    i["ndaCodeSentAt"] = datetime.utcnow().isoformat()
    try: table_("interessenten").update_entity(i)
    except Exception as ex: return err_(f"Speichern fehlgeschlagen: {ex}", 500)
    if not ACS_CONN:
        return err_("E-Mail-Service nicht konfiguriert", 500)
    try:
        from azure.communication.email import EmailClient
        client = EmailClient.from_connection_string(ACS_CONN)
        try:
            t = dict(table_("targets").get_entity("target", i.get("targetId", "")))
            mb_nr = t.get("mbNr", "")
        except Exception:
            mb_nr = ""
        html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a">
<p>Hallo {_first_name(i.get('name')) or i.get('firma') or ''},</p>
<p>Dein Bestätigungscode für die Online-Unterzeichnung des NDAs zu Projekt <strong>{mb_nr}</strong> lautet:</p>
<p style="font-size:28px;font-weight:700;letter-spacing:6px;background:#fff7ed;padding:14px 22px;border-radius:10px;display:inline-block;color:#FF6F00">{code}</p>
<p>Der Code ist {SIGNATURE_CODE_EXPIRY_MIN} Minuten gültig.</p>
<p>Bitte gib ihn im Browser ein, um Deine elektronische Signatur abzuschließen.</p>
<p style="color:#666;font-size:11px;margin-top:18px">Wenn Du diese Anfrage nicht gestartet hast, ignoriere diese E-Mail.</p>
</body></html>"""
        client.begin_send({
            "senderAddress": ACS_SENDER,
            "recipients": {"to": [{"address": i.get("email", "")}]},
            "content": {"subject": f"Bestätigungscode für NDA-Unterzeichnung – Projekt {mb_nr}", "plainText": f"Code: {code}", "html": html},
        })
    except Exception as ex:
        return err_(f"Mailversand fehlgeschlagen: {ex}", 500)
    return ok_({"ok": True, "email": i.get("email", "")})


@app.route(route="nda-public-sign", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def nda_public_sign(req: func.HttpRequest) -> func.HttpResponse:
    """Public: Interessent signiert NDA online via Canvas.
    Body: { token, signatureDataUrl, code }"""
    if req.method == "OPTIONS":
        return opt_()
    body = req.get_json() or {}
    token = (body.get("token") or "").strip()
    sig_data = body.get("signatureDataUrl", "")
    code = (body.get("code") or "").strip()
    daten = body.get("interessentenDaten") or {}
    if not (sig_data and code):
        return err_("signatureDataUrl und code erforderlich", 400)
    if not is_valid_public_token(token):
        return err_("Token ungueltig", 400)
    items = list(table_("interessenten").query_entities("exposeToken eq @t", parameters={"t": token}))
    if not items:
        return err_("Token ungültig", 404)
    i = dict(items[0])
    # Interessenten-Stammdaten aus dem Modal uebernehmen (ueberschreibt evtl. leere Felder)
    if daten:
        for src, dst in [("firma","firma"),("vertreten","name"),("strasse","strasse"),
                          ("plz","plz"),("ort","ort"),("email","email")]:
            v = (daten.get(src) or "").strip()
            if v: i[dst] = v
    # Code prüfen (Salt + Hash + Ablaufzeit)
    salt = i.get("ndaCodeSalt", "")
    expected = i.get("ndaCodeHash", "")
    sent_at = i.get("ndaCodeSentAt", "")
    if not (salt and expected and sent_at):
        return err_("Bitte zuerst einen Bestätigungscode anfordern.", 400)
    if _hash_code_sig(code, salt) != expected:
        return err_("Code falsch", 400)
    try:
        sent_dt = datetime.fromisoformat(sent_at)
        if (datetime.utcnow() - sent_dt).total_seconds() > SIGNATURE_CODE_EXPIRY_MIN * 60:
            return err_("Code abgelaufen – bitte neuen anfordern", 400)
    except Exception:
        return err_("Code-Validierung fehlgeschlagen", 400)
    target_id = i.get("targetId", "")
    try:
        t = dict(table_("targets").get_entity("target", target_id))
    except Exception:
        return err_("Target nicht gefunden", 404)
    # PDF generieren
    form = _build_nda_form_for_interessent(i, t)
    try:
        unsigned_pdf = _render_nda_pdf_bytes(form, "investor")
    except Exception as ex:
        return err_(f"NDA-PDF fehlgeschlagen: {ex}", 500)
    # Signatur dekodieren
    try:
        if sig_data.startswith("data:"):
            sig_data = sig_data.split(",", 1)[1]
        sig_bytes = base64.b64decode(sig_data)
    except Exception:
        return err_("Signatur ungueltig", 400)
    # Audit-Trail
    ip = req.headers.get("X-Forwarded-For", "").split(",")[0].strip() or req.headers.get("Client-IP", "")
    audit = {
        "email": i.get("email", ""),
        "signed_at": datetime.utcnow().isoformat(),
        "ip": ip,
        "user_agent": req.headers.get("User-Agent", "")[:200],
        "code_hash": expected,  # Code-Verifizierung im Audit-Trail
    }
    try:
        signed_pdf = _embed_signature_in_pdf(unsigned_pdf, sig_bytes, i.get("name") or i.get("firma", ""), audit,
                                              anchor_keywords=["Unterschrift Investor", "Unterschrift"])
    except Exception as ex:
        return err_(f"Signatur-Embedding fehlgeschlagen: {ex}", 500)
    # Code invalidieren nach erfolgreicher Signatur
    i["ndaCodeHash"] = ""
    i["ndaCodeSalt"] = ""
    # Blob speichern (vertraege-Container + zusaetzlich als Dokument im Target-Datenraum)
    blob_name = f"nda-interessent-{i['RowKey']}-signed.pdf"
    try:
        _blob_container_lazy("vertraege").upload_blob(blob_name, signed_pdf, overwrite=True)
    except Exception as ex:
        return err_(f"Upload fehlgeschlagen: {ex}", 500)
    # Auch in den NDA-Ordner des Targets ablegen (sichtbar in Akte → Dokumente → NDA)
    try:
        doc_blob_name = f"{target_id}/NDA/NDA_{i.get('firma') or i.get('name','interessent')}_{datetime.utcnow().strftime('%Y%m%d')}.pdf".replace(" ", "_")
        _blob_container_lazy("datenraum").upload_blob(doc_blob_name, signed_pdf, overwrite=True)
        doc_id = "nda-" + i["RowKey"]
        table_("dokumente").upsert_entity({
            "PartitionKey": target_id,
            "RowKey": doc_id,
            "fileName": f"NDA_{i.get('firma') or i.get('name','interessent')}_signiert.pdf",
            "ordner": "NDA",
            "blobName": doc_blob_name,
            "container": "datenraum",
            "size": len(signed_pdf),
            "contentType": "application/pdf",
            "uploadedAt": datetime.utcnow().isoformat(),
            "uploadedBy": i.get("email", ""),
            "quelle": "Online-Signatur Interessent",
        })
    except Exception as ex:
        logging.warning(f"NDA als Target-Dokument speichern fehlgeschlagen: {ex}")
    # Interessent aktualisieren
    i["ndaStatus"] = "unterzeichnet"
    i["ndaUploadedAt"] = audit["signed_at"]
    i["ndaBlob"] = blob_name
    i["ndaFileName"] = f"NDA_{t.get('mbNr','')}_signed.pdf"
    i["ndaSignedOnline"] = True
    i["ndaSigIp"] = audit["ip"]
    try: table_("interessenten").update_entity(i)
    except Exception: pass

    # Auto-Kontakt-Anlage: wenn die E-Mail noch nicht in der zentralen Kontaktliste ist,
    # neuen Kontakt anlegen (Firma/Name/Adresse aus NDA-Daten).
    try:
        new_email = (i.get("email") or "").strip().lower()
        if new_email:
            existiert = list(table_("kontakte").query_entities("email eq @e", parameters={"e": new_email}))
            if not existiert:
                kontakt_id = str(uuid.uuid4())
                table_("kontakte").create_entity({
                    "PartitionKey": "kontakt",
                    "RowKey": kontakt_id,
                    "firma": i.get("firma", ""),
                    "name": i.get("name", ""),
                    "email": i.get("email", ""),
                    "strasse": i.get("strasse", ""),
                    "plz": i.get("plz", ""),
                    "ort": i.get("ort", ""),
                    "quelle": f"NDA-Signatur Projekt {t.get('mbNr','')}",
                    "istKunde": False,
                    "createdAt": datetime.utcnow().isoformat(),
                    "createdVia": "nda-public-sign",
                })
                logging.info(f"Kontakt automatisch angelegt: {i.get('firma')} ({new_email})")
    except Exception as ex:
        logging.warning(f"Auto-Kontakt-Anlage fehlgeschlagen: {ex}")

    # Kein Target-Verlauf-Eintrag — Interessenten-Aktionen sieht der Mandant
    # im Interessenten-Tab, mibeca dort auch. Target-Verlauf ist ausschliesslich
    # fuer mibeca-Aktionen am Mandanten (z.B. Ausschreibung versendet).
    # Kontakt-Verlauf-Eintrag (CRM-Sicht):
    try:
        tc = table_("kontakte")
        rec_email_lc = (i.get("email") or "").strip().lower()
        if rec_email_lc:
            kontakt = None
            for k in tc.list_entities():
                if (k.get("email", "") or "").strip().lower() == rec_email_lc:
                    kontakt = dict(k); break
            if kontakt:
                try: kverlauf = json.loads(kontakt.get("verlaufJson") or "[]")
                except: kverlauf = []
                if not isinstance(kverlauf, list): kverlauf = []
                kverlauf.append({
                    "id": "kv" + str(int(datetime.utcnow().timestamp() * 1000)),
                    "typ": "wichtig",
                    "datum": datetime.utcnow().isoformat(),
                    "autor": i.get("name") or i.get("firma", ""),
                    "betreff": f"NDA signiert ({t.get('mbNr','')})",
                    "beschreibung": f"NDA online unterschrieben (IP: {audit['ip']}).",
                    "kontextTargetId": target_id,
                    "kontextMbNr": t.get('mbNr', ''),
                })
                kontakt["verlaufJson"] = json.dumps(kverlauf, ensure_ascii=False)
                tc.update_entity(kontakt)
    except Exception as ex:
        logging.warning(f"Kontakt-Verlauf-Eintrag (NDA) fehlgeschlagen: {ex}")
    # Bestaetigungs-Mail (selber Block wie /nda-upload)
    if ACS_CONN:
        try:
            landing = {}
            try: landing = json.loads(t.get("landingJson", "{}") or "{}")
            except: landing = {}
            termin_url = landing.get("terminBookingUrl") or DEFAULT_BOOKINGS_URL
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.6">
<p>Hallo {_first_name(i.get('name')) or i.get('firma') or ''},</p>
<p>vielen Dank für Dein unterschriebenes NDA zur Projektnummer <strong>{t.get('mbNr','')}</strong> &ndash; damit hast Du den ersten wichtigen Schritt gemacht!</p>
<p>Du hast nun Zugang zum Exposé und kannst direkt einen Termin mit unserer M&amp;A-Beraterin Jennifer Kaplan buchen:</p>
<p style="margin:24px 0"><a href="{termin_url}" style="background:#0088ba;color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:600">Termin jetzt buchen</a></p>
<p>Herzliche Grüße<br/>Dein M&amp;A-Team der Mike Bergmann Akademie</p>
</body></html>"""
            nda_attachment = {
                "name": f"NDA_{t.get('mbNr','')}_unterzeichnet.pdf",
                "contentType": "application/pdf",
                "contentInBase64": base64.b64encode(signed_pdf).decode(),
            }
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": i.get("email", "")}]},
                "content": {"subject": f"Dein unterschriebenes NDA – Projekt {t.get('mbNr','')}", "plainText": f"NDA siehe Anhang. Termin buchen: {termin_url}", "html": html},
                "attachments": [nda_attachment],
            })
            mibeca_mail = os.environ.get("MIBECA_NOTIFY_EMAIL", "jk@mike-bergmann.de")
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": mibeca_mail}]},
                "content": {"subject": f"[ITUKV] NDA online signiert zu {t.get('mbNr','')}", "plainText": f"{i.get('firma') or i.get('name')} hat NDA online unterschrieben.", "html": f"<p><strong>NDA online signiert</strong></p><p>Projekt: {t.get('mbNr','')}</p><p>Interessent: {i.get('firma','')} / {i.get('name','')} / {i.get('email','')}</p><p>Das unterschriebene NDA liegt im NDA-Ordner der Projekt-Akte und ist im Anhang.</p>"},
                "attachments": [nda_attachment],
            })
        except Exception as ex:
            logging.warning(f"NDA-Sign-Mail fehlgeschlagen: {ex}")
    return ok_({"ok": True})


# =========================================================================
# DOKUMENTE / DATENRAUM mit Azure Blob Storage
# =========================================================================

_EXPOSE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><title>Exposé {{ mbNr }}</title>
<style>
  @page {
    size: A4; margin: 24mm 18mm 24mm 18mm;
    @top-left { content: "Projekt {{ mbNr }} · mibeca GmbH"; font-size: 9pt; color: #888; }
    @bottom-right { content: "Seite " counter(page) " / " counter(pages); font-size: 9pt; color: #888; }
  }
  html, body { font-family: "Helvetica", "Arial", system-ui, sans-serif; font-size: 10.5pt; line-height: 1.55; color: #1f2937; }
  h1 { font-size: 22pt; font-weight: 700; color: #0e7c92; margin: 0; }
  .hl-line { color: #6b7280; font-size: 10pt; margin: 4pt 0 18pt 0; padding-bottom: 8pt; border-bottom: 1pt solid #e5e7eb; }
  .headline-box { background: linear-gradient(to right, #0e7c92, #0a9aaf); color: white; padding: 18pt 22pt; border-radius: 6pt; margin-bottom: 18pt; }
  .headline-box h2 { font-size: 14pt; margin: 0 0 6pt 0; font-weight: 700; }
  .headline-box p { margin: 0; opacity: 0.95; font-size: 11pt; }
  .section { display: flex; gap: 16pt; margin-bottom: 14pt; page-break-inside: avoid; }
  .section-label { width: 130pt; flex-shrink: 0; font-weight: 700; color: #0e7c92; font-size: 10.5pt; }
  .section-body { flex: 1; }
  .section-body p { margin: 0 0 6pt 0; text-align: justify; white-space: pre-wrap; }
  .section-body ul { margin: 4pt 0; padding-left: 16pt; }
  table { width: 100%; border-collapse: collapse; margin: 6pt 0; font-size: 9.5pt; }
  th, td { padding: 4pt 6pt; text-align: left; border-bottom: 1pt solid #e5e7eb; }
  th { background: #f9fafb; color: #0e7c92; font-weight: 700; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  .footer-note { font-size: 9pt; color: #6b7280; margin-top: 18pt; padding-top: 10pt; border-top: 1pt solid #e5e7eb; }
</style></head><body>

<h1>Unternehmensexposé</h1>
<p class="hl-line">Projektnummer: <strong>{{ mbNr }}</strong> · Stand: {{ stand }}</p>

<div class="headline-box">
  <h2>{{ headline }}</h2>
  <p>{{ subheadline }}</p>
</div>

{% for s in sektionen %}
{% if s.body %}
<div class="section">
  <div class="section-label">{{ s.label }}</div>
  <div class="section-body"><p>{{ s.body }}</p></div>
</div>
{% endif %}
{% endfor %}

{% if finanzen %}
<div class="section">
  <div class="section-label">Umsätze, Erträge</div>
  <div class="section-body">
    <p>{{ finanzen.einleitung or "" }}</p>
    {% if finanzen.jahre %}
    <table>
      <thead>
        <tr><th>Position</th>{% for j in finanzen.jahre %}<th class="num">{{ j }}</th>{% endfor %}</tr>
      </thead>
      <tbody>
        {% for row in finanzen.rows %}
        <tr><td>{{ row.label }}</td>{% for v in row.werte %}<td class="num">{{ v }}</td>{% endfor %}</tr>
        {% endfor %}
      </tbody>
    </table>
    {% endif %}
  </div>
</div>
{% endif %}

<p class="footer-note">Dieses Exposé ist vertraulich und ausschließlich zur Information vorgesehener Empfänger bestimmt. Eine Weitergabe an Dritte ist ohne ausdrückliche Zustimmung der mibeca GmbH untersagt.</p>

</body></html>"""


def _render_expose_pdf_bytes(data):
    from jinja2 import Template
    from weasyprint import HTML
    html = Template(_EXPOSE_HTML_TEMPLATE).render(**data)
    return HTML(string=html, base_url="/").write_pdf()


_LOI_HTML_TEMPLATE = """<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<style>
  @page { size: A4 landscape; margin: 18mm 14mm; }
  html, body { font-family: "Helvetica", Arial, sans-serif; font-size: 9.5pt; color: #1f2937; }
  h1 { font-size: 18pt; color: #0088ba; margin: 0 0 4pt 0; }
  .meta { color: #6b7280; font-size: 10pt; margin: 0 0 16pt 0; border-bottom: 1pt solid #e5e7eb; padding-bottom: 8pt; }
  .meta strong { color: #1f2937; }
  table { width: 100%; border-collapse: collapse; }
  th { background: #f3f4f6; color: #0088ba; font-weight: 700; padding: 6pt 5pt; font-size: 9pt; text-align: left; border: 1pt solid #d1d5db; }
  th.einigung { background: #e0f2fb; }
  td { padding: 6pt 5pt; border: 1pt solid #e5e7eb; vertical-align: top; }
  td.einigung { background: #f0f9ff; font-weight: 600; }
  td.final-yes { background: #dcfce7; color: #166534; font-weight: 700; text-align: center; }
  td.final-no { background: #fef3c7; color: #92400e; text-align: center; font-size: 8pt; }
  .footer-stats { margin-top: 14pt; font-size: 9pt; color: #6b7280; text-align: right; }
</style></head><body>
<h1>LOI · Finale Verhandlung</h1>
<p class="meta">
  Projekt: <strong>{{ mbNr }}</strong>  ·  Datum: <strong>{{ datum }}</strong><br/>
  Käufer: <strong>{{ kaeufer or '—' }}</strong>  ·  Verkäufer: <strong>{{ verkaeufer or '—' }}</strong>
</p>
<table>
<thead><tr>
  <th style="width:18%">LOI-Punkt</th>
  <th style="width:15%">Angebot Verkäufer</th>
  <th style="width:15%">Angebot Käufer</th>
  <th class="einigung" style="width:18%">Einigung</th>
  <th style="width:24%">Erläuterung</th>
  <th style="width:10%">Status</th>
</tr></thead>
<tbody>
{% for p in punkte %}
<tr>
  <td><strong>{{ p.punkt }}</strong></td>
  <td>{{ p.angebotVerkaeufer or '' }}</td>
  <td>{{ p.angebotKaeufer or '' }}</td>
  <td class="einigung">{{ p.einigung or '' }}</td>
  <td>{{ p.erlaeuterung or '' }}</td>
  {% if p.final %}<td class="final-yes">final</td>{% else %}<td class="final-no">offen</td>{% endif %}
</tr>
{% endfor %}
</tbody>
</table>
<div class="footer-stats">
  {{ punkte|length }} Punkte gesamt · {{ punkte|selectattr('final')|list|length }} final verhandelt · {{ punkte|rejectattr('final')|list|length }} noch offen
</div>
</body></html>"""


@app.route(route="loi-pdf", methods=["POST", "OPTIONS"])
def loi_pdf(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    try:
        from jinja2 import Template
        from weasyprint import HTML
        html = Template(_LOI_HTML_TEMPLATE).render(
            mbNr=body.get("mbNr", ""),
            datum=body.get("datum", ""),
            kaeufer=body.get("kaeufer", ""),
            verkaeufer=body.get("verkaeufer", ""),
            punkte=body.get("punkte", []),
        )
        pdf_bytes = HTML(string=html, base_url="/").write_pdf()
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)
    return pdf_response(pdf_bytes, f'LOI_{body.get("mbNr","")}.pdf')


@app.route(route="expose-pdf", methods=["POST", "OPTIONS"])
def expose_pdf(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    try:
        pdf_bytes = _render_expose_pdf_bytes(body)
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)
    return pdf_response(pdf_bytes, f'Expose_{body.get("mbNr","")}.pdf')


@app.route(route="status-report-pdf", methods=["POST", "OPTIONS"])
def status_report_pdf(req: func.HttpRequest) -> func.HttpResponse:
    """Generiert einen Status-Bericht als PDF fuer einen Verkaeufer.
    Inhalt: Stammdaten, aktuelle Phase, abgeschlossene + offene Aufgaben,
    juengste Verlauf-Eintraege, anstehende Termine."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    tid = (body.get("targetId") or "").strip()
    if not tid:
        return err_("targetId erforderlich", 400)
    if p.get("role") != "admin" and p.get("targetId") != tid:
        return err_("Nicht autorisiert", 403)
    try:
        t = dict(table_("targets").get_entity("target", tid))
    except Exception:
        return err_("Target nicht gefunden", 404)

    # PDF generieren via Helper (auch von Monthly-Cron genutzt)
    try:
        pdf_bytes = _build_status_report_pdf(t)
    except Exception as ex:
        return err_(f"PDF-Erstellung fehlgeschlagen: {ex}", 500)
    filename = f"Statusbericht_{(t.get('mbNr','') or 'mandat')}_{datetime.utcnow().date().isoformat()}.pdf"
    return pdf_response(pdf_bytes, filename)



@app.route(route="dokument-upload-url", methods=["POST", "OPTIONS"])
def dokument_upload_url(req: func.HttpRequest) -> func.HttpResponse:
    """Generiert SAS-URL für direkten Blob-Upload (auch Videos, beliebige Groesse)."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    ordner = (body.get("ordner") or "Sonstiges").strip()
    file_name = (body.get("fileName") or "datei").strip()
    content_type = body.get("contentType", "application/octet-stream")
    if not target_id:
        return err_("targetId erforderlich", 400)
    if p.get("role") == "target":
        if p.get("targetId") and p.get("targetId") != target_id:
            return err_("Nicht autorisiert", 403)
    # Path-Traversal-Schutz: keine Slashes/Backslashes/Punkt-Sequenzen in
    # ordner und fileName erlauben (sonst koennte ein Angreifer in fremde Container schreiben)
    def _sanitize_path_segment(s, default):
        if not s:
            return default
        # Entferne Pfad-Trenner und Punkt-Sequenzen
        s = s.replace("\\", "_").replace("/", "_")
        while ".." in s:
            s = s.replace("..", "_")
        # Auf druckbare Zeichen + Umlaute begrenzen
        s = "".join(c for c in s if c.isprintable())
        return s.strip() or default
    ordner = _sanitize_path_segment(ordner, "Sonstiges")
    file_name = _sanitize_path_segment(file_name, "datei")
    # Target-Id muss UUID-Format haben (verhindert Container-Sprünge)
    if not all(c.isalnum() or c == "-" for c in target_id):
        return err_("Ungueltige targetId", 400)
    from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
    svc = BlobServiceClient.from_connection_string(TABLE_CONN)
    try: svc.create_container("datenraum")
    except Exception: pass
    blob_name = f"{target_id}/{ordner}/{uuid.uuid4()}_{file_name}"
    sas = generate_blob_sas(
        account_name=svc.account_name, container_name="datenraum", blob_name=blob_name,
        account_key=svc.credential.account_key,
        permission=BlobSasPermissions(create=True, write=True),
        expiry=datetime.utcnow() + timedelta(minutes=15),
    )
    return ok_({
        "uploadUrl": f"https://{svc.account_name}.blob.core.windows.net/datenraum/{blob_name}?{sas}",
        "blobName": blob_name,
    })


@app.route(route="dokument-stream-url", methods=["GET", "POST", "OPTIONS"])
def dokument_stream_url(req: func.HttpRequest) -> func.HttpResponse:
    """Generiert eine kurzlebige SAS-URL fuer direktes Browser-Streaming
    (Videos, große PDFs). Liefert URL inkl. content-type + inline-Disposition,
    damit <video src=...>/<iframe src=...> direkt streamen koennen mit
    Range-Requests + Seeking."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    target_id = req.params.get("targetId", "") or ((req.get_json() or {}).get("targetId", "") if req.method == "POST" else "")
    doc_id = req.params.get("id", "") or ((req.get_json() or {}).get("id", "") if req.method == "POST" else "")
    if not (target_id and doc_id):
        return err_("targetId + id erforderlich", 400)
    if p.get("role") == "target":
        if p.get("targetId") and p.get("targetId") != target_id:
            return err_("Nicht autorisiert", 403)
    if p.get("role") != "admin" and target_id and p.get("targetId") != target_id:
        return err_("Nicht autorisiert", 403)
    try:
        ent = dict(table_("dokumente").get_entity(target_id, doc_id))
    except Exception:
        return err_("Dokument nicht gefunden", 404)
    # NDAs sind nur fuer Admin (Datenschutz)
    if ent.get("ordner") == "NDA" and p.get("role") != "admin":
        return err_("Nicht autorisiert", 403)
    file_name = ent.get("fileName", "file") or "file"
    ct = ent.get("contentType") or ""
    if not ct or ct == "application/octet-stream":
        ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
        ct = {
            "pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg",
            "jpeg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml",
            "webp": "image/webp", "mp4": "video/mp4", "mov": "video/quicktime",
            "webm": "video/webm", "mp3": "audio/mpeg", "wav": "audio/wav",
            "m4a": "audio/mp4",
        }.get(ext, "application/octet-stream")
    from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
    svc = BlobServiceClient.from_connection_string(TABLE_CONN)
    sas = generate_blob_sas(
        account_name=svc.account_name, container_name="datenraum",
        blob_name=ent["blobName"], account_key=svc.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=10),
        content_type=ct,
        content_disposition=f'inline; filename="{file_name}"',
    )
    return ok_({
        "streamUrl": f"https://{svc.account_name}.blob.core.windows.net/datenraum/{ent['blobName']}?{sas}",
        "contentType": ct, "fileName": file_name,
    })


@app.route(route="dokument-register", methods=["POST", "OPTIONS"])
def dokument_register(req: func.HttpRequest) -> func.HttpResponse:
    """Nach SAS-Upload: Metadaten in Tabelle anlegen."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    target_id = body.get("targetId", "")
    if not (target_id and body.get("blobName") and body.get("fileName")):
        return err_("targetId, blobName, fileName erforderlich", 400)
    if p.get("role") == "target":
        if p.get("targetId") and p.get("targetId") != target_id:
            return err_("Nicht autorisiert", 403)
    doc_id = str(uuid.uuid4())
    entity = {
        "PartitionKey": target_id, "RowKey": doc_id,
        "ordner": body.get("ordner", "Sonstiges"),
        "fileName": body.get("fileName"),
        "blobName": body.get("blobName"),
        "contentType": body.get("contentType", "application/octet-stream"),
        "size": int(body.get("size") or 0),
        "uploadedBy": p.get("name", "") or p.get("email", ""),
        "uploadedByRole": p.get("role", ""),
        "uploadedAt": datetime.utcnow().isoformat(),
    }
    table_("dokumente").create_entity(entity)
    return ok_({"id": doc_id, "fileName": entity["fileName"], "ordner": entity["ordner"], "size": entity["size"], "uploadedAt": entity["uploadedAt"], "uploadedBy": entity["uploadedBy"]}, 201)


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
        items = [dict(d) for d in table_("dokumente").query_entities("PartitionKey eq @pk", parameters={"pk": target_id})]
    except Exception:
        items = []
    # NDAs der Interessenten sind nur fuer Admins einsehbar (Datenschutz)
    if p.get("role") != "admin":
        items = [d for d in items if d.get("ordner") != "NDA"]
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
    # Content-Type: bevorzugt aus Entity, sonst aus Dateiname ableiten
    file_name = ent.get("fileName", "file") or "file"
    ct = ent.get("contentType") or ""
    if not ct or ct == "application/octet-stream":
        ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
        ct = {
            "pdf": "application/pdf",
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif",
            "svg": "image/svg+xml", "webp": "image/webp",
            "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
            "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
            "txt": "text/plain; charset=utf-8", "csv": "text/csv; charset=utf-8",
            "json": "application/json", "xml": "application/xml",
        }.get(ext, "application/octet-stream")
    # Disposition: "inline" fuer Browser-darstellbare Typen, "attachment" sonst
    inline_types = ("application/pdf", "image/", "video/", "audio/", "text/")
    disp = "inline" if any(ct.startswith(t) for t in inline_types) else "attachment"
    return func.HttpResponse(data, status_code=200,
                             mimetype=ct,
                             headers={**CORS, "Content-Disposition": f'{disp}; filename="{file_name}"'})


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


# =========================================================================
# DASHBOARD-ÜBERSICHT: Aktivität + "Wartet auf mich"
# =========================================================================

@app.route(route="dashboard-uebersicht", methods=["GET", "OPTIONS"])
def dashboard_uebersicht(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert Aktivitaets-Feed + 'Wartet auf mich' für Admin-Übersicht."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    user = _get_user_full(p.get("id")) or {}
    last_seen_map = {}
    try: last_seen_map = json.loads(user.get("lastSeenVerlauf", "{}") or "{}")
    except Exception: last_seen_map = {}

    feed = []  # alle Verlauf-Eintraege über alle Targets
    wartet = {
        "vertragsGegenzeichnung": [],   # Vertraege wo Target signiert hat
        "ndaReview": [],                # Interessenten mit NDA-Upload
        "ungelesen": [],                # Targets mit ungelesenen Eintraegen
        "wiedervorlage": [],            # Targets mit faelliger Wiedervorlage heute/überfaellig
        "pressefreigabe": [],           # Pressetext wartet auf Kunden-Freigabe oder mibeca-Aktion
        "fragebogenZuPruefen": [],      # Verkäufer hat Fragebogen abgegeben, mibeca muss auswerten
        "exposeKorrekturwunsch": [],    # Verkäufer hat Korrekturwunsch zum Exposé
        "exposeFreigabeAusstehend": [], # Exposé wurde an Kunden gesendet, wartet auf seine Freigabe
        "mandateLaufenAus": [],         # Mandat laeuft in <=60 Tagen aus oder ist abgelaufen
    }
    termine_anstehend = []  # alle Termine aus termineJson aller Targets (ueberfaellig + naechste 14 Tage)

    today = datetime.utcnow().date().isoformat()
    try:
        targets = [dict(t) for t in table_("targets").list_entities()]
    except Exception:
        targets = []

    for t in targets:
        tid = t.get("RowKey", "")
        mb_nr = t.get("mbNr", "")
        firma = t.get("verkaueferName", "") or t.get("firma", "")
        try: verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
        except Exception: verlauf = []
        # Feed — alle Eintraege sammeln, am Ende global nach Datum sortieren + auf 30 begrenzen
        for e in verlauf:
            feed.append({
                "targetId": tid, "mbNr": mb_nr, "firma": firma,
                "id": e.get("id", ""), "typ": e.get("typ", ""),
                "datum": e.get("datum", ""), "autor": e.get("autor", ""),
                "betreff": e.get("betreff", ""), "beschreibung": (e.get("beschreibung") or "")[:200],
            })
        # Ungelesen — auch Alt-Eintraege ohne createdBy korrekt per Autor-Name zuordnen
        ls = last_seen_map.get(tid, "1970-01-01T00:00:00")
        my_id_o = p.get("id", "")
        my_name_o = (p.get("name", "") or "").strip().lower()
        unread = [e for e in verlauf
                  if (e.get("datum", "") or "") > ls
                  and e.get("createdBy", "") != my_id_o
                  and (my_name_o == "" or (e.get("autor", "") or "").strip().lower() != my_name_o)]
        if unread:
            wartet["ungelesen"].append({"targetId": tid, "mbNr": mb_nr, "firma": firma, "anzahl": len(unread)})
        # Vertrag zur Gegenzeichnung
        try:
            v = json.loads(t.get("vertragJson", "{}") or "{}")
            if v.get("signiertAm") and not v.get("gegengezeichnetAm"):
                wartet["vertragsGegenzeichnung"].append({"targetId": tid, "mbNr": mb_nr, "firma": firma, "signiertAm": v.get("signiertAm", "")})
        except Exception: pass
        # Pressetext
        try:
            pr = json.loads(t.get("presseJson", "{}") or "{}")
            if pr.get("freigabeStatus") == "aenderung_gewuenscht":
                wartet["pressefreigabe"].append({"targetId": tid, "mbNr": mb_nr, "firma": firma, "kommentar": pr.get("freigabeKommentar", "")})
        except Exception: pass
        # Wiedervorlage
        wv = t.get("wiedervorlage", "")
        if wv and wv <= today:
            wartet["wiedervorlage"].append({"targetId": tid, "mbNr": mb_nr, "firma": firma, "datum": wv})
        # Termine: alles aus termineJson, was in den naechsten 14 Tagen liegt oder ueberfaellig ist
        try:
            termine_list = json.loads(t.get("termineJson", "[]") or "[]")
        except Exception:
            termine_list = []
        for tm in termine_list:
            datum = tm.get("datum", "")
            if not datum:
                continue
            try:
                d = datetime.fromisoformat(datum[:10]).date()
            except Exception:
                continue
            tage = (d - datetime.utcnow().date()).days
            if tm.get("erledigt"):
                continue
            if tage <= 14:
                termine_anstehend.append({
                    "targetId": tid, "mbNr": mb_nr, "firma": firma,
                    "id": tm.get("id", ""),
                    "datum": datum,
                    "titel": tm.get("titel", ""),
                    "typ": tm.get("typ", "sonstiges"),
                    "tageBisDatum": tage,
                    "ueberfaellig": tage < 0,
                })
        # Mandatslaufzeit: warnen wenn <=60 Tage bis Ende
        try:
            mandat_start = t.get("mandatStart", "") or ""
            mandat_monate = int(t.get("mandatLaufzeitMonate", 0) or 0)
            mandat_status = (t.get("status") or "").lower()
            if mandat_start and mandat_monate > 0 and mandat_status not in ("verkauft", "abgebrochen"):
                start_dt = datetime.fromisoformat(mandat_start[:10])
                ende_dt = start_dt + timedelta(days=mandat_monate * 30)  # naeherungsweise
                tage_bis_ende = (ende_dt.date() - datetime.utcnow().date()).days
                if tage_bis_ende <= 60:
                    wartet["mandateLaufenAus"].append({
                        "targetId": tid, "mbNr": mb_nr, "firma": firma,
                        "endeAm": ende_dt.date().isoformat(),
                        "tageBisEnde": tage_bis_ende,
                        "abgelaufen": tage_bis_ende < 0,
                    })
        except Exception:
            pass
        # Fragebogen abgegeben → mibeca muss auswerten (solange noch kein Exposé)
        if t.get("fragebogenStatus") == "abgegeben":
            try:
                ej = json.loads(t.get("exposeJson", "{}") or "{}")
                expose_status = ej.get("status", "")
            except Exception:
                expose_status = ""
            if expose_status in ("", "draft"):
                wartet["fragebogenZuPruefen"].append({
                    "targetId": tid, "mbNr": mb_nr, "firma": firma,
                    "abgegebenAm": t.get("fragebogenAbgegebenAm", ""),
                })
        # Exposé-Workflow
        try:
            ej = json.loads(t.get("exposeJson", "{}") or "{}")
            es = ej.get("status", "")
            if es == "changes_requested":
                wartet["exposeKorrekturwunsch"].append({"targetId": tid, "mbNr": mb_nr, "firma": firma})
            elif es == "awaiting_approval":
                wartet["exposeFreigabeAusstehend"].append({"targetId": tid, "mbNr": mb_nr, "firma": firma})
        except Exception: pass

    # Interessenten mit unterschriebenem NDA (zur Review)
    try:
        # Build target-id → mb-Nr Lookup
        target_mb = {t.get("RowKey", ""): t.get("mbNr", "") for t in targets}
        for i in table_("interessenten").list_entities():
            if i.get("ndaStatus") == "unterzeichnet" and not i.get("ndaReviewed"):
                tid = i.get("targetId", "")
                wartet["ndaReview"].append({
                    "targetId": tid,
                    "mbNr": target_mb.get(tid, ""),
                    "interessentId": i.get("RowKey", ""),
                    "firma": i.get("firma", "") or i.get("name", ""),
                    "uploadedAt": i.get("ndaUploadedAt", ""),
                    "ndaDocId": "nda-" + i.get("RowKey", ""),  # Verweis auf dokumente-Tabelle
                })
    except Exception: pass

    feed.sort(key=lambda x: x.get("datum", ""), reverse=True)
    termine_anstehend.sort(key=lambda x: x.get("datum", ""))
    return ok_({
        "feed": feed[:30],
        "wartet": wartet,
        "totalWartet": sum(len(v) for v in wartet.values()),
        "termineAnstehend": termine_anstehend,
    })


# ============================================================
# E-Mail-Vorlagen
# ============================================================

_SEED_VORLAGEN = [
    {
        "RowKey": "jenny-erstkontakt-2",
        "name": "Erstkontakt Interessent (mit Online-Formular, Du-Form)",
        "kategorie": "Interessenten-Akquise",
        "betreff": "Dein IT-Systemhaus zum Verkauf, Projekt {{mbNr}}",
        "body": "Moin XYZ (hier in Du-Form, was der Standard ist, da bekannter Seminarteilnehmer),\n\nDeine Chance: Du kannst ein IT-Systemhaus in Deiner Nähe kaufen – hier die Informationen dazu.\n\nEine einfache Möglichkeit, um Mitarbeiter und Kunden zu gewinnen.\n\n \n\nDu weißt ja, dass ich seit dem erfolgreichen Verkauf der Mehrheit von meinem Systemhaus Exabyters an die TELCAT, einer Tochter der Salzgitter AG, sehr aktiv darin bin, auch andere IT-Systemhäuser beim erfolgreichen Verkauf zu unterstützen. \n\nAndererseits unterstütze ich auch wachsende, innovative IT-Systemhäuser dabei, durch Zukäufe ein anorganisches Wachstum zu meistern… Kaufen geht schneller als selbst aufbauen – Dies gilt für Mitarbeiter genauso wie für Kundenbeziehungen. Allein 13 solcher Projekte habe ich im Jahr 2018 erfolgreich mitbegleitet.\n\nNun das spannende Angebot für Dich: Über den Link\n\n{{anfrageLink}} (HIER MUSS NOCH DER RICHTIGE LINK HIN)\n\nkommst Du an das Kurzexposé von einem IT-Systemhaus in Deiner Nähe. Hierfür hinterlegst Du bitte Deine vollständigen Kontaktdaten, über die wir Dich bei vertraulichen Rückfragen erreichen können. Das Exposé ist bewusst anonym gehalten, so dass keine Rückschlüsse auf den Verkäufer möglich sind. Es vermittelt Dir einen Eindruck über Zahlen, Daten und Fakten über das Unternehmen, und außerdem, was das Motiv des Verkäufers ist.\n\nBitte schau das Exposé durch und entscheide, ob Du mehr über diese besondere Möglichkeit erfahren möchtest. Wie gut passen Deine Kaufmotive zu den Verkaufsmotiven des Verkäufers?\n\nDu hast großes Interesse? Dann unterschreibst Du bitte den NDA auf den letzten Seiten und mailst mir diesen zurück.\n\nIm Anschluss stelle ich Dir dann einen Kontakt her zum Verkäufer. Ihr vereinbart dann ein erstes Kennenlerngespräch. In diesem Gespräch geht es darum, sich menschlich kennenzulernen. Es geht darum, dass Du die Hintergründe des Unternehmens kennenlernst und herausfinden kannst, ob das Unternehmen generell zu Dir passt. Wichtig: Im ersten Termin wird grundsätzlich nie über Kaufpreise gesprochen.\n\nBei allen Verkaufsmandaten verfolge ich immer strikt einen festen Prozess, wie er in der Mitte des Exposés beschrieben ist. Lass uns bitte diesen Prozess in dieser Form einhalten und ich verspreche Dir, dass wir innerhalb kurzer Zeit zu guten Ergebnissen kommen werden. Mein schnellster Firmenverkauf des letzten Jahres lief in gerade einmal 22 Tagen nach diesem Verfahren durch.\n\nÜbrigens: Kosten entstehen Dir durch meine Arbeit keine – meine Leistungen werden komplett vom Verkäufer bezahlt.\n\nJetzt bin ich gespannt auf Deine Antwort. Deine Fragen beantworte ich gern. Viel Spaß beim Lesen!\n\nBis bald!\n\n \n\nHier ein paar Presseberichte über meine Aktivitäten in diesem Bereich: https://mibeca.de/presse",
    },
    {
        "RowKey": "jenny-erstkontakt-2b",
        "name": "Erstkontakt mit Kurzexposé (kurze Variante, Du-Form)",
        "kategorie": "Interessenten-Akquise",
        "betreff": "Möglichkeit zum Unternehmenszukauf, Projekt {{mbNr}}",
        "body": "Moin XYZ (hier in Du-Form, was der Standard ist, da bekannter Seminarteilnehmer),\n\n \n\nDeine Chance: Du kannst ein IT-Unternehmen in Deiner Nähe kaufen – bevor wir in die öffentliche Ausschreibung gehen, möchte ich gezielt Dir die Chance geben einen Blick auf dieses Unternehmen zu werfen.\n\nWir können uns sehr gut vorstellen, dass dieses Unternehmen gut zu Deinem Unternehmen passt und somit eine einfache Möglichkeit für Dich darstellt, um Mitarbeiter und Kunden zu gewinnen. \n\nBist Du grundsätzlich offen für einen Unternehmenszukauf eines Teams von 16 Mitarbeitern aus deiner Nähe?\n\n \n\nDas Exposé ist bewusst anonym gehalten, so dass keine Rückschlüsse auf den Verkäufer möglich sind. Es vermittelt Dir einen Eindruck über Zahlen, Daten und Fakten über das Unternehmen, und außerdem, was das Motiv des Verkäufers ist.\n\nBitte schau das Exposé durch und entscheide, ob Du mehr über diese besondere Möglichkeit erfahren möchtest. Wie gut passen Deine Kaufmotive zu den Verkaufsmotiven des Verkäufers?\n\n \n\nWenn das IT-Unternehmen für Dich interessant ist, dann sende mir gerne die E-Mailadresse, an die ich dir über Zoho Sign eine Vertraulichkeitsvereinbarung (NDA) zusenden kann. Nachdem wir diese unterzeichnet zurückerhalten haben, können wir Dir nähere Informationen zu diesem IT-Unternehmen zukommen lassen und ich stelle Dir dann einen Kontakt zum Verkäufer her. Ihr vereinbart dann ein erstes Kennenlerngespräch. In diesem Gespräch geht es darum, sich menschlich kennenzulernen. Es geht darum, dass Du die Hintergründe des Unternehmens kennenlernst und herausfinden kannst, ob das Unternehmen generell zu Dir passt. Wichtig: Im ersten Termin wird grundsätzlich nie über Kaufpreise gesprochen.\n\n \n\nBei allen Verkaufsmandaten verfolge ich immer strikt einen festen Prozess. Lass uns bitte diesen Prozess in dieser Form einhalten und ich verspreche Dir, dass wir innerhalb kurzer Zeit zu guten Ergebnissen kommen werden.\n\nMein schnellster Firmenverkauf des letzten Jahres lief in gerade einmal 22 Tagen nach diesem Verfahren durch.\n\n \n\nÜbrigens: Kosten entstehen Dir durch meine Arbeit keine – meine Leistungen werden komplett vom Verkäufer bezahlt.\n\n \n\n \n\n \n\nJetzt bin ich gespannt auf Deine Antwort. Deine Fragen beantworte ich gern. Viel Spaß beim Lesen!\n\n \n\nBis bald!",
    },
    {
        "RowKey": "jenny-investor-nach-telefonat",
        "name": "Nach Telefonat mit Investor: Zusammenfassung",
        "kategorie": "Netzwerk",
        "betreff": "Nach unserem Telefonat - was wir machen",
        "body": "Moin XYZ (hier per Du, weil wir schon miteinander gesprochen haben)\n\n \n\nvielen Dank für das freundliche eben geführte Telefonat. \n\nSeit dem erfolgreichen Verkauf der Mehrheit von dem Systemhaus Exabyters an die TELCAT, einer Tochter der Salzgitter AG, ist die Mike Bergmann Akademie geboren und sehr aktiv darin, auch andere IT-Systemhäuser beim erfolgreichen Verkauf zu unterstützen. Andererseits unterstützt die Mike Bergmann Akademie auch wachsende, innovative IT-Systemhäuser dabei, durch Zukäufe ein anorganisches Wachstum zu meistern. Kaufen geht schneller als selbst aufbauen – Dies gilt für Mitarbeiter genauso wie für Kundenbeziehungen. In den letzten Jahren wurden dabei rund 40 Transaktionen von uns begleitet. \n\nAuch durch unser großes Netzwerk (über 4000 IT Unternehmen in Deutschland) finden wir sehr schnell verkaufsfähige Unternehmen, die euren Bedürfnissen entsprechen. \n\nBei allen Mandaten verfolgen wir einen festen Prozess. Wenn wir diesen Prozess einhalten versprechen wir Dir, dass wir innerhalb kurzer Zeit zu guten Ergebnissen kommen werden. \n\nIm angefügten Link kannst du eine Auswahl von Unternehmens(ver)käufe und Kundenerfolge nachlesen: \n\nPresse (mike-bergmann-akademie.de)\n\nIch freue mich auf deine Rückmeldung! \n\nMit freundlichen Grüßen",
    },
    {
        "RowKey": "jenny-erstkontakt-1a",
        "name": "Erstkontakt Interessent (Exposé im Anhang, Du-Form)",
        "kategorie": "Interessenten-Akquise",
        "betreff": "Ich biete Dir ein IT-Systemhaus zum Verkauf an - Kurzexposé {{mbNr}}",
        "body": "Moin XYZ (hier in Du-Form, was der Standard ist, da bekannter Seminarteilnehmer),\n\nDeine Chance: Du kannst ein IT-Systemhaus in Deiner Nähe kaufen – hier die Informationen dazu.\n\nEine einfache Möglichkeit, um Mitarbeiter und Kunden zu gewinnen.\n\n \n\nDu weißt ja, dass ich seit dem erfolgreichen Verkauf der Mehrheit von meinem Systemhaus Exabyters an die TELCAT, einer Tochter der Salzgitter AG, sehr aktiv darin bin, auch andere IT-Systemhäuser beim erfolgreichen Verkauf zu unterstützen. \n\nAndererseits unterstütze ich auch wachsende, innovative IT-Systemhäuser dabei, durch Zukäufe ein anorganisches Wachstum zu meistern… Kaufen geht schneller als selbst aufbauen – Dies gilt für Mitarbeiter genauso wie für Kundenbeziehungen. Allein 13 solcher Projekte habe ich im Jahr 2018 erfolgreich mitbegleitet.\n\nNun das spannende Angebot für Dich:\n\nIm Anhang findest Du ein Kurzexposé von einem IT-Systemhaus in Deiner Nähe. Das Exposé ist bewusst anonym gehalten, so dass keine Rückschlüsse auf den Verkäufer möglich sind. Es vermittelt Dir einen Eindruck über Zahlen, Daten und Fakten über das Unternehmen, und außerdem, was das Motiv des Verkäufers ist.\n\nBitte schau das Exposé durch und entscheide, ob Du mehr über diese besondere Möglichkeit erfahren möchtest. Wie gut passen Deine Kaufmotive zu den Verkaufsmotiven des Verkäufers?\n\nDu hast großes Interesse? Dann unterschreibst Du bitte den NDA auf den letzten Seiten und mailst mir diesen zurück.\n\nIm Anschluss stelle ich Dir dann einen Kontakt her zum Verkäufer. Ihr vereinbart dann ein erstes Kennenlerngespräch. In diesem Gespräch geht es darum, sich menschlich kennenzulernen. Es geht darum, dass Du die Hintergründe des Unternehmens kennenlernst und herausfinden kannst, ob das Unternehmen generell zu Dir passt. Wichtig: Im ersten Termin wird grundsätzlich nie über Kaufpreise gesprochen.\n\nBei allen Verkaufsmandaten verfolge ich immer strikt einen festen Prozess, wie er in der Mitte des Exposés beschrieben ist. Lass uns bitte diesen Prozess in dieser Form einhalten und ich verspreche Dir, dass wir innerhalb kurzer Zeit zu guten Ergebnissen kommen werden. Mein schnellster Firmenverkauf des letzten Jahres lief in gerade einmal 22 Tagen nach diesem Verfahren durch.\n\nÜbrigens: Kosten entstehen Dir durch meine Arbeit keine – meine Leistungen werden komplett vom Verkäufer bezahlt.\n\nJetzt bin ich gespannt auf Deine Antwort. Deine Fragen beantworte ich gern. Viel Spaß beim Lesen!\n\nBis bald!\n\n \n\nHier ein paar Presseberichte über meine Aktivitäten in diesem Bereich: https://mibeca.de/presse",
    },
    {
        "RowKey": "jenny-erstkontakt-2a",
        "name": "Erstkontakt vor öffentlicher Ausschreibung (Du-Form)",
        "kategorie": "Interessenten-Akquise",
        "betreff": "Diskretes Verkaufsangebot vor Ausschreibung, Projekt {{mbNr}}",
        "body": "Moin XYZ (hier in Du-Form, was der Standard ist, da bekannter Seminarteilnehmer),\n\nDeine Chance: Du kannst ein IT-Unternehmen in Deiner Nähe kaufen – bevor wir in die öffentliche Ausschreibung gehen, möchte ich gezielt Dir die Chance geben einen Blick auf dieses Unternehmen zu werfen. Wir können uns sehr gut vorstellen, dass dieses Unternehmen gut zu Deinem Unternehmen passt und somit eine einfache Möglichkeit für Dich darstellt, um Mitarbeiter und Kunden zu gewinnen. \n\nBist Du grundsätzlich offen für einen Unternehmenszukauf eines Teams von 16 Mitarbeitern aus deiner Nähe? Wenn das für Dich interessant ist, dann sende mir gerne die E-Mailadresse, an die ich dir über Zoho Sign eine Vertraulichkeitsvereinbarung (NDA) zusenden kann. Nachdem wir diese unterzeichnet zurückerhalten haben, können wir Dir nähere Informationen zu diesem IT-Unternehmen zukommen lassen in Form eines anonymen Exposés, so dass keine Rückschlüsse auf den Verkäufer möglich sind. Es vermittelt Dir einen Eindruck über Zahlen, Daten und Fakten über das Unternehmen, und außerdem, was das Motiv des Verkäufers ist.\n\nSollte dein Interesse geweckt sein, würde ich im Anschluss den Kontakt zum Verkäufer herstellen. \n\nWir vereinbaren dann ein erstes Kennenlerngespräch. In diesem Gespräch geht es darum, sich menschlich kennenzulernen. Es geht darum, dass Du die Hintergründe des Unternehmens kennenlernst und herausfinden kannst, ob das Unternehmen generell zu Dir passt. Wichtig: Im ersten Termin wird grundsätzlich nie über Kaufpreise gesprochen.\n\nLass uns bitte diesen Prozess in dieser Form einhalten und ich verspreche Dir, dass wir innerhalb kurzer Zeit zu guten Ergebnissen kommen werden. Mein schnellster Firmenverkauf des letzten Jahres lief in gerade einmal 22 Tagen nach diesem Verfahren durch.\n\nÜbrigens: Kosten entstehen Dir durch meine Arbeit keine – meine Leistungen werden komplett vom Verkäufer bezahlt.\n\n \n\nJetzt bin ich gespannt auf Deine Antwort. Deine Fragen beantworte ich gern.\n\nBis bald!",
    },
    {
        "RowKey": "jenny-nach-nda",
        "name": "Nach NDA-Rücksendung: Verkäufer-Kontakt herstellen",
        "kategorie": "Interessenten-Nachfass",
        "betreff": "Hier ist der Kontakt zum Verkäufer, Projekt {{mbNr}}",
        "body": "Moin XYZ (hier in Du-Form, was der Standard ist, da bekannter Seminarteilnehmer),\n\n \n\nvielen Dank für die Rücksendung des unterzeichneten NDAs. Es freut mich, dass Du an dem Unternehmen interessiert bist. Sicher hast Du schon Deine ganz eigene Story, wie Du das Unternehmen an Dein bestehendes IT-Systemhaus anbinden kannst.\n\n \n\nIn dieser Mail sende ich Dir die Kontaktdaten des Systemhauschefs zu.\n\n \n\nEr erwartet Deine Kontaktaufnahme per E-Mail zur Vereinbarung eines persönlichen Kennenlerntermins. Wichtig dabei: Wähle bitte zuerst den E-Mail Kontakt und rufe nicht über die Firmennummer an. Es ist absolut erforderlich, dass Die Mitarbeiter des Verkäufers davon nichts mitbekommen.\n\n \n\nBesonders wichtig beim Erstgespräch:\n\n \n\nIn diesem Gespräch geht es darum, sich menschlich kennenzulernen. Es geht darum, dass Du die Hintergründe des Unternehmens kennenlernst und herausfinden kannst, ob das Unternehmen generell zu Dir passt. Wichtig: Im ersten Termin wird grundsätzlich nie über Kaufpreise gesprochen.\n\n \n\nBei allen Verkaufsmandaten verfolge ich immer strikt einen festen Prozess, wie er in der Mitte des Exposés beschrieben ist. Lass uns bitte diesen Prozess in dieser Form einhalten und ich verspreche Dir, dass wir innerhalb kurzer Zeit zu guten Ergebnissen kommen werden. Mein schnellster Firmenverkauf des letzten Jahres lief in gerade einmal 22 Tagen nach diesem Verfahren durch.\n\n \n\nOft fordern Interessenten nach dem ersten Gespräch noch weitere Unterlagen vom Verkäufer an, die dieser dann gemeinsam mit mir für Dich aufbereitet.\n\n \n\nWenn Du Dir einen guten Eindruck vom Unternehmen verschaffen konntest, bitte ich Dich um Zusendung eines ersten indikativen Kaufangebotes an mich per E-Mail. Dieses ist nicht in Stein gemeißelt. Es geht darum, dass Du Dein Interesse in einer Zahl konkretisierst. Du könntest z.B. schreiben „Ich bin daran interessiert, das IT-Systemhaus zum 01.08.2020 komplett zu übernehmen mit allen Kunden und Mitarbeitern. Dafür bin ich bereit, XYZ TEUR zu investieren. Um mein Gebot zu festigen, benötige ich noch folgende Informationen ….“\n\n \n\nDa wir das Exposé an einen größeren Verteiler von IT Unternehmen im Umkreis von etwa 200km gesendet haben, warten der Verkäufer und ich nun die ersten indikativen Kaufgebote ab. In jedem Fall bekommst Du von uns eine klare Rückmeldung. Mit allen Interessenten, die ein faires Angebot vorlegen und die menschlich aus Sicht des Verkäufers passen, steigen wir dann in weitere Verhandlungen ein.\n\n \n\nDem Verkäufer geht es dabei nicht einfach um den höchsten Preis, sondern um ein schlüssiges Gesamtkonzept von Dir, was für ihn, seine Mitarbeiter und seine Kunden passen wird.\n\n \n\nHier die Kontaktdaten:\n\nUnternehmensname:\n\nGeschäftsführer\n\nE-Mail-Adresse\n\nInternetseite\n\nMobilnummer\n\n \n\nWichtig: Bitte rufe nicht über die Büronummer an, da die Mitarbeiter über den gesamten Vorgang zunächst nichts erfahren sollen.\n\n \n\nIch wünsche euch viel Erfolg beim ersten Gespräch. Bei Fragen komme ich gern auch bei einem weiteren Gespräch per Videokonferenz hinzu.\n\n \n\nBis bald!\n\nMike\n\nGuten Tag Herr XXXX,\n\nvielen Dank für die Rücksendung des unterzeichneten NDAs. Es freut mich, dass Sie an dem Unternehmen interessiert sind. Sicher haben Sie schon ihre ganz eigene Story, wie Sie das Unternehmen an ihr bestehendes IT-Systemhaus anbinden können.\n\nIn dieser Mail sende ich Ihnen die Kontaktdaten der Systemhauschefs zu.\n\nEr erwartet Ihre Kontaktaufnahme per E-Mail zur Vereinbarung eines persönlichen Kennenlerntermins. Wichtig dabei: Wählen Sie bitte zuerst den E-Mail Kontakt und rufen Sie nicht über die Firmennummer an. Es ist absolut erforderlich, dass die Mitarbeiter des Verkäufers davon nichts mitbekommen.\n\nBesonders wichtig beim Erstgespräch: \n\nIn diesem Gespräch geht es darum, sich menschlich kennenzulernen. Es geht darum, dass Sie die Hintergründe des Unternehmens kennenlernen und herausfinden können, ob das Unternehmen generell zu Ihnen passt. Wichtig: Im ersten Termin wird grundsätzlich nie über Kaufpreise gesprochen.\n\nBei allen Verkaufsmandaten verfolge ich immer strikt einen festen Prozess, wie er in der Mitte des Exposés beschrieben ist. Lassen Sie uns bitte diesen Prozess in dieser Form einhalten und ich verspreche Ihnen, dass wir innerhalb kurzer Zeit zu guten Ergebnissen kommen werden. Mein schnellster Firmenverkauf des letzten Jahres lief in gerade einmal 22 Tagen nach diesem Verfahren durch.\n\nOft fordern Interessenten nach dem ersten Gespräch noch weitere Unterlagen vom Verkäufer an, die dieser dann gemeinsam mit mir für Sie aufbereitet.\n\nWenn Sie sich einen guten Eindruck vom Unternehmen verschaffen konnten, bitte wir ich Sie um Zusendung eines ersten indikativen Kaufangebotes an mich per E-Mail. Dieses ist nicht in Stein gemeißelt. Es geht darum, dass Sie Ihr Interesse in einer Zahl konkretisieren. Sie könnten z.B. schreiben „Ich bin daran interessiert, das IT-Systemhaus zum 01.03.2020 komplett zu übernehmen mit allen Kunden und Mitarbeitern. Dafür bin ich bereit, XYZ TEUR zu investieren. Um mein Gebot zu festigen, benötige ich noch folgende Informationen ….“\n\n \n\nDa wir das Exposé an einen größeren Verteiler von IT Unternehmen im Umkreis von etwa 200km gesendet haben, warten die Verkäufer und ich nun die ersten indikativen Kaufgebote ab. In jedem Fall bekommen Sie von uns eine klare Rückmeldung. Mit allen Interessenten, die ein faires Angebot vorlegen und die menschlich aus Sicht der Verkäufer passen, steigen wir dann in weitere Verhandlungen ein.\n\nDem Verkäufer geht es dabei nicht einfach um den höchsten Preis, sondern um ein schlüssiges Gesamtkonzept von Ihnen, was für ihn, deren Mitarbeiter und deren Kunden passen wird.\n\nHier die Kontaktdaten:\n\nxxxx\n\nUnternehmensgründer: xxx \n\nE-Mail Adressen:\n\nMobilnummer xxxx\n\n \n\nWichtig: Bitte rufen Sie nicht über die Büronummer an, da die Mitarbeiter über den gesamten Vorgang zunächst nichts erfahren sollen.\n\nIch wünsche Ihnen viel Erfolg beim ersten Gespräch. Bei Fragen komme ich gern auch bei einem weiteren Gespräch per Videokonferenz hinzu.\n\nBis bald!",
    },
    {
        "RowKey": "jenny-nachfass-nda-fehlt",
        "name": "Nachfass: NDA noch nicht erhalten",
        "kategorie": "Interessenten-Nachfass",
        "betreff": "Firmenverkauf {{mbNr}}, noch kein NDA erhalten - bitte um Rückmeldung",
        "body": "Hallo XXXX,\n\nvor kurzem hattest Du mein Kontaktformular ausgefüllt und Dir das Exposé für das zu verkaufende Systemhaus heruntergeladen. Hier ist noch mal der Downloadlink: {{anfrageLink}}\n\nWie interessant ist dieses Angebot nun für Dich?\n\nWenn Du die Kontaktdaten der verkaufenden Unternehmer haben möchtest, benötige ich die letzten Seiten vom Exposé unterschrieben per E-Mail zurück als Bestätigung der Verschwiegenheitserklärung / NDA.\n\nSollte ich binnen 4 Werktagen auf meine Mail von Dir nichts mehr hören, verstehe ich dies so, dass Du kein weiteres Interesse an dem Unternehmen mehr hast. \n\nIch werde Dich dann aus dem Verteiler für diesen Unternehmensverkauf streichen.\n\nDie ersten Kontaktaufnahmen und Kennenlerngespräche zwischen den Verkäufern und Interessenten haben bereits stattgefunden, so dass der Zeitpunkt für Dich jetzt also ideal ist, um auch noch in den Prozess einsteigen zu können.\n\nIch freue mich auf Deine Antwort.\n\nHallo XXXX,\n\nvor kurzem hatten Sie mein Kontaktformular ausgefüllt und sich das Exposé für das zu verkaufende Systemhaus heruntergeladen. Hier ist noch mal der Downloadlink: {{anfrageLink}}\n\nWie interessant ist dieses Angebot nun für Sie?\n\nWenn Sie die Kontaktdaten des verkaufenden Unternehmers haben möchtest, benötige ich die letzten Seiten vom Exposé unterschrieben per E-Mail zurück als Bestätigung der Verschwiegenheitserklärung / NDA.\n\nSollte ich binnen 4 Werktagen auf meine Mail von Ihnen nichts mehr hören, verstehe ich dies so, dass Sie kein weiteres Interesse an dem Unternehmen mehr haben.\n\nIch werde Sie dann aus dem Verteiler für diesen Unternehmensverkauf streichen.\n\nDie ersten Kontaktaufnahmen und Kennenlerngespräche zwischen dem Verkäufern und Interessenten haben bereits stattgefunden, so dass der Zeitpunkt für Sie jetzt also ideal ist, um auch noch in den Prozess einsteigen zu können.\n\nIch freue mich auf Ihre Antwort.\n\nMike Bergmann",
    },
    {
        "RowKey": "jenny-nachfass-keine-reaktion",
        "name": "Nachfass: keine Reaktion auf Kurzexposé+NDA",
        "kategorie": "Interessenten-Nachfass",
        "betreff": "Meine E-Mail mit dem Kurzexposé zu {{mbNr}} - hattest Du diese erhalten?",
        "body": "Moin ,\n\nich hatte Dir vor ein paar Tagen eine E-Mail mit dem Kurzexposé eines IT-Systemhauses zugesandt, dessen Verkaufsauftrag ich erhalten habe.\n\nAllerdings habe ich auf meine E-Mail noch keine Antwort erhalten. Bin ich im Spamfilter gelandet oder hast Du kein Interesse?\n\nBitte gib mir eine kurze, klare Antwort dazu. Von zwei möglichen Interessenten, von Dir und einem weiteren, habe ich noch keinen unterschriebenen NDA zurückerhalten – mit allen weiteren Interessenten aus der Region (ca. 100km Umkreis) sind wir schon einige Schritte weiter, es werden schon Informationen ausgetauscht und Kennenlerntermine vereinbart. Es geht also zügig voran.\n\n \n\nAlso, wenn Du nach wie vor interessiert bist, durch den Zukauf eines anderen IT-Systemhauses zu wachsen, dann schau Dir das Kurzexposé an und sende mir bei Interesse den angehängten NDA unterschrieben per E-Mail zu.\n\nDas weitere Vorgehen folgt einem genau strukturierten und schlanken Prozess, es kann also schnell vorangehen. Solltest Du kein Interesse haben, bitte ich um eine kurze Absage.\n\n \n\nVielen Dank und bis bald!",
    },
    {
        "RowKey": "jenny-verkaeufer-wartet",
        "name": "Nachfass: Verkäufer wartet auf Terminvorschlag",
        "kategorie": "Interessenten-Nachfass",
        "betreff": "{{mbNr}} - der Verkäufer wartet noch auf Deinen Terminvorschlag",
        "body": "Hallo XYZ,\n\nbitte melde Dich zeitnah per E-Mail bei den Verkäufern des IT-Systemhauses – die Kontaktdaten hatte ich Dir bereits in der letzten Mail zugeschickt!\n\nAm besten sende ihnen gleich drei Terminvorschläge für ein Kennenlerntreffen oder ein Kennenlerntelefonat zu.\n\nHintergrund: Der Verkaufsprozess hat deutlich an Fahrt aufgenommen, die ersten Gespräche haben stattgefunden – und die ersten indikativen Kaufgebote liegen bereits schriftlich vor. Die Nachfrage ist tatsächlich groß und ich rechne damit, dass wir in Kürze mit den ersten Vertragsvorhandlungen mit Interessenten beginnen werden.\n\nWenn Du Dir selbst diese Chance auf den Zukauf eines IT-Systemhauses sichern willst, handle bitte schnell und vereinbare einen Kennenlerntermin!\n\nEs geht im ersten Kennenlernen darum:\n\ndie Verkäufer kennenzulernen (stimmt der „Nasen-Faktor“?) und\n\npasst die Story? Passen Deine Kaufmotive zu den Verkaufsmotiven des Verkäufers.\n\nÜber den Kaufpreis wird im ersten Kennenlerntermin grundsätzlich nicht gesprochen.\n\nVielen Dank und bis bald!\n\nMike Bergmann\n\n \n\nHallo Herr,\n\nbitte melden Sie zeitnah per E-Mail bei den Verkäufern des IT-Systemhauses – die Kontaktdaten hatte ich Ihnen bereits in der letzten Mail zugeschickt!\n\nAm besten senden Sie ihnen gleich drei Terminvorschläge für ein Kennenlerntreffen oder ein Kennenlerntelefonat zu.\n\nHintergrund: Der Verkaufsprozess hat deutlich an Fahrt aufgenommen, die ersten Gespräche haben stattgefunden – und die ersten indikativen Kaufgebote liegen bereits schriftlich vor. Die Nachfrage ist tatsächlich groß und ich rechne damit, dass wir in Kürze mit den ersten Vertragsvorhandlungen mit Interessenten beginnen werden.\n\nWenn Sie sich selbst diese Chance auf den Zukauf eines IT-Systemhauses sichern wollen, handeln Sie bitte schnell und vereinbaren einen Kennenlerntermin!\n\nEs geht im ersten Kennenlernen darum:\n\ndie Verkäufer kennenzulernen (stimmt der „Nasen-Faktor“?) und\n\npasst die Story? Passen Ihre Kaufmotive zu den Verkaufsmotiven des Verkäufers.\n\nÜber den Kaufpreis wird im ersten Kennenlerntermin grundsätzlich nicht gesprochen.\n\nVielen Dank und bis bald!\n\nMike Bergmann",
    },
    {
        "RowKey": "jenny-letzte-aufforderung-gebot",
        "name": "Letzte Aufforderung Kaufgebot",
        "kategorie": "Interessenten-Nachfass",
        "betreff": "{{mbNr}} - Frist für Kennenlerngespräch / Kaufgebot endet",
        "body": "Verkäufer NUR in BCC nehmen (nicht sichtbar)\n\nHallo XYZ,\n\nDu hattest ja Interesse am Kauf dieses Unternehmens bekundet und das Kurzexposé erhalten. Eine „TODO“ für mich und den Verkäufer bezüglich einer Terminvereinbarung oder der Nachforderung weiterer Unterlagen liegt mir momentan nicht vor. Oder habe ich etwas übersehen?\n\nWir sind im Prozess weit fortgeschritten und es liegen mehrere indikative Kaufgebote vor, mit denen wir jetzt in konkrete Verhandlungen einsteigen.\n\nWenn Du weiterhin am Kauf dieses Unternehmens interessiert bist, fordere ich Dich freundlich auf, per E-Mail mit dem Verkäufer in Kontakt zu treten, um ein persönliches oder telefonisches Kennenlernen zu vereinbaren. Im Gespräch kannst Du dann auch weitere Unterlagen anfordern.\n\nAlternativ kannst Du auch direkt ein indikatives Kaufgebot per E-Mail zuzusenden, wenn Dir alle wichtigen Informationen vorliegen.\n\n \n\nWir erwarten Deine Antwort bis zum\n\n20.08.2019, 18 Uhr.\n\n \n\nSollten wir bis dahin keinen Vorschlag zur Terminvereinbarung oder alternativ ein Gebot erhalten haben, interpretieren wir dies so, dass Du kein Interesse mehr an diesem Unternehmen hast. In diesem Fall bitte ich Dich, unverzüglich die Dir vorliegenden Unterlagen und Informationen über das Unternehmen zu löschen.\n\nVielen Dank!\n\nVerkäufer NUR in BCC nehmen (nicht sichtbar)\n\nHallo XYZ,\n\nSie hatten ja Interesse am Kauf dieses Unternehmens bekundet und das Kurzexposé erhalten. Eine „TODO“ für mich und den Verkäufer bezüglich einer Terminvereinbarung oder der Nachforderung weiterer Unterlagen liegt mir momentan nicht vor. Oder habe ich etwas übersehen?\n\nWir sind im Prozess weit fortgeschritten und es liegen mehrere indikative Kaufgebote vor, mit denen wir jetzt in konkrete Verhandlungen einsteigen.\n\nWenn Sie weiterhin am Kauf dieses Unternehmens interessiert sind, fordere ich Sie hiermit freundlich auf, per E-Mail mit dem Verkäufer in Kontakt zu treten, um ein persönliches oder telefonisches Kennenlernen zu vereinbaren. Im Gespräch können Sie dann auch weitere Unterlagen anfordern.\n\nAlternativ können Sie auch direkt ein indikatives Kaufgebot per E-Mail zuzusenden, wenn Ihnen alle wichtigen Informationen vorliegen.\n\n \n\nWir erwarten Ihre Antwort bis zum\n\n20.08.2019, 18 Uhr.\n\n \n\nSollten wir bis dahin keinen Vorschlag zur Terminvereinbarung oder alternativ ein Gebot erhalten haben, interpretieren wir dies so, dass Sie kein Interesse mehr an diesem Unternehmen haben. In diesem Fall bitte ich Sie, unverzüglich die Ihnen vorliegenden Unterlagen und Informationen über das Unternehmen zu löschen.\n\nVielen Dank!",
    },
    {
        "RowKey": "jenny-nach-kennenlernen-gebot",
        "name": "Nach Kennenlernen: indikatives Gebot erwartet",
        "kategorie": "Interessenten-Nachfass",
        "betreff": "{{mbNr}} - Kennenlernen stattgefunden, Kaufgebot benötigt",
        "body": "WICHTIG! ANLAGE INDIKATIVES KAUFGEBOT (EXCEL) MIT RICHTIGER PROJEKTNUMMER ANHÄNGEN\n\n \n\nHallo XXXX,\n\ndas erste Kennenlernen mit dem Unternehmen hat nun ja stattgefunden und von beiden Seiten besteht grundsätzliches Interesse – sehr schön!\n\nZum einen passt die zwischenmenschlichen Ebene als wichtige Voraussetzung.\n\nZum anderen passen Deine Kaufmotive und die Verkaufsmotive der Verkäufer gut zusammen.\n\nAls nächstes benötige ich von Dir ein erstes indikatives Kaufgebot innerhalb der nächsten Tage.\n\nWas bist Du bereit, für dieses Unternehmen zu investieren?\n\nDafür habe ich Dir eine Excel Datei als Vorlage beigelegt, so dass sich das Angebot gut strukturieren lässt (Du kannst auch gern ein freies Angebot formulieren).\n\n \n\nAuf die gleiche Art und Weise stehen wir auch mit den anderen Interessenten in Verbindung. Wir haben schon mehrere Kaufgebote vorliegen. So ergibt sich für die Verkäufer ein klares Bild, wie der Marktpreis von deren IT-Unternehmen eingeschätzt wird.\n\n \n\nSolltest Du zur Abgabe Deines ersten Gebotes noch weitere Zahlen, Daten, Fakten benötigen, sende einfach eine Liste der benötigten Informationen an die Verkäufer und mich. Wir werden Dir diese Informationen dann aufbereiten.\n\n \n\nEIN KLARES HILFEANGEBOT VON MIR: Auch können wir gern einen Telefontermin vereinbaren, in dem wir uns gemeinsam einer Unternehmensbewertung nähern. Falls gewünscht, schicke bitte einfach eine E-Mail. Meine Assistentin wird Dir dann drei Terminvorschläge per E-Mail zusenden.\n\n \n\nSobald uns auch Dein Gebot vorliegt, bekommst Du von mir eine klare Aussage zurückgespiegelt, wie gut Dein Angebot passt. Neben einem fairen Kaufpreis kommt es den Verkäufern auch auf weitere Faktoren an, z.B. eine gute Vertrauensebene, eine sichere Zukunftsplanung für die Mitarbeiter und Kunden etc.\n\n \n\nWenn wir uns dann im Großen und Ganzen einig sind, gehen wir in die nächste Stufe und erstellen einen „Letter Of Intent“, also einen Vorvertrag, der die groben Rahmenbedingungen des Unternehmenskaufs festlegt.\n\n \n\nIst dieser geschlossen, beginnt die „Due Diligence“ Phase. In dieser Phase hast Du für einen definierten Zeitraum die Möglichkeit, alle Interna sowie Zahlen, Daten und Fakten des Unternehmens genauestens zu prüfen. Parallel beginnt dann die Erstellung des notariellen Kaufvertrages, wofür ich schon eine darauf spezialisierte Kanzlei in meinem geschäftlichen Umfeld habe.\n\n \n\nBei allen Schritten begleite ich den Prozess mit und stehe für Deine Fragen und die der Verkäufer zur Verfügung. Wenn wir schnell sind, sind wir in wenigen Wochen mit diesem Vorgang durch. Solche Verkäufe habe ich schon innerhalb von 3-4 Wochen realisiert.\n\n \n\nWelche Deiner Fragen sind noch offen?\n\n \n\nPS: Wenn Du für den fairen Preis Deines ersten indikativen Kaufgebotes Unterstützung benötigst, schick mir bitte eine E-Mail. Meine Assistentin sendet Dir dann drei Terminvorschläge für einen gemeinsamen Telefontermin zurück (Die Verkäufer nehmen an diesem Telefonat dann nicht teil).\n\nWICHTIG! ANLAGE INDIKATIVES KAUFGEBOT (EXCEL) MIT RICHTIGER PROJEKTNUMMER ANHÄNGEN\n\n \n\nHallo Herr,\n\n \n\ndas erste Kennenlernen mit dem Unternehmen hat nun ja stattgefunden und von beiden Seiten besteht grundsätzliches Interesse – sehr schön!\n\n \n\nZum einen passt die zwischenmenschlichen Ebene als wichtige Voraussetzung.\n\nZum anderen passen Ihre Kaufmotive und die Verkaufsmotive der Verkäufer gut zusammen.\n\n \n\nAls nächstes benötige ich von Ihnen ein erstes indikatives Kaufgebot innerhalb der nächsten Tage.\n\nWas sind Sie bereit, für dieses Unternehmen zu investieren?\n\nDafür habe ich Ihnen eine Excel Datei als Vorlage beigelegt, so dass sich das Angebot gut strukturieren lässt (Sie können natürlich gern ein freies Angebot formulieren).\n\n \n\nAuf die gleiche Art und Weise stehen wir auch mit den anderen Interessenten in Verbindung. Wir haben schon mehrere Kaufgebote vorliegen. So ergibt sich für die Verkäufer ein klares Bild, wie der Marktpreis von deren IT-Unternehmen eingeschätzt wird.\n\n \n\nSollten Sie zur Abgabe Ihres ersten Gebotes noch weitere Zahlen, Daten, Fakten benötigen, senden Sie einfach eine Liste der benötigten Informationen an die Verkäufer und mich. Wir werden Ihnen diese Informationen dann aufbereiten.\n\n \n\nEIN KLARES HILFEANGEBOT VON MIR: Auch können wir gern einen Telefontermin vereinbaren, in dem wir uns gemeinsam einer Unternehmensbewertung nähern. Falls gewünscht, schickes Sie bitte einfach eine E-Mail. Meine Assistentin wird Ihnen dann drei Terminvorschläge per E-Mail zusenden.\n\n \n\nSobald uns auch ihr Gebot vorliegt, bekommen Sie von mir eine klare Aussage zurückgespiegelt, wie gut Ihr Angebot passt. Neben einem fairen Kaufpreis kommt es den Verkäufern auch auf weitere Faktoren an, z.B. eine gute Vertrauensebene, eine sichere Zukunftsplanung für die Mitarbeiter und Kunden etc.\n\n \n\nWenn wir uns dann im Großen und Ganzen einig sind, gehen wir in die nächste Stufe und erstellen einen „Letter Of Intent“, also einen Vorvertrag, der die groben Rahmenbedingungen des Unternehmenskaufs festlegt.\n\n \n\nIst dieser geschlossen, beginnt die „Due Diligence“ Phase. In dieser Phase haben Sie für einen definierten Zeitraum die Möglichkeit, alle Interna sowie Zahlen, Daten und Fakten des Unternehmens genauestens zu prüfen. Parallel beginnt dann die Erstellung des notariellen Kaufvertrages, wofür ich schon eine darauf spezialisierte Kanzlei in meinem geschäftlichen Umfeld habe.\n\n \n\nBei allen Schritten begleite ich den Prozess mit und stehe für Ihre Fragen und die der Verkäufer zur Verfügung. Wenn wir schnell sind, sind wir in wenigen Wochen mit diesem Vorgang durch. Solche Verkäufe habe ich schon innerhalb von 3-4 Wochen realisiert.\n\n \n\nWelche Ihrer Fragen sind noch offen?\n\n \n\nPS: Wenn Sie für den fairen Preis Ihres ersten indikativen Kaufgebotes Unterstützung benötigen, schicken Sie mir bitte eine E-Mail. Meine Assistentin sendet Ihnen dann drei Terminvorschläge für einen gemeinsamen Telefontermin zurück (Die Verkäufer nehmen an diesem Telefonat dann nicht teil).",
    },
    {
        "RowKey": "jenny-oliver-leadempfehlung",
        "name": "Oliver Wegner: Lead-Empfehlung",
        "kategorie": "Partner",
        "betreff": "Leadanmeldung {{firma}}, {{name}}, {{mbNr}}",
        "body": "Hallo Oliver,\n\nmit dem oben genannten Unternehmen stehe ich in Gesprächen zum Verkauf des Unternehmens.\n\nBitte bestätige mir, dass ihr bisher noch keinen Kontakt zu dem oben genannten Unternehmen hattet.\n\nVor einer Kontaktaufnahme ist es zwingend erforderlich, dass wir telefonieren und den Kontakt aufwärmen und vorbereiten.\n\nHier die Kontaktdaten:\n\nxxx\n\nxxx\n\n \n\nIch freue mich auf Deine Bestätigung!",
    },
    {
        "RowKey": "jenny-oliver-tueroeffner",
        "name": "Oliver Wegner: Tür öffnen",
        "kategorie": "Partner",
        "betreff": "Neue Kontakte und Ideen, Projekt {{mbNr}}",
        "body": "ACHTUNG! VIEL ANPASSUNG ERFORDERLICH! NUR EINE GROBE VORLAGE!\nIch hatte mich mit einem Kollegen, der auch IT Unternehmensverkäufe betreut, ohne Namensnennung über die Wizard Computersysteme unterhalten.\n\nIch habe bei ihm mal angetestet, was er zu Geschäftsmodell „Systemhaus mit echtem, eigenem RZ“, Mitarbeiteranzahl und Umsätzen sagt – und er teilte mir mit, dass diese Beschreibung gut zu einigen Gesuchen in seiner Kartei passt.\n\nSomit hätten wir einen weiteren Pfeil im Köcher.\n\nIch warte nun ab, wie die Gespräche zwischen Ihnen und Herrn Kalisch und Herrn Schmidt verlaufen sind und freue mich auf Ihren Anruf an 27.02.2019 um 17.30 Uhr auf meinem Handy 0160-94428355.\n\nSollten die Gespräche mit K+S nicht zu Ihrer Zufriedenheit verlaufen sein, so können Sie sich in der Zwischenzeit Gedanken machen, ob ich Ihre Kontaktdaten an meinem Kollegen weiterleiten darf, damit Sie einmal darüber sprechen können, welche Interessenten noch zu Ihnen passen können.\n\nIhnen ein schönes Wochenende!",
    },
    {
        "RowKey": "jenny-uve-coaching-ablauf",
        "name": "UVE-Coaching läuft ab - was passiert jetzt",
        "kategorie": "Verkäufer-Akquise",
        "betreff": "Dein UVE-Coaching - wie geht es weiter",
        "body": "Hallo XXX (per DU),\n\nich melde mich zu deinem UVE-Coaching, welches du bei uns gebucht hast. \n\nDein aktuelles Programm läuft am xxx aus / ist am xxx ausgelaufen. \n\nWir haben keine weiteren Rückmeldungen zu deinem aktuellen Status erhalten und informieren dich hiermit über den weiteren Verlauf, was jetzt passiert.",
    },
    {
        "RowKey": "jenny-kanzlei-vertrag",
        "name": "Kanzlei für Vertragserstellung anstoßen",
        "kategorie": "Partner",
        "betreff": "Vertragserstellung für {{mbNr}}",
        "body": "Hallo XYZ,\n\nhiermit stelle ich den Kontakt zwischen euch beiden her.\n\nBastian Rottenberg möchte ASAP, möglichst schon zum Monatsende, 100% seines IT-Systemhauses A-Z Systeme in Mühlhausen verkaufen. Einen konkreten Interessenten haben wir, ein LOI ist heute geschlossen worden (siehe Anhang).\n\nIch habe Bastian darüber informiert, dass sein Investment für die Vertragserstellung erfahrungsgemäß ca. 4000 Euro betragen wird.\n\nDafür erstellt ihr einen notarfähigen Vertrag, der unter juristischen und steuerlichen Gesichtspunkten geprüft und aufgestellt ist.\n\nTypischerweise wird es dann diverse Korrekturrunden mit dem Kaufinteressenten geben. Beide, sowohl Bastian Rottenberg als auch Ronny Wittig als Käufer sind momentan sehr schnell unterwegs und haben sich freie Zeit geblockt, so dass der Zeitplan durchaus realistisch erscheint.\n\nEine DD ist bereits im vollen Gange.\n\n \n\nDiese Schritte empfehle ich als nächstes:\n\n1.)    Kontaktaufnahme von einem Kollegen der Mittelstandsberater (Christian, Du?) zu Bastian Rottenberg zur Klärung von Fragen\n\n2.)    Schriftliche Mandatserteilung durch die Mittelstandsberater\n\n3.)    Vertragsgestaltung anhand des LOI, dann Korrekturlesen durch Bastian und mich, danach weiterleiten an den Käufer\n\n4.)    Ggf. Korrekturrunden per Mail oder Abstimmungen per GOTOMEETING Videokonferenz\n\n5.)    Finale Erstellung des Vertrages, so dass Bastian und Ronny dann einen Notartermin vereinbaren können\n\n \n\nOkay? Dann bitte ich Dich, Christian, um Kontaktaufnahme bei Ronny.\n\n \n\n \n\nHier die Kontaktdaten:\n\nA-Z Systeme GmbH\n\nWanfrieder Str. 169/170\n\n99974 Mühlhausen\n\nGeschäftsführer Bastian Rottenberg\n\nE-Mail-Adresse: bastian@rottenbergs.de\n\nInternetseite: http://www.az-systeme.de\n\nMobilnummer: 0172-6879247\n\n \n\n \n\n \n\nHier die Kontaktdaten der Mittelstandsberater:\n\nhttp://www.ihre-mittelstandsberater.de",
    },
    {
        "RowKey": "jenny-antwort-ohne-nda",
        "name": "Antwort: Interessent will Infos ohne NDA",
        "kategorie": "Interessenten-Antwort",
        "betreff": "Ihre Rückfragen zum zu verkaufenden IT-Unternehmen",
        "body": "Hallo Herr Moll,\n\nvielen Dank für die Rückfragen zum Kurzexposé. Es zeigt, dass Sie sich mit dem Thema ja intensiv beschäftigen und ganz genau hinter die Kulissen schauen möchten.\n\nDie Antwort vorweg in einem Satz, bevor ich diese nähere erläutere:\n\nBitte unterzeichnen Sie zunächst den NDA und senden diesen zurück. Dieser ist Grundvoraussetzung dafür, dass Sie wir Ihnen weitere Informationen zusenden und Sie einen ersten Kennenlerntermin vereinbaren können.\n\nDie Hintergründe dazu:\n\nSelbstverständlich gibt es noch viele weitere Fakten, die Sie vor der Investition in ein IT-Unternehmen genau wissen wollen. Erfahrungsgemäß möchte übrigens jeder Interessent ein paar andere Dinge genau wissen.\n\nWarum nicht mehr Informationen im Kurzexposé stehen, hat einen guten Grund: Das Exposé ist ja anonym gehalten, damit Kunden, Mitarbeiter oder direkte Konkurrenten des zu verkaufenden IT-Unternehmens aus dem Kurzexposé keine Rückschlüsse auf das Unternehmen vornehmen können, solange die Verschwiegenheitserklärung nicht vorliegt. Darauf legen die Unternehmer, die mich mit dem Verkauf beauftragen, größten Wert.\n\nMein Vorschlag: Nach Vorliegen des von Ihnen unterzeichneten NDAs leiten wir Ihre Fragen direkt an den verkaufenden Unternehmer weiter. Dieser kann, gemeinsam mit seiner Antwort, auch gleich einen Termin für ein erstes Kennenlerngespräch mit Ihnen vereinbaren.\n\nNoch einmal zur Erinnerung: Im ersten Kennenlerngespräch geht es vor allem darum, dass Sie das Unternehmen und den Unternehmer kennenlernen können, auch vertiefende Fragen stellen oder zusätzliche Unterlagen anfordern können. Auch geht es um die Zukunftsperspektiven für beide Unternehmen durch Ihren Zukauf. Im ersten Kennenlerngespräch finden keinerlei Gespräche über den Kaufpreis statt.\n\nIn der Folge des Kennenlerngespräches senden Sie, Ihr Interesse natürlich vorausgesetzt, dann mir bitte per E-Mail ein erstes indikatives Kaufgebot. Der weitere Prozess ist ebenfalls im Kurzexposé/NDA Dokument beschrieben.\n\nIch freue mich auf Ihre Zusendung des NDAs – bis bald!",
    },
    {
        "RowKey": "jenny-vernichten-loeschen",
        "name": "Absage nach Verkauf: bitte vernichten/löschen",
        "kategorie": "Abschluss",
        "betreff": "{{firma}} ist verkauft - bitte Unterlagen vernichten",
        "body": "Hallo XXXX,\n\n \n\nan dieser Stelle möchte ich Dir mitteilen, dass wir in wenigen Wochen den Verkauf der XXXX abgeschlossen haben werden. Wir sind uns mit Interessenten einig geworden und der Notartermin steht kurz bevor.\n\nIch danke auch im Namen von XXX für das Interesse und für die angenehme Zusammenarbeit.\n\n \n\nBitte vernichte alle Dir vorliegenden Unterlagen über die XXXX und bestätige mir die Vernichtung durch eine kurze E-Mail.\n\n \n\nWenn ich wieder ein für Dich geeignetes Unternehmen zum Zukauf finden sollte, werde ich auf Dich zukommen.\n\n \n\nVielen Dank und bis bald!\n\nHallo XXXX,\n\n \n\nan dieser Stelle möchte ich Dir mitteilen, dass wir in wenigen Wochen den Verkauf der XXXX abgeschlossen haben werden. Wir sind uns mit Interessenten einig geworden und der Notartermin steht kurz bevor.\n\nIch danke auch im Namen von XXX für das Interesse und für die angenehme Zusammenarbeit.\n\n \n\nBitte vernichten Sie alle Ihnen vorliegenden Unterlagen über die XXXXX und bestätigen mir die Vernichtung durch eine kurze E-Mail.\n\n \n\nWenn ich wieder ein für Sie geeignetes Unternehmen zum Zukauf finden sollte, werde ich auf Sie zukommen.\n\n \n\nVielen Dank und bis bald!",
    },
    {
        "RowKey": "jenny-dienstleistungsvertrag",
        "name": "Dienstleistungsvertrag zur Gegenzeichnung",
        "kategorie": "Verkäufer-Mandat",
        "betreff": "{{mbNr}} - Dienstleistungsvertrag von mir unterschrieben",
        "body": "Hallo…,\n\nvielen Dank für das vertrauensvolle Gespräch.\n\nIch bin überzeugt davon, dass ich für euch in kurzer Zeit den optimalen Käufer finden werde.\n\nIm Anhang der bereits von mir unterzeichnete Dienstleistungsvertrag. Bitte sendet mir diesen gegengezeichnet zurück.\n\nIm Anschluss erhaltet ihr dann von mir zwei Dateien („Fragebogen-Unternehmensbewertung-blanko.xlsx“ und „Zahlen-Daten-Fakten-leer-mit-Beispielzahlen.xlsx“), die ihr bitte ausfüllt und zurücksendet.\n\nAuf dieser Basis dann erstelle ich das Kurzexposé, welches ich euch dann noch einmal zur Freigabe zusende.\n\nAb diesem Moment beginnt dann das Kontakten der ersten Interessenten, die ich mir bereits vorbereitet habe.\n\nWir kommen also schnell ins Handeln mit einem sicheren, strukturierten und mehrfach erprobten Prozess.\n\n \n\nWenn ihr Fragen habt, schreibt mir einfach eine E-Mail.\n\nIm Auftrag von Mike:\n\nSehr geehrter Herr XXX,\n\nim Auftrag von Herrn Mike Bergmann sende ich Ihnen hiermit den Dienstleistungsvertrag zu.\n\nWir bitten um Überprüfung und Unterschrift des Vertrages. \n\nNach Erhalt des durch Ihnen unterschriebenen Vertrages werden die weiteren Details gerne besprochen.\n\nFür Rückfragen stehe ich Ihnen gerne zur Verfügung.",
    },
    {
        "RowKey": "jenny-verkaeufer-3-expose-online",
        "name": "3. Mail Verkäufer: Exposé ist online",
        "kategorie": "Verkäufer-Mandat",
        "betreff": "{{mbNr}} - Dein Exposé ist online, wie geht es weiter",
        "body": "Guten Morgen,\n\nvielen Dank für eure Daten. Damit konnte ich das Exposé jetzt „rund“ machen. \n\nIhr könnt es über diesen Link direkt downloaden:  {{anfrageLink}} (LINK ANPASSEN)\n\n \n\nInteressenten bekommen es von mir nicht direkt, sondern nur über die Bekanntgabe von deren Kontaktdaten: {{anfrageLink}} (LINK ANPASSEN)\n\n \n\nDurch das Eintragen wird automatisch ein Google Doc (Online-Excel) mitgeführt, in dem wir auch Notizen über den Gesprächsstand notieren.\n\nWenn ihr mir beide einen persönlichen Google Account von euch meldet, schalte ich diesen für einen Zugriff auf das Dokument frei. So könnt ihr stets sehen, mit wem wir in Verhandlungen stehen. Außerdem könnt ihr ein VETO für die Weitergabe eurer persönlichen Kontaktdaten eintragen (z.B. wenn es ein besonders unliebsamer Mitbewerber ist, der nicht wissen soll, dass ihr verkaufen wollt.)\n\nWie geht es nun weiter: Ich beginne nun mit der Erstansprache der Interessenten über zahlreiche verschiedene Kanäle. Diese erhalten dann ein Anschreiben und den Link. Sobald ich für das Dokument freigeschaltet habe, könnt ihr „zusehen“, wie sich die Liste füllen wird. Tragt dann ggf. ein Veto ein sowie Bemerkungen von euch als Lemontec.\n\nAuf geht’s!",
    },
    {
        "RowKey": "jenny-entziehungsgespraech",
        "name": "Druck machen / Entziehungsgespräch",
        "kategorie": "Interessenten-Antwort",
        "betreff": "{{mbNr}} - Entscheidung erforderlich",
        "body": "rot = ggf. anpassen\n\nSehr geehrter Interessent,\n\n(ggf. Duzen, wie z.B “Hallo Thomas”),\n\nbis vor einiger Zeit hatten wir uns intensiv über Dein Kauinteresse für das IT-Unternehmen mit der Projektnr. {{mbNr}} unterhalten. In den letzten Wochen habe ich von Dir nichts mehr bezüglich dieser Transaktion gehört, weshalb ich davon ausgehe, dass Dein Interesse am Kauf mittlerweile erloschen ist.\n\nDa wir zur Zeit in konkreten Verhandlungen mit anderen Interessenten stehen, bitte ich Dich, gemäß NDA alle über das Unternehmen erhaltenen vertraulichen Information zu löschen und mich über die erfolgte Löschung zu informieren.\n\nSollte allerdings weiterhin konkretes und kurzfristiges Interesse an einer Transaktion über {{mbNr}} von Deiner Seite bestehen, so bitte ich Dich, umgehend mit uns in Kontakt zu treten. Unterbreite und dann die nächsten konkreten Angebote und Vorschläge für diese Transaktion, damit wir Dich im Verhandlungsprozess noch weiterhin berücksichtigen können.\n\nVielen Dank.",
    },
    {
        "RowKey": "jenny-eröffnung-erstgespraech",
        "name": "Eröffnungsmail nach Erstgespräch",
        "kategorie": "Verkäufer-Akquise",
        "betreff": "Nach unserem Gespräch - Fragebogen und BWAs",
        "body": "Hallo ,\n\nvielen Dank für unser ausführliches Gespräch und für Deinen Vertrauensvorschuss. Ich bin mir sicher, dass wir für Dich, Deine persönlichen Ziele und Dein Unternehmen, den richtigen Zukunftsweg finden werden.\n\nDamit ich mir einen genauen Eindruck verschaffen kann, fülle bitte diesen Excel-Fragebogen aus (zwei Tabellenblätter) und sende mir außerdem die BWAs und Bilanzen der letzten drei Jahre. Oftmals sind die Bilanzen nicht auf dem aktuellen Stand, von daher ist es umso wichtiger, dass zumindest die BWAs so aktuell wie möglich sind.\n\nAuf dem zweiten Tabellenblatt „Adjusted EBIT“ geht es darum, dass Du alle „privaten Sonderlocken“, die Du über die Firma nutzt, für uns intern deutlich machst. Die Angaben hier haben eine ganz erhebliche Auswirkung auf den späteren Kaufpreis.\n\n \n\nNachdem ich die Daten dann von Dir gesichtet habe, vereinbaren wir einen neuen Termin und besprechen das weitere Vorgehen. Einverstanden?\n\n \n\nHier der NDA als Verschwiegenheitserklärung. Bitte unterschreibe und sende mir diesen zurück: https://www.dropbox.com/s/s0vx1qqqq125ip0/NDA%20-%20Allgemeine%20beidseitige%20Vertraulichkeitsvereinbarung%20MB.pdf?dl=0\n\nUnd hier der besagte Fragebogen:\n\nhttps://www.dropbox.com/s/x6qebceyrspat2z/Fragebogen-Unternehmensbewertung-blanko-2021-Kurzfassung.xlsx?dl=0\n\nÜbrigens: Solltest Du einmal eine Mail von Margot Gaenicke-Kaffke bekommen, obwohl Du mir geschrieben hast: Margot ist seit 2010 meine Assistentin, sehr verschwiegen und ehemals Leiterin eines Notariats. Sie unterstützt mich von A bis Z bei allen Prozessen im Unternehmens(ver)kauf.\n\n \n\nIch freue mich auf Deine Antwort, bis bald!",
    },
    {
        "RowKey": "jenny-erste-anforderung-fragebogen",
        "name": "Erste Anforderung Fragebogen (Sie-Form)",
        "kategorie": "Verkäufer-Akquise",
        "betreff": "Nach Ihrer Anfrage - Fragebogen für die nächsten Schritte",
        "body": "Hallo Herr XXX,\n\nvielen Dank für die Ansprache über Empfehlung. Grundsätzlich kann ich Ihnen bei Unternehmensverkäufen in der IT weiterhelfen. In den letzten 3 Jahren habe ich über 30 Transaktionen erfolgreich begleitet.\n\nDas wichtigste für uns beide ist es im Vorfeld, einmal genau herauszufinden, ob ich für Ihr Unternehmen den richtigen Käufer finde.\n\nDie Nachfrage ist momentan sehr groß, dass ich vor jedem neuen Auftrag, den ich annehme, ganz genau schaue, ob ich dem Verkäufer, also Ihnen, auch wirklich weiterhelfen kann.\n\nDeshalb bitte ich Sie, mir diesen Fragebogen ausgefüllt zurückzusenden:\n\nhttps://www.dropbox.com/s/x6qebceyrspat2z/Fragebogen-Unternehmensbewertung-blanko-2021-Kurzfassung.xlsx?dl=0\n\nIm Dokument werden auch Unterlagen wie BWAs und Bilanzen angefordert.\n\nSobald ich den Fragenbogen und die Unterlagen gesichtet habe, kann ich Ihnen eine klare Rückmeldung geben, ob und wie ich Ihnen weiterhelfen kann.\n\nErst dann macht auch ein Telefonat Sinn, weil wir dann qualifiziert über das Thema sprechen können.\n\nEinverstanden?\n\nVielen Dank und bis dann.",
    },
    {
        "RowKey": "jenny-verkaeufer-1-pruefung",
        "name": "1. Mail Verkäufer: Prüfung Kurz-Exposé",
        "kategorie": "Verkäufer-Mandat",
        "betreff": "{{mbNr}} - nächste Schritte",
        "body": "Am Beispiel von Marco Radoux, Machines:\n\n \n\nHallo Herr Radoux,\n\nhallo Margot,\n\n \n\ndamit unser Projekt in Gang kommt, auch während ich im Urlaub bin, habe ich hier die wichtigen Schritte zusammengefasst.\n\nEs ist wichtig, dass dieser Vorgang bereits in der Woche ab dem Montag 18.02.2019 in Gang kommt.\n\nHier das Vorgehen: \n\n1.)               Herr Marco Radoux (kurz MR) schaut sich das Kurzexposé als Word-Datei an, nimmt ggf. kleine Änderungen vor und sendet dann im Anschluss die Word-Datei und eine PDF Datei des Dokumentes zurück: https://www.dropbox.com/s/1vmf28ahz3vhj9a/Kurzexpos%C3%A9-und-NDA-{{mbNr}}.docx?dl=0\n\n2.)               Margot Gaenicke-Kaffke (kurz MG) legt diese Dokumente dann in „it-unternehmen-kaufen-verkaufen\\Machines-Radoux-mb058“ ab.\n\n3.)               MG sendet dann diese PDF Datei mit meinem Anschreiben (MG, siehe separate Mail) und in meinem Namen an die fünf hier genannten Interessenten (siehe unten). Wichtig: Bitte jede Mail separat versenden. Mit allen Herren bin ich per Du, bis auf Herrn Patric Moll, der bitte gesiezt wird.\n\n4.)               Sobald diejenigen geantwortet haben, erhalten diese das zweite Anschreiben per Mail (MG, siehe separate Mail). In diesem wird dann der Kontakt zu Herrn Radoux hergestellt. Herr Radoux stimmt dann mit diesen Kontakten selbst ein erstes Gespräch ab.\n\n5.)               Herr Radoux, im ersten Gespräch geht es NUR um den zwischenmenschlichen Kontakt und die Story – niemals um den Kaufpreis, okay?\n\n \n\nIch wünsche uns allen gutes Gelingen während meiner Abwesenheit:\n\n \n\nRoger Geitzenhauer\n\nSky Systems\n\nr.geitzenauer@skysystems.it\n\nPatric Moll\n\nMoll IT Solutions\n\npatrick.moll@moll-it-solutions.de\n\nClaas Mehrwald\n\nPCM GmbH Claas Mehrwald\n\nclaas.mehrwald@pcm-gmbh.com\n\nMike Brumniera\n\nedv Trend\n\nMb@edv-Trend.de\n\nZoran Trajkovic\n\nIndusys GmbH\n\ntrajkovic@indusys.de",
    },
    {
        "RowKey": "jenny-verkaeufer-2-vertrag",
        "name": "2. Mail Verkäufer: Dienstleistungsvertrag",
        "kategorie": "Verkäufer-Mandat",
        "betreff": "{{mbNr}} - Dienstleistungsvertrag von mir unterschrieben",
        "body": "Hallo…,\n\nvielen Dank für das vertrauensvolle Gespräch.\n\nIch bin überzeugt davon, dass ich für euch in kurzer Zeit den optimalen Käufer finden werde.\n\nIm Anhang der bereits von mir unterzeichnete Dienstleistungsvertrag. Bitte sendet mir diesen gegengezeichnet zurück.\n\n \n\nIm Anschluss erhaltet ihr dann von mir zwei Dateien („Fragebogen-Unternehmensbewertung-blanko.xlsx“ und „Zahlen-Daten-Fakten-leer-mit-Beispielzahlen.xlsx“), die ihr bitte ausfüllt und zurücksendet.\n\nAuf dieser Basis dann erstelle ich das Kurzexposé, welches ich euch dann noch einmal zur Freigabe zusende.\n\nAb diesem Moment beginnt dann das Kontakten der ersten Interessenten, die ich mir bereits vorbereitet habe.\n\nWir kommen also schnell ins Handeln mit einem sicheren, strukturierten und mehrfach erprobten Prozess.\n\n \n\nWenn ihr Fragen habt, schreibt mir einfach eine E-Mail oder kontaktiert mich über Handy.",
    },
]


def _seed_vorlagen_if_empty():
    """Beim ersten Aufruf: Default-Vorlagen anlegen, falls Tabelle leer."""
    try:
        existing = list(table_("mailvorlagen").list_entities())
        if existing:
            return
        for v in _SEED_VORLAGEN:
            ent = {"PartitionKey": "vorlage", **v}
            table_("mailvorlagen").create_entity(ent)
    except Exception as e:
        logging.exception("seed_vorlagen failed: %s", e)


def _ensure_seed_vorlagen():
    """Idempotent: legt nur Vorlagen an, die noch nicht existieren (per RowKey).
    Editierte Versionen werden NICHT überschrieben."""
    added = 0
    try:
        existing_keys = {v.get("RowKey") for v in table_("mailvorlagen").list_entities()}
        for v in _SEED_VORLAGEN:
            if v["RowKey"] in existing_keys:
                continue
            ent = {"PartitionKey": "vorlage", **v}
            try:
                table_("mailvorlagen").create_entity(ent)
                added += 1
            except Exception as e:
                logging.exception("ensure_seed %s failed: %s", v["RowKey"], e)
    except Exception as e:
        logging.exception("ensure_seed_vorlagen failed: %s", e)
    return added


@app.route(route="mailvorlagen-reseed", methods=["POST", "OPTIONS"])
def mailvorlagen_reseed(req: func.HttpRequest) -> func.HttpResponse:
    """Fuegt Jenny-Vorlagen hinzu, die noch fehlen. Vorhandene werden NICHT überschrieben."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    added = _ensure_seed_vorlagen()
    return ok_({"added": added, "total": len(_SEED_VORLAGEN)})


@app.route(route="mailvorlagen-list", methods=["GET", "OPTIONS"])
def mailvorlagen_list(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    _seed_vorlagen_if_empty()
    try:
        items = [dict(v) for v in table_("mailvorlagen").list_entities()]
    except Exception:
        items = []
    items.sort(key=lambda x: (x.get("kategorie", ""), x.get("name", "")))
    return ok_(items)


@app.route(route="mailvorlage-save", methods=["POST", "OPTIONS"])
def mailvorlage_save(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    try:
        body = req.get_json()
    except Exception:
        return err_("Ungueltiger Body")
    rk = body.get("RowKey") or f"vorlage-{int(datetime.utcnow().timestamp() * 1000)}"
    ent = {
        "PartitionKey": "vorlage",
        "RowKey": rk,
        "name": body.get("name", "").strip(),
        "kategorie": body.get("kategorie", "Allgemein").strip(),
        "betreff": body.get("betreff", ""),
        "body": body.get("body", ""),
    }
    if not ent["name"]:
        return err_("Name fehlt")
    try:
        table_("mailvorlagen").upsert_entity(ent)
    except Exception as e:
        return err_(f"Speichern fehlgeschlagen: {e}", 500)
    return ok_(ent)


@app.route(route="mailvorlage-delete", methods=["POST", "OPTIONS"])
def mailvorlage_delete(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    try:
        body = req.get_json()
        rk = body.get("RowKey")
    except Exception:
        return err_("Ungueltiger Body")
    if not rk:
        return err_("RowKey fehlt")
    try:
        table_("mailvorlagen").delete_entity("vorlage", rk)
    except Exception as e:
        return err_(f"Loeschen fehlgeschlagen: {e}", 500)
    return ok_({"deleted": rk})


# ============================================================
# Geplante Hintergrund-Jobs (Daily/Monthly via TimerTrigger)
# ============================================================

def _send_email_html(to_address, subject, html_body, plain_body=""):
    """Sendet eine HTML-Mail via Azure Communication Services.
    Stiller Failover wenn ACS nicht konfiguriert ist."""
    if not (ACS_CONN and to_address):
        return False
    try:
        from azure.communication.email import EmailClient
        client = EmailClient.from_connection_string(ACS_CONN)
        client.begin_send({
            "senderAddress": ACS_SENDER,
            "recipients": {"to": [{"address": to_address}]},
            "content": {
                "subject": subject,
                "plainText": plain_body or subject,
                "html": html_body,
            },
        })
        return True
    except Exception as ex:
        logging.warning(f"Mail-Versand an {to_address} fehlgeschlagen: {ex}")
        return False


def _list_admin_emails():
    """Liefert E-Mail-Adressen aller aktiven Admins (fuer interne Benachrichtigungen)."""
    out = []
    try:
        for u in table_("users").list_entities():
            if u.get("role") == "admin" and u.get("email"):
                out.append(u["email"])
    except Exception:
        pass
    return out


def _list_monthly_report_recipients():
    """Empfaenger der Monats-Statusberichte. Wenn ENV MONTHLY_REPORT_RECIPIENTS
    gesetzt ist (komma-separierte Mails), nutze ausschliesslich diese Liste.
    Sonst Fallback: alle Admin-Mails."""
    custom = os.environ.get("MONTHLY_REPORT_RECIPIENTS", "").strip()
    if custom:
        return [m.strip() for m in custom.split(",") if m.strip()]
    return _list_admin_emails()


@app.timer_trigger(schedule="0 0 6 * * *", arg_name="dailyTimer", run_on_startup=False, use_monitor=True)
def daily_termin_reminders(dailyTimer: func.TimerRequest) -> None:
    """Laeuft taeglich um 06:00 UTC (=08:00 Berlin Sommer / 07:00 Winter).
    Schickt Erinnerungs-Mails fuer Termine, die heute oder in 3 Tagen anstehen.
    Tracking ueber `reminderSent` im Termin-Objekt verhindert Duplikate."""
    logging.info("[CRON] daily_termin_reminders gestartet")
    today = datetime.utcnow().date()
    admin_mails = _list_admin_emails()
    if not admin_mails:
        logging.info("[CRON] Keine Admin-Mails gefunden - Reminder uebersprungen")
        return

    try:
        targets = list(table_("targets").list_entities())
    except Exception as ex:
        logging.error(f"[CRON] Targets nicht abrufbar: {ex}")
        return

    reminders_sent = 0
    for t in targets:
        try:
            termine = json.loads(t.get("termineJson", "[]") or "[]")
        except Exception:
            continue
        if not termine:
            continue
        changed = False
        mb_nr = t.get("mbNr", "")
        firma = t.get("verkaueferName", "") or t.get("firma", "")
        for tm in termine:
            if tm.get("erledigt"):
                continue
            datum = tm.get("datum", "")
            if not datum:
                continue
            try:
                d = datetime.fromisoformat(datum[:10]).date()
            except Exception:
                continue
            tage = (d - today).days
            # Reminder-Fenster: 3 Tage vorher + Tag selbst
            if tage not in (0, 3):
                continue
            # Schon erinnert heute?
            last_reminder = tm.get("lastReminderDate", "")
            if last_reminder == today.isoformat():
                continue
            # Mail rausschicken
            label_zeit = "HEUTE" if tage == 0 else "in 3 Tagen"
            titel = tm.get("titel", "(ohne Titel)")
            typ = tm.get("typ", "sonstiges")
            notiz = tm.get("notiz", "")
            akte_url = f"{FRONTEND_BASE.rstrip('/')}/"
            html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.5">
                <h2 style="color:#0088ba">Termin-Erinnerung: {label_zeit}</h2>
                <table cellpadding="6" style="background:#f0fdfa;border-radius:8px;border-collapse:separate;margin:10px 0">
                  <tr><td>Datum:</td><td><strong>{d.strftime('%d.%m.%Y')}</strong></td></tr>
                  <tr><td>Mandat:</td><td>{mb_nr} &middot; {firma}</td></tr>
                  <tr><td>Typ:</td><td>{typ}</td></tr>
                  <tr><td>Titel:</td><td><strong>{titel}</strong></td></tr>
                  {f'<tr><td>Notiz:</td><td>{notiz}</td></tr>' if notiz else ''}
                </table>
                <p><a href="{akte_url}" style="background:#0088ba;color:white;padding:10px 18px;border-radius:8px;text-decoration:none">Zur Akte</a></p>
                <p style="font-size:11px;color:#888">Automatische Erinnerung des ITUKV Dashboards.</p>
            </body></html>"""
            subject = f"[ITUKV] Termin {label_zeit}: {titel} ({mb_nr})"
            for mail in admin_mails:
                _send_email_html(mail, subject, html, plain_body=f"{titel} – {d.strftime('%d.%m.%Y')} – {mb_nr} {firma}")
                reminders_sent += 1
            tm["lastReminderDate"] = today.isoformat()
            changed = True
        if changed:
            try:
                t["termineJson"] = json.dumps(termine, ensure_ascii=False)
                table_("targets").update_entity(dict(t))
            except Exception as ex:
                logging.warning(f"[CRON] Konnte Reminder-Status nicht speichern: {ex}")
    logging.info(f"[CRON] daily_termin_reminders fertig - {reminders_sent} Mails verschickt")


@app.timer_trigger(schedule="0 0 7 1 * *", arg_name="monthlyTimer", run_on_startup=False, use_monitor=True)
def monthly_status_reports(monthlyTimer: func.TimerRequest) -> None:
    """Laeuft am 1. jedes Monats um 07:00 UTC.
    Schickt fuer jedes aktive Mandat einen Status-Bericht-PDF an die
    hinterlegten Admin-Mails (nicht an Verkaeufer - Jenny prueft erst,
    bevor sie es weitergibt)."""
    logging.info("[CRON] monthly_status_reports gestartet")
    admin_mails = _list_monthly_report_recipients()
    if not admin_mails or not ACS_CONN:
        logging.info("[CRON] Keine Admin-Mails / kein ACS - Reports uebersprungen")
        return

    try:
        targets = list(table_("targets").list_entities())
    except Exception as ex:
        logging.error(f"[CRON] Targets nicht abrufbar: {ex}")
        return

    sent = 0
    for t in targets:
        status = (t.get("status") or "").lower()
        if status in ("verkauft", "abgebrochen"):
            continue
        tid = t.get("RowKey", "")
        mb_nr = t.get("mbNr", "") or "mandat"
        firma = t.get("verkaueferName", "") or t.get("firma", "")
        # PDF generieren via interne Hilfsroutine
        try:
            pdf_bytes = _build_status_report_pdf(dict(t))
        except Exception as ex:
            logging.warning(f"[CRON] PDF-Generierung fuer {mb_nr} fehlgeschlagen: {ex}")
            continue
        # Mail mit Attachment
        filename = f"Statusbericht_{mb_nr}_{datetime.utcnow().date().isoformat()}.pdf"
        html = f"""<html><body style="font-family:Arial,sans-serif;color:#161e2a;line-height:1.5">
            <h2 style="color:#0088ba">Monats-Statusbericht: {mb_nr}</h2>
            <p>Anbei der automatische Statusbericht fuer das Mandat <strong>{firma}</strong>.</p>
            <p style="color:#666;font-size:12px">Pruefe vor dem Weiterleiten an den Mandanten ob der Bericht den aktuellen Stand korrekt wiedergibt.</p>
        </body></html>"""
        try:
            from azure.communication.email import EmailClient
            client = EmailClient.from_connection_string(ACS_CONN)
            pdf_b64 = base64.b64encode(pdf_bytes).decode()
            for mail in admin_mails:
                client.begin_send({
                    "senderAddress": ACS_SENDER,
                    "recipients": {"to": [{"address": mail}]},
                    "content": {
                        "subject": f"[ITUKV] Monats-Statusbericht {mb_nr} – {firma}",
                        "plainText": f"Anbei der Monatsbericht zu {mb_nr} ({firma}).",
                        "html": html,
                    },
                    "attachments": [{
                        "name": filename,
                        "contentType": "application/pdf",
                        "contentInBase64": pdf_b64,
                    }],
                })
                sent += 1
        except Exception as ex:
            logging.warning(f"[CRON] Mail-Versand fuer {mb_nr} fehlgeschlagen: {ex}")
    logging.info(f"[CRON] monthly_status_reports fertig - {sent} Mails")


def _build_status_report_pdf(t):
    """Wird vom Cronjob UND vom HTTP-Endpoint genutzt. Liefert PDF-Bytes."""
    tid = t.get("RowKey", "")
    try: phasen = json.loads(t.get("phasenJson", "[]") or "[]")
    except Exception: phasen = []
    aktuelle = None
    abgeschlossen = []
    for ph in phasen:
        aufgs = ph.get("aufgaben", []) or []
        if aufgs and all(a.get("done") for a in aufgs):
            abgeschlossen.append(ph)
        elif aufgs and not aktuelle:
            aktuelle = ph
    if not aktuelle and phasen:
        aktuelle = phasen[len(abgeschlossen)] if len(abgeschlossen) < len(phasen) else phasen[-1]
    try: verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
    except Exception: verlauf = []
    verlauf_recent = sorted(verlauf, key=lambda e: e.get("datum", ""), reverse=True)[:8]
    try: termine = json.loads(t.get("termineJson", "[]") or "[]")
    except Exception: termine = []
    today_iso = datetime.utcnow().date().isoformat()
    termine_kommend = sorted(
        [tm for tm in termine if (tm.get("datum", "") >= today_iso) and not tm.get("erledigt")],
        key=lambda x: x.get("datum", "")
    )[:10]
    try:
        ints = list(table_("interessenten").query_entities("targetId eq @t", parameters={"t": tid}))
        anzahl_int = len(ints)
        anzahl_nda = sum(1 for i in ints if i.get("ndaStatus") == "unterzeichnet")
    except Exception:
        anzahl_int = 0; anzahl_nda = 0
    mandat_text = ""
    try:
        if t.get("mandatStart") and t.get("mandatLaufzeitMonate"):
            start = datetime.fromisoformat(t["mandatStart"][:10])
            mo = int(t["mandatLaufzeitMonate"])
            ende = start + timedelta(days=mo * 30)
            mandat_text = f"{start.date().strftime('%d.%m.%Y')} – {ende.date().strftime('%d.%m.%Y')} ({mo} Monate)"
    except Exception:
        pass
    from html import escape as _esc
    def fmt_date(s):
        try: return datetime.fromisoformat(s[:10]).strftime("%d.%m.%Y")
        except Exception: return s
    now_str = datetime.utcnow().strftime("%d.%m.%Y")
    aktuelle_aufg_html = ""
    if aktuelle:
        aufgs = aktuelle.get("aufgaben", []) or []
        aktuelle_aufg_html = "<ul>" + "".join(
            f"<li>{'✓ ' if a.get('done') else '◯ '}{_esc(a.get('label',''))}</li>"
            for a in aufgs
        ) + "</ul>"
    verlauf_html = "<p style='color:#999'>Keine Aktivitäten erfasst.</p>" if not verlauf_recent else (
        "<ul>" + "".join(
            f"<li><strong>{fmt_date(e.get('datum',''))}</strong> – {_esc(e.get('betreff') or e.get('typ',''))}</li>"
            for e in verlauf_recent
        ) + "</ul>"
    )
    termine_html = "<p style='color:#999'>Keine anstehenden Termine.</p>" if not termine_kommend else (
        "<ul>" + "".join(
            f"<li><strong>{fmt_date(tm.get('datum',''))}</strong> – {_esc(tm.get('titel',''))} <em style='color:#888'>({_esc(tm.get('typ','sonstiges'))})</em></li>"
            for tm in termine_kommend
        ) + "</ul>"
    )
    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 18mm 16mm; }}
body {{ font-family: Helvetica, Arial, sans-serif; color: #161e2a; font-size: 11pt; line-height: 1.45; }}
h1 {{ color: #0088ba; font-size: 20pt; margin: 0 0 4px; }}
h2 {{ color: #0088ba; font-size: 13pt; margin: 18px 0 6px; padding-bottom: 3px; border-bottom: 1.5px solid #0088ba33; }}
.meta {{ color: #666; font-size: 10pt; margin-bottom: 16px; }}
.box {{ background: #f0fdfa; border-left: 3px solid #0088ba; padding: 10px 14px; margin: 8px 0; }}
table.stats {{ width: 100%; border-collapse: collapse; margin: 8px 0; }}
table.stats td {{ padding: 6px 8px; border-bottom: 1px solid #eee; font-size: 10.5pt; }}
table.stats td:first-child {{ color: #666; width: 45%; }}
ul {{ margin: 4px 0 8px 18px; padding: 0; }}
li {{ margin: 3px 0; font-size: 10.5pt; }}
.footer {{ color: #999; font-size: 9pt; margin-top: 24px; border-top: 1px solid #eee; padding-top: 8px; }}
</style></head>
<body>
  <h1>Status-Bericht Verkaufsmandat</h1>
  <div class="meta">Stand: {now_str} &middot; {_esc(t.get('mbNr',''))} &middot; {_esc(t.get('verkaueferName',''))}</div>
  <h2>Stammdaten</h2>
  <table class="stats">
    <tr><td>mb-Nummer</td><td>{_esc(t.get('mbNr',''))}</td></tr>
    <tr><td>Verkäufer</td><td>{_esc(t.get('verkaueferName',''))}</td></tr>
    <tr><td>Branche</td><td>{_esc(t.get('branche',''))}</td></tr>
    <tr><td>Region</td><td>{_esc(t.get('region',''))}</td></tr>
    <tr><td>Mitarbeiter</td><td>{_esc(str(t.get('mitarbeiter','') or ''))}</td></tr>
    <tr><td>Umsatz</td><td>{_esc(t.get('umsatz',''))}</td></tr>
    <tr><td>Mandatslaufzeit</td><td>{_esc(mandat_text or 'noch nicht erfasst')}</td></tr>
  </table>
  <h2>Aktueller Stand im Prozess</h2>
  <div class="box">
    <strong>{_esc(aktuelle.get('titel','—') if aktuelle else '—')}</strong>
    {aktuelle_aufg_html}
  </div>
  <p style="font-size:10.5pt;color:#666">Phasen abgeschlossen: {len(abgeschlossen)} von {len(phasen)}</p>
  <h2>Interessenten</h2>
  <table class="stats">
    <tr><td>Gesamt angesprochen</td><td>{anzahl_int}</td></tr>
    <tr><td>Davon NDA unterzeichnet</td><td>{anzahl_nda}</td></tr>
  </table>
  <h2>Anstehende Termine</h2>
  {termine_html}
  <h2>Letzte Aktivitäten</h2>
  {verlauf_html}
  <div class="footer">
    Erstellt durch das mibeca ITUKV Dashboard &middot; Vertraulich &middot; nur für den Mandanten bestimmt
  </div>
</body></html>"""
    from weasyprint import HTML
    return HTML(string=html_doc, base_url="/").write_pdf()


# ============================================================
# AUDIT-TRAIL — wer hat wann was geaendert
# ============================================================

def log_audit(p, action, target_type, target_id="", details=None):
    """Schreibt einen Audit-Log-Eintrag.
    Felder: PK='audit', RK=timestamp+uuid, userId, userName, userRole,
            action (create/update/delete/login/...), targetType (target/kontakt/user/...),
            targetId, details (JSON-String mit zusaetzlichen Infos)."""
    try:
        tc = table_("auditlog")
        now = datetime.utcnow()
        rk = now.isoformat() + "_" + str(uuid.uuid4())[:8]
        tc.create_entity({
            "PartitionKey": "audit", "RowKey": rk,
            "ts": now.isoformat(),
            "userId": (p or {}).get("id", "") or "",
            "userName": (p or {}).get("name", "") or "",
            "userRole": (p or {}).get("role", "") or "",
            "action": action,
            "targetType": target_type,
            "targetId": target_id or "",
            "details": json.dumps(details, ensure_ascii=False, default=str)[:32000] if details else "",
        })
    except Exception as ex:
        logging.warning(f"[AUDIT] Konnte Log-Eintrag nicht schreiben: {ex}")


@app.route(route="audit-log", methods=["GET", "OPTIONS"])
def audit_log_list(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert die letzten 200 Audit-Eintraege. Admin-only."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    target_filter = (req.params.get("targetId") or "").strip()
    user_filter = (req.params.get("userId") or "").strip()
    limit = int(req.params.get("limit", "200") or "200")
    try:
        items = list(table_("auditlog").list_entities())
    except Exception:
        items = []
    items = [dict(i) for i in items]
    if target_filter:
        items = [i for i in items if i.get("targetId") == target_filter]
    if user_filter:
        items = [i for i in items if i.get("userId") == user_filter]
    items.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return ok_({"items": items[:limit], "total": len(items)})


# ============================================================
# WEEKLY BACKUP — Tabellen + Audit als JSON in Blob speichern
# ============================================================

@app.timer_trigger(schedule="0 0 3 * * 0", arg_name="weeklyTimer", run_on_startup=False, use_monitor=True)
def weekly_backup(weeklyTimer: func.TimerRequest) -> None:
    """Laeuft Sonntags um 03:00 UTC. Exportiert die wichtigsten Tabellen
    als JSON in den Blob-Container 'backups'. Behaelt 12 Wochen
    (rolliert aelteste raus)."""
    logging.info("[BACKUP] weekly_backup gestartet")
    TABLES = ["targets", "kontakte", "interessenten", "dokumente", "users",
              "mailvorlagen", "vertragsignaturen", "auditlog", "passwordresets"]
    snapshot = {"createdAt": datetime.utcnow().isoformat(), "tables": {}}
    for tname in TABLES:
        try:
            tc = table_(tname)
            entities = []
            for e in tc.list_entities():
                d = dict(e)
                # passwordHash NICHT ins Backup (Risk-Hygiene)
                if tname == "users":
                    d.pop("passwordHash", None)
                entities.append(d)
            snapshot["tables"][tname] = entities
            logging.info(f"[BACKUP] {tname}: {len(entities)} Records")
        except Exception as ex:
            logging.warning(f"[BACKUP] Tabelle {tname} nicht abrufbar: {ex}")
            snapshot["tables"][tname] = {"error": str(ex)}
    # Als JSON in Blob speichern
    try:
        from azure.storage.blob import BlobServiceClient
        svc = BlobServiceClient.from_connection_string(TABLE_CONN)
        try: svc.create_container("backups")
        except Exception: pass
        container = svc.get_container_client("backups")
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        blob_name = f"backup_{date_str}.json"
        body = json.dumps(snapshot, ensure_ascii=False, default=str).encode("utf-8")
        container.upload_blob(blob_name, body, overwrite=True)
        logging.info(f"[BACKUP] gespeichert als {blob_name} ({len(body)/1024:.0f} KB)")
        # Rotation: behalte nur letzte 12
        backups = sorted([b.name for b in container.list_blobs() if b.name.startswith("backup_")], reverse=True)
        for old in backups[12:]:
            try:
                container.delete_blob(old)
                logging.info(f"[BACKUP] alte Sicherung geloescht: {old}")
            except Exception:
                pass
    except Exception as ex:
        logging.error(f"[BACKUP] Upload fehlgeschlagen: {ex}")


@app.route(route="backup-trigger", methods=["POST", "OPTIONS"])
def backup_trigger_manual(req: func.HttpRequest) -> func.HttpResponse:
    """Loest den Backup-Job manuell aus. Admin-only.
    Praktisch fuer „kurz vor groesserer Aenderung Snapshot machen"."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    try:
        weekly_backup(None)  # type: ignore
    except Exception as ex:
        return err_(f"Backup fehlgeschlagen: {ex}", 500)
    log_audit(p, "backup_manual", "system")
    return ok_({"ok": True})


@app.route(route="backup-list", methods=["GET", "OPTIONS"])
def backup_list(req: func.HttpRequest) -> func.HttpResponse:
    """Listet alle verfuegbaren Backups + Download-URL (SAS, 10 Min)."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    out = []
    try:
        from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
        svc = BlobServiceClient.from_connection_string(TABLE_CONN)
        container = svc.get_container_client("backups")
        for b in container.list_blobs():
            sas = generate_blob_sas(
                account_name=svc.account_name, container_name="backups",
                blob_name=b.name, account_key=svc.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(minutes=10),
            )
            out.append({
                "name": b.name,
                "createdAt": b.creation_time.isoformat() if b.creation_time else "",
                "sizeKb": round((b.size or 0) / 1024, 1),
                "downloadUrl": f"https://{svc.account_name}.blob.core.windows.net/backups/{b.name}?{sas}",
            })
    except Exception as ex:
        logging.warning(f"backup-list fehlgeschlagen: {ex}")
    out.sort(key=lambda x: x.get("name", ""), reverse=True)
    return ok_({"backups": out})


# ============================================================
# AI BULK UPDATE — Endpoint speziell fuer KI-Coworker
# Beschraenkter Schreibumfang, jede Aktion ins Audit-Log
# ============================================================

# Felder die ein KI-Agent setzen darf.
# Tabu: alles was Mandats-Stammdaten ist (mbNr, status, projekttyp, Phasen, Mandatslaufzeit),
# und alles was Auth/Berechtigung beruehrt.
AI_WRITABLE_KONTAKT_FIELDS = {
    # Stammdaten zur Anreicherung
    "geschaeftsfuehrer", "name", "telefon", "email", "website",
    "plz", "ort", "region", "branche",
    # Geschaeftskennzahlen
    "mitarbeiter", "umsatzTeur", "ebitMarge", "recurringPct",
    # Klassifizierung / Notizen
    "bietet", "sucht", "kommentar", "kommentarKI", "investorTyp",
    # Strukturierte JSON-Blobs (z.B. weitere Ansprechpartner, Handelsregister-Daten)
    "ansprechpartnerJson", "handelsregisterJson", "bewertungKIJson",
}
AI_WRITABLE_TARGET_FIELDS = {
    # Adresse + Stammdaten-Anreicherung (NICHT mbNr, NICHT status)
    "region", "plz", "branche", "mitarbeiter", "umsatz", "beschreibung",
    # Unternehmens-Stammdaten
    "rechtsform", "gruendungsjahr", "ebitMarge", "recurringPct",
    # Bewertung + Fragebogen + Notizen
    "bewertungJson", "fragebogenJson", "suchprofilJson",
    "kommentarKI", "bewertungKIJson",
    # Geschaeftsfuehrer kann ergaenzt werden, Name aber nicht
    "geschaeftsfuehrer",
}


@app.route(route="ai-bulk-update", methods=["POST", "OPTIONS"])
def ai_bulk_update(req: func.HttpRequest) -> func.HttpResponse:
    """Bulk-Update von Kontakten oder Targets durch einen KI-Service-Account.
    Erlaubt nur Rolle 'ai-agent'. Felder sind streng begrenzt.
    Jeder Aufruf wird ins Audit-Log geschrieben.
    Body: { updates: [{ type: 'kontakt'|'target', id, fields: {...} }, ...] }
    Max 500 Updates pro Aufruf."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") not in ("ai-agent", "admin"):
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    updates = body.get("updates", [])
    if not isinstance(updates, list) or not updates:
        return err_("updates-Array erforderlich", 400)
    if len(updates) > 500:
        return err_("Max 500 Updates pro Aufruf", 400)

    ok_count = 0
    errors = []
    for u in updates:
        ttype = u.get("type")
        tid = u.get("id")
        fields = u.get("fields") or {}
        if not (ttype and tid and isinstance(fields, dict)):
            errors.append({"id": tid, "error": "Ungueltige Struktur"})
            continue
        if ttype == "kontakt":
            allowed = AI_WRITABLE_KONTAKT_FIELDS
            tname = "kontakte"; pk = "kontakt"
        elif ttype == "target":
            allowed = AI_WRITABLE_TARGET_FIELDS
            tname = "targets"; pk = "target"
        else:
            errors.append({"id": tid, "error": f"Unbekannter type: {ttype}"})
            continue
        clean_fields = {k: v for k, v in fields.items() if k in allowed}
        if not clean_fields:
            errors.append({"id": tid, "error": "Keine erlaubten Felder"})
            continue
        try:
            tc = table_(tname)
            ent = tc.get_entity(pk, tid)
            old_values = {k: ent.get(k, "") for k in clean_fields}
            for k, v in clean_fields.items():
                ent[k] = v
            tc.update_entity(dict(ent))
            log_audit(p, "ai_update", ttype, tid, {
                "fields": list(clean_fields.keys()),
                "old": old_values,
                "new": clean_fields,
            })
            ok_count += 1
        except Exception as ex:
            errors.append({"id": tid, "error": str(ex)[:200]})
    return ok_({"updated": ok_count, "failed": len(errors), "errors": errors[:20]})


@app.route(route="ai-verlauf-add", methods=["POST", "OPTIONS"])
def ai_verlauf_add(req: func.HttpRequest) -> func.HttpResponse:
    """KI-Agent haengt einen Verlauf-Eintrag an ein Target an.
    Erlaubte Typen: 'notiz', 'ki_analyse'.
    Body: { targetId, betreff, beschreibung, typ?='ki_analyse', beteiligte? }"""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") not in ("ai-agent", "admin"):
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    tid = (body.get("targetId") or "").strip()
    betreff = (body.get("betreff") or "").strip()
    beschreibung = (body.get("beschreibung") or "").strip()
    typ = body.get("typ") or "ki_analyse"
    if typ not in ("notiz", "ki_analyse"):
        return err_("Erlaubte Typen: 'notiz' oder 'ki_analyse'", 400)
    if not (tid and (betreff or beschreibung)):
        return err_("targetId + (betreff oder beschreibung) erforderlich", 400)
    try:
        ent = dict(table_("targets").get_entity("target", tid))
    except Exception:
        return err_("Target nicht gefunden", 404)
    try:
        verlauf = json.loads(ent.get("kommunikationJson", "[]") or "[]")
    except Exception:
        verlauf = []
    if not isinstance(verlauf, list):
        verlauf = []
    new_entry = {
        "id": "ai" + str(int(datetime.utcnow().timestamp() * 1000)),
        "typ": typ,
        "datum": datetime.utcnow().isoformat(),
        "autor": "KI-Coworker",
        "betreff": betreff[:300],
        "beschreibung": beschreibung[:10000],
        "beteiligte": body.get("beteiligte", "") or "",
        "createdBy": p.get("id", ""),  # damit eigene Mails nicht als ungelesen flaggen
        "createdByKI": True,            # UI-Marker: das war die KI
    }
    verlauf.append(new_entry)
    ent["kommunikationJson"] = json.dumps(verlauf, ensure_ascii=False)
    try:
        table_("targets").update_entity(ent)
    except Exception as ex:
        return err_(f"Speichern fehlgeschlagen: {ex}", 500)
    log_audit(p, "ai_verlauf_add", "target", tid, {
        "typ": typ, "betreff": betreff[:100],
    })
    return ok_({"ok": True, "entry": new_entry})


@app.route(route="ai-dokument-upload", methods=["POST", "OPTIONS"])
def ai_dokument_upload(req: func.HttpRequest) -> func.HttpResponse:
    """KI-Coworker laedt ein Dokument in den Datenraum eines Targets.
    Erlaubt nur Rolle 'ai-agent' oder 'admin'.

    Restriktionen vs. menschlichem Upload:
    - Nur PDF / JSON / XLSX / CSV erlaubt
    - Max 5 MB
    - Pflichtfeld 'quelleUrl' (woher kommt das Dokument?)
    - Wird mit KI-Marker gespeichert, separates Audit-Log
    - Auto-Verlauf-Eintrag in der Akte

    Body: { targetId, ordner, fileName, fileData (base64), contentType, quelleUrl, beschreibung? }
    """
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") not in ("ai-agent", "admin"):
        return err_("Nicht autorisiert", 401)

    body = req.get_json() or {}
    target_id = (body.get("targetId") or "").strip()
    ordner = (body.get("ordner") or "KI-Recherche").strip()
    file_name = (body.get("fileName") or "ki-upload").strip()
    file_data = body.get("fileData", "")
    content_type = body.get("contentType", "application/octet-stream")
    quelle_url = (body.get("quelleUrl") or "").strip()
    beschreibung = (body.get("beschreibung") or "").strip()

    # Pflichtfelder
    if not (target_id and file_data and quelle_url):
        return err_("targetId, fileData und quelleUrl erforderlich", 400)

    # Pro-Akte-Opt-In pruefen (gleicher Schalter wie KI-Analyse)
    try:
        target_ent = table_("targets").get_entity("target", target_id)
    except Exception:
        return err_("Target nicht gefunden", 404)
    if p.get("role") == "ai-agent" and not target_ent.get("kiAnalyseErlaubt"):
        return err_("KI-Zugriff fuer diese Akte nicht freigegeben (kiAnalyseErlaubt=true noetig)", 403)

    # Dateityp-Whitelist (nur die genannten erlauben)
    allowed_ct = {"application/pdf", "application/json", "text/csv",
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                  "application/vnd.ms-excel"}
    fname_lower = file_name.lower()
    allowed_ext = fname_lower.endswith(('.pdf', '.json', '.csv', '.xlsx', '.xls'))
    if content_type not in allowed_ct and not allowed_ext:
        return err_(f"Dateityp nicht erlaubt fuer KI-Upload: {content_type}. Nur PDF/JSON/CSV/XLSX.", 400)

    # Base64-Decode
    try:
        if file_data.startswith("data:"):
            file_data = file_data.split(",", 1)[1]
        binary = base64.b64decode(file_data)
    except Exception as ex:
        return err_(f"Decoding fehlgeschlagen: {ex}", 400)

    # Groessen-Limit (5 MB strict fuer KI)
    if len(binary) > 5 * 1024 * 1024:
        return err_(f"Datei zu gross fuer KI-Upload ({len(binary)} bytes). Max 5 MB.", 400)

    # Path-Sanitization
    def _sanitize(s, default):
        if not s: return default
        s = s.replace("\\", "_").replace("/", "_")
        while ".." in s: s = s.replace("..", "_")
        s = "".join(c for c in s if c.isprintable())
        return s.strip() or default
    ordner = _sanitize(ordner, "KI-Recherche")
    file_name = _sanitize(file_name, "ki-upload")
    if not all(c.isalnum() or c == "-" for c in target_id):
        return err_("Ungueltige targetId", 400)

    # Blob hochladen
    blob_name = f"{target_id}/{ordner}/{uuid.uuid4()}_{file_name}"
    try:
        container = _blob_container_lazy("datenraum")
        from azure.storage.blob import ContentSettings
        container.upload_blob(blob_name, binary, overwrite=False,
                              content_settings=ContentSettings(content_type=content_type))
    except Exception as ex:
        return err_(f"Upload fehlgeschlagen: {ex}", 500)

    # Metadaten in Table mit KI-Marker
    doc_id = str(uuid.uuid4())
    now_iso = datetime.utcnow().isoformat()
    entity = {
        "PartitionKey": target_id,
        "RowKey": doc_id,
        "ordner": ordner,
        "fileName": file_name,
        "blobName": blob_name,
        "contentType": content_type,
        "size": len(binary),
        "uploadedBy": p.get("name", "") or p.get("email", "KI-Coworker"),
        "uploadedByRole": p.get("role", ""),
        "uploadedAt": now_iso,
        # KI-spezifische Felder
        "kiUpload": True,
        "kiQuelleUrl": quelle_url,
        "kiBeschreibung": beschreibung[:1000],
    }
    table_("dokumente").create_entity(entity)

    # Auto-Verlauf-Eintrag in der Akte
    try:
        verlauf = json.loads(target_ent.get("kommunikationJson", "[]") or "[]")
        if not isinstance(verlauf, list): verlauf = []
    except Exception:
        verlauf = []
    verlauf.append({
        "id": "kiup" + str(int(datetime.utcnow().timestamp() * 1000)),
        "typ": "ki_analyse",
        "datum": now_iso,
        "autor": "KI-Coworker",
        "betreff": f"KI hat Dokument hochgeladen: {file_name}",
        "beschreibung": f"Quelle: {quelle_url}\nOrdner: {ordner}\n{beschreibung}",
        "createdBy": p.get("id", ""),
        "createdByKI": True,
    })
    target_ent["kommunikationJson"] = json.dumps(verlauf, ensure_ascii=False)
    try:
        table_("targets").update_entity(target_ent)
    except Exception:
        pass  # Verlauf-Update darf den Upload nicht fehlschlagen lassen

    # Audit-Log
    log_audit(p, "ai_upload", "dokument", doc_id, {
        "targetId": target_id, "ordner": ordner, "fileName": file_name,
        "contentType": content_type, "size": len(binary), "quelleUrl": quelle_url,
    })

    return ok_({
        "id": doc_id,
        "fileName": file_name,
        "ordner": ordner,
        "size": len(binary),
        "uploadedAt": now_iso,
        "kiUpload": True,
        "kiQuelleUrl": quelle_url,
    }, 201)


@app.route(route="ai-uploads-recent", methods=["GET", "OPTIONS"])
def ai_uploads_recent(req: func.HttpRequest) -> func.HttpResponse:
    """Listet alle KI-Uploads der letzten N Tage (default 7) fuer Admin-Review."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    days = int(req.params.get("days", "7"))
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    items = []
    try:
        for d in table_("dokumente").list_entities():
            if d.get("kiUpload") and (d.get("uploadedAt") or "") >= cutoff:
                items.append(dict(d))
    except Exception as ex:
        return err_(f"Lesen fehlgeschlagen: {ex}", 500)
    items.sort(key=lambda x: x.get("uploadedAt", ""), reverse=True)
    return ok_(items)


@app.route(route="element-import", methods=["POST", "OPTIONS"])
def element_import(req: func.HttpRequest) -> func.HttpResponse:
    """Importiert einen Element/Matrix-Raum-JSON-Export in den Verlauf einer Akte.

    Body: {
        targetId: str,
        fileData: str (base64 von JSON-Datei),
        mibecaSenderId: str (optional, Matrix-User-ID der mibeca-Beraterin),
        dryRun: bool (optional, default false)
    }

    Nur Admin. Body-Limit 25 MB.
    """
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    tid = (body.get("targetId") or "").strip()
    file_data = body.get("fileData", "")
    mibeca_sender = (body.get("mibecaSenderId") or "").strip()
    dry_run = bool(body.get("dryRun", False))
    if not (tid and file_data):
        return err_("targetId und fileData erforderlich", 400)

    # Base64 decode
    try:
        if file_data.startswith("data:"):
            file_data = file_data.split(",", 1)[1]
        raw = base64.b64decode(file_data)
        if len(raw) > 25 * 1024 * 1024:
            return err_("Datei zu gross (max 25 MB)", 400)
        export = json.loads(raw.decode("utf-8"))
    except Exception as ex:
        return err_(f"JSON konnte nicht gelesen werden: {ex}", 400)

    # Target laden
    try:
        target = dict(table_("targets").get_entity("target", tid))
    except Exception:
        return err_("Target nicht gefunden", 404)

    # Nachrichten extrahieren
    candidates = []
    if isinstance(export, list):
        candidates = export
    elif isinstance(export, dict):
        for key in ("messages", "chunk", "events", "items"):
            if isinstance(export.get(key), list):
                candidates = export[key]; break

    msgs = []
    for ev in candidates:
        if not isinstance(ev, dict): continue
        if ev.get("type") and ev.get("type") != "m.room.message": continue
        content = ev.get("content") or {}
        body_text = content.get("body") or content.get("formatted_body") or ""
        if not body_text: continue
        msgtype = content.get("msgtype", "m.text")
        if msgtype not in ("m.text", "m.notice", "m.emote", ""): continue
        sender_id = ev.get("sender", "")
        sender_name = ev.get("sender_name") or ev.get("display_name") or sender_id
        ts_ms = ev.get("origin_server_ts") or ev.get("timestamp") or 0
        try:
            datum_iso = datetime.utcfromtimestamp(ts_ms / 1000).isoformat() if ts_ms else ""
        except Exception:
            datum_iso = ""
        event_id = ev.get("event_id") or ev.get("id") or ""
        # Globale mibeca-Matrix-IDs (alle in einem Set; Vergleich case-insensitive)
        MIBECA_MATRIX_IDS = {
            "@jennifer.kaplan:matrix.mb-ak.de",
            "@m.bergmann:matrix.mb-ak.de",
            "@mb:matrix.mb-ak.de",
            "@cb:matrix.mb-ak.de",
            "@wielad.micheel:matrix.mb-ak.de",
            "@michaela.boyer:matrix.mb-ak.de",
            "@so:matrix.mb-ak.de",
            "@kw:matrix.mb-ak.de",
        }
        sender_lower = sender_id.lower()
        # 1) Sender ist in der globalen mibeca-Liste -> mibeca
        # 2) Sender stimmt mit dem optionalen mibeca_sender-Parameter ueberein -> mibeca
        ist_mibeca = sender_lower in {m.lower() for m in MIBECA_MATRIX_IDS}
        if not ist_mibeca and mibeca_sender:
            ist_mibeca = sender_id == mibeca_sender
        msgs.append({
            "event_id": event_id,
            "datum": datum_iso,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "body": body_text[:5000],
            # 'chat' als neuer Typ fuer Element/Matrix-Imports
            # (war vorher faelschlich mail_in/mail_out -> wirkte wie E-Mail)
            "typ": "chat_out" if ist_mibeca else "chat_in",
        })

    preview = [
        {"datum": m["datum"], "autor": m["sender_name"], "typ": m["typ"], "body": m["body"][:120]}
        for m in msgs[:5]
    ]

    if dry_run:
        return ok_({"foundMessages": len(msgs), "preview": preview, "dryRun": True})

    # Element-Eintraege gehen in separate Tabelle `verlaufentries`,
    # um Azure's 32K-Limit pro Feld in kommunikationJson nicht zu sprengen.
    # Jeder Eintrag wird eine eigene Entity.
    try:
        ventc = table_("verlaufentries")
    except Exception as ex:
        return err_(f"Verlauf-Tabelle nicht verfuegbar: {ex}", 500)

    # Bestehende event_ids ermitteln (sowohl in alter kommunikationJson als auch in der Tabelle)
    existing = set()
    try:
        old_verlauf = json.loads(target.get("kommunikationJson") or "[]")
        if isinstance(old_verlauf, list):
            for e in old_verlauf:
                if isinstance(e, dict) and e.get("elementEventId"):
                    existing.add(e["elementEventId"])
    except Exception:
        pass
    try:
        for e in ventc.query_entities("PartitionKey eq @t", parameters={"t": tid}):
            if e.get("elementEventId"):
                existing.add(e["elementEventId"])
    except Exception:
        pass

    neu = 0
    errors = 0
    for m in msgs:
        if m["event_id"] and m["event_id"] in existing:
            continue
        # RowKey eindeutig pro Target + event_id (oder fallback timestamp)
        import hashlib
        rk_basis = m["event_id"] or (m["datum"] + m["sender_id"])
        rk = hashlib.sha256(rk_basis.encode("utf-8")).hexdigest()[:32]
        try:
            ventc.upsert_entity({
                "PartitionKey": tid,
                "RowKey": rk,
                "typ": m["typ"],
                "datum": m["datum"],
                "autor": m["sender_name"],
                "betreff": "(Element-Import)",
                # Beschreibung auf Azure-Limit kuerzen (32K UTF-16 = ca. 30000 ASCII safe)
                "beschreibung": m["body"][:30000],
                "elementEventId": m["event_id"],
                "elementSender": m["sender_id"],
                "importedFromElement": True,
                "createdAt": datetime.utcnow().isoformat(),
            })
            neu += 1
        except Exception:
            errors += 1
    log_audit(p, "element_import", "target", tid, {"imported": neu, "found": len(msgs), "errors": errors})
    return ok_({"imported": neu, "foundMessages": len(msgs), "preview": preview,
                "skipped": len(msgs) - neu - errors, "errors": errors})


@app.route(route="verlauf-entries-get", methods=["GET", "POST", "OPTIONS"])
def verlauf_entries_get(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert kombinierten Verlauf eines Targets:
    - Eintraege aus target.kommunikationJson (klassisch, Limit 32K)
    - Eintraege aus separater Tabelle 'verlaufentries' (Element-Import, ohne Limit pro Eintrag)
    Sortiert chronologisch absteigend.
    """
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)
    if req.method == "GET":
        tid = (req.params.get("targetId") or "").strip()
    else:
        body = req.get_json() or {}
        tid = (body.get("targetId") or "").strip()
    if not tid:
        return err_("targetId erforderlich", 400)
    # IDOR-Schutz: nicht-admin nur eigene Akte
    if p.get("role") != "admin" and p.get("targetId") != tid:
        return err_("Nicht autorisiert", 403)

    eintraege = []
    # 1. Aus kommunikationJson am Target
    try:
        target = table_("targets").get_entity("target", tid)
        try:
            arr = json.loads(target.get("kommunikationJson") or "[]")
            if isinstance(arr, list):
                for e in arr:
                    if isinstance(e, dict): eintraege.append(e)
        except Exception:
            pass
    except Exception:
        return err_("Target nicht gefunden", 404)
    # 2. Aus separater Tabelle (Element-Import + ggf. spaetere groessere Eintraege)
    try:
        for e in table_("verlaufentries").query_entities("PartitionKey eq @t", parameters={"t": tid}):
            eintraege.append({
                "id": "vt" + (e.get("RowKey", "")[-12:]),
                "typ": e.get("typ", ""),
                "datum": e.get("datum", ""),
                "autor": e.get("autor", ""),
                "betreff": e.get("betreff", ""),
                "beschreibung": e.get("beschreibung", ""),
                "elementEventId": e.get("elementEventId", ""),
                "elementSender": e.get("elementSender", ""),
                "importedFromElement": e.get("importedFromElement", False),
            })
    except Exception:
        pass
    # Chronologisch absteigend
    eintraege.sort(key=lambda x: (x.get("datum", "") or ""), reverse=True)
    return ok_({"entries": eintraege, "total": len(eintraege)})


@app.route(route="ai-action", methods=["POST", "OPTIONS"])
def ai_action(req: func.HttpRequest) -> func.HttpResponse:
    """Generischer Endpoint fuer KI-Aktionen aus dem Dashboard.

    Body: { action: <name>, targetId?, kontaktId?, frage?, kontext?, conversation? }

    Unterstuetzte Aktionen:
    - verlauf-zusammenfassen: targetId -> Zusammenfassung des Kommunikationsverlaufs
    - frag-ki: frage + kontext -> Allgemeine M&A-Antwort (Chat)
    - kontakt-anreichern: kontaktId -> Vorschlaege fuer Stammdaten-Ergaenzung
    - suchprofil-schaerfen: targetId -> Rueckfragen + Konkretisierungsvorschlaege
    - match-begruendung: targetId + kontaktId -> Begruendung des Matches

    Auth:
    - frag-ki: alle eingeloggten User (admin, target, investor)
    - alle anderen: nur admin
    """
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p:
        return err_("Nicht autorisiert", 401)

    # KI global aktiv?
    if os.environ.get("AI_ANALYSE_AKTIV", "").lower() not in ("true", "1", "yes"):
        return err_("KI-Funktion ist global deaktiviert", 503)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return err_("ANTHROPIC_API_KEY nicht gesetzt", 503)

    body = req.get_json() or {}
    action = (body.get("action") or "").strip()
    if not action:
        return err_("action erforderlich", 400)

    # Rollen-Check
    is_admin = p.get("role") == "admin"
    public_actions = {"frag-ki", "suchprofil-schaerfen"}
    if action not in public_actions and not is_admin:
        return err_("Nicht autorisiert fuer diese Aktion", 403)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except Exception as ex:
        return err_(f"KI-Client nicht verfuegbar: {ex}", 500)

    def _call_claude(system_prompt, user_prompt, max_tokens=1500):
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        tokens = {
            "input": msg.usage.input_tokens if hasattr(msg, "usage") else 0,
            "output": msg.usage.output_tokens if hasattr(msg, "usage") else 0,
        }
        return text, tokens

    # --- Aktion: Verlauf zusammenfassen ---
    if action == "verlauf-zusammenfassen":
        tid = body.get("targetId", "")
        if not tid:
            return err_("targetId erforderlich", 400)
        try:
            t = table_("targets").get_entity("target", tid)
        except Exception:
            return err_("Target nicht gefunden", 404)
        # Verlauf aus BEIDEN Quellen kombinieren (wie /verlauf-entries-get)
        try:
            verlauf = json.loads(t.get("kommunikationJson", "[]") or "[]")
            if not isinstance(verlauf, list): verlauf = []
        except Exception:
            verlauf = []
        try:
            for e in table_("verlaufentries").query_entities("PartitionKey eq @t", parameters={"t": tid}):
                verlauf.append({
                    "datum": e.get("datum", ""),
                    "autor": e.get("autor", ""),
                    "typ": e.get("typ", ""),
                    "betreff": e.get("betreff", ""),
                    "beschreibung": e.get("beschreibung", ""),
                })
        except Exception:
            pass
        # Chronologisch sortieren (aelteste zuerst fuer Kontext)
        verlauf.sort(key=lambda x: (x.get("datum", "") or ""))
        if not verlauf:
            return ok_({"text": "Noch kein Verlauf vorhanden zur Zusammenfassung."})
        # Bei riesigen Verlaeufen: nur die letzten 100 Eintraege + Beschreibung pro
        # Eintrag auf 500 Zeichen gecapped, damit der Prompt unter dem Token-Limit bleibt.
        total = len(verlauf)
        recent = verlauf[-100:]
        verlauf_str = "\n\n".join(
            f"[{e.get('datum','')}] {e.get('autor','')} ({e.get('typ','')}): {e.get('betreff','')}\n{(e.get('beschreibung','') or '')[:500]}"
            for e in recent
        )
        kontext_hinweis = f"(Insgesamt {total} Eintraege im Verlauf, dies sind die letzten {len(recent)})" if total > len(recent) else ""
        system = ("Du bist Beratungs-Assistentin in einem M&A-Beratungsunternehmen (mibeca). "
                  "Deine Aufgabe ist es, den Kommunikationsverlauf einer Mandatsakte praegnant zusammenzufassen.")
        user = (
            f"Hier ist der Verlauf des Mandats {t.get('mbNr','?')} ({t.get('firma','')}). {kontext_hinweis}\n\n"
            f"{verlauf_str}\n\n"
            "Erstelle eine strukturierte Status-Zusammenfassung in folgender Form "
            "(Markdown mit ## Ueberschriften, KEINE Emojis):\n\n"
            "## Aktueller Stand\n(1-2 Saetze)\n\n"
            "## Was wurde erledigt\n(max 3 Bullet-Punkte)\n\n"
            "## Was steht aus\n(max 3 Bullet-Punkte)\n\n"
            "## Risiken / offene Themen\n(falls erkennbar)\n\n"
            "## Empfehlung naechster Schritt\n\n"
            "Halte dich knapp, max 200 Worte gesamt. Antworte auf Deutsch. KEINE Emojis."
        )
        text, tokens = _call_claude(system, user, max_tokens=1000)
        log_audit(p, "ai_action", "target", tid, {"action": action, "tokens": tokens})
        return ok_({"text": text, "tokens": tokens})

    # --- Aktion: Frag die KI (Chat) ---
    if action == "frag-ki":
        frage = (body.get("frage") or "").strip()
        if not frage:
            return err_("frage erforderlich", 400)
        if len(frage) > 2000:
            return err_("Frage zu lang (max 2000 Zeichen)", 400)
        kontext = (body.get("kontext") or "").strip()
        conversation = body.get("conversation") or []  # [{role: 'user'|'assistant', text: ...}]

        system = (
            "Du bist die KI-Assistentin im ITUKV-Dashboard von mibeca GmbH. "
            "Du hilfst Mandanten und Beratern bei Fragen zum M&A-Prozess "
            "(Unternehmenskauf/-verkauf in Deutschland). "
            "Antworte praezise, sachlich und in einfacher Sprache. "
            "Bei rechtlichen oder steuerlichen Fragen verweise auf den Anwalt/Steuerberater. "
            "Bei spezifischen Mandats-Fragen verweise auf Jenny Kaplan (jk@mike-bergmann.de). "
            "Erfinde keine Zahlen oder Fakten - sag lieber 'das weiss ich nicht' wenn unsicher."
        )
        # Conversation als messages
        messages = []
        for m in conversation[-10:]:  # max 10 letzte Turns
            role = m.get("role", "user")
            txt = (m.get("text") or "")[:2000]
            if role in ("user", "assistant") and txt:
                messages.append({"role": role, "content": txt})
        # Aktuelle Frage hinzufuegen
        user_content = frage
        if kontext:
            user_content = f"Kontext: {kontext[:1000]}\n\nFrage: {frage}"
        messages.append({"role": "user", "content": user_content})

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system,
            messages=messages,
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        tokens = {
            "input": msg.usage.input_tokens if hasattr(msg, "usage") else 0,
            "output": msg.usage.output_tokens if hasattr(msg, "usage") else 0,
        }
        log_audit(p, "ai_action", "chat", "", {"action": action, "tokens": tokens, "fragePreview": frage[:80]})
        return ok_({"text": text, "tokens": tokens})

    # --- Aktion: Kontakt anreichern ---
    if action == "kontakt-anreichern":
        kid = body.get("kontaktId", "")
        if not kid:
            return err_("kontaktId erforderlich", 400)
        try:
            k = table_("kontakte").get_entity("kontakt", kid)
        except Exception:
            return err_("Kontakt nicht gefunden", 404)
        firma = k.get("firma", "")
        if not firma:
            return err_("Kontakt hat keine Firma", 400)

        # Aktuelle Daten als JSON
        ist_daten = {
            "firma": firma,
            "geschaeftsfuehrer": k.get("geschaeftsfuehrer", ""),
            "branche": k.get("branche", ""),
            "plz": k.get("plz", ""),
            "ort": k.get("ort", ""),
            "mitarbeiter": k.get("mitarbeiter", ""),
            "umsatzTeur": k.get("umsatzTeur", ""),
            "ebitMarge": k.get("ebitMarge", ""),
            "website": k.get("website", ""),
        }
        system = ("Du bist Analystin im M&A-Bereich. Deine Aufgabe: bei einem Firmenkontakt "
                  "Stammdaten ergaenzen, sofern du sie aus allgemeinem Wissen ueber die Firma kennst. "
                  "WICHTIG: Erfinde NICHTS. Wenn du dir nicht sicher bist -> Feld leer/null.")
        user = (
            f"Aktuelle Daten des Kontakts:\n{json.dumps(ist_daten, ensure_ascii=False, indent=2)}\n\n"
            "Was kannst du aus deinem allgemeinen Wissen ergaenzen oder korrigieren? "
            "Antworte als JSON-Objekt mit den Feldern, die du belegen kannst:\n"
            '{\n'
            '  "geschaeftsfuehrer": "Name oder null",\n'
            '  "branche": "konkretere Branche oder null",\n'
            '  "plz": "PLZ oder null",\n'
            '  "ort": "Ort oder null",\n'
            '  "mitarbeiter": Zahl oder null,\n'
            '  "umsatzTeur": Zahl oder null,\n'
            '  "website": "URL oder null",\n'
            '  "begruendung": "kurze Erklaerung woher diese Infos kommen (max 2 Saetze)",\n'
            '  "konfidenz": "hoch | mittel | niedrig"\n'
            '}\n\n'
            "Nur JSON, keine zusaetzliche Erklaerung."
        )
        text, tokens = _call_claude(system, user, max_tokens=800)
        # JSON parsen
        try:
            if "```" in text:
                text = text.split("```", 2)[1].lstrip("json").strip()
                if "```" in text:
                    text = text.split("```", 1)[0].strip()
            data = json.loads(text)
        except Exception as ex:
            return ok_({"raw": text, "error": f"Antwort konnte nicht geparst werden: {ex}", "tokens": tokens})
        log_audit(p, "ai_action", "kontakt", kid, {"action": action, "tokens": tokens, "konfidenz": data.get("konfidenz", "")})
        return ok_({"vorschlaege": data, "tokens": tokens})

    # --- Aktion: Suchprofil schaerfen ---
    if action == "suchprofil-schaerfen":
        tid = body.get("targetId", "")
        if not tid:
            return err_("targetId erforderlich", 400)
        try:
            t = table_("targets").get_entity("target", tid)
        except Exception:
            return err_("Target nicht gefunden", 404)
        # IDOR: nicht-admin nur eigene Akte
        if not is_admin and p.get("targetId") != tid:
            return err_("Nicht autorisiert", 403)
        try:
            suchprofil = json.loads(t.get("suchprofilJson", "{}") or "{}")
        except Exception:
            suchprofil = {}
        try:
            akq = json.loads(t.get("akquisitionsstrategieJson", "{}") or "{}")
        except Exception:
            akq = {}

        system = ("Du bist Akquisitionsberater. Hilf einem Käufer, sein Suchprofil zu schaerfen.")
        user = (
            f"Aktuelles Suchprofil:\n{json.dumps(suchprofil, ensure_ascii=False, indent=2)}\n\n"
            f"Akquisitionsstrategie:\n{json.dumps(akq, ensure_ascii=False, indent=2)}\n\n"
            "Stelle 3-5 konkrete Rueckfragen, die dem Käufer helfen wuerden, sein Profil schaerfer zu machen. "
            "Beispiele: 'Soll der GF verbleiben?' 'Welche Branchen-Subkategorien sind ausgeschlossen?'\n\n"
            "Antworte als JSON:\n"
            '{ "fragen": ["...", "...", "..."], "begruendung": "warum diese Fragen helfen, max 2 Saetze" }'
        )
        text, tokens = _call_claude(system, user, max_tokens=600)
        try:
            if "```" in text:
                text = text.split("```", 2)[1].lstrip("json").strip()
                if "```" in text:
                    text = text.split("```", 1)[0].strip()
            data = json.loads(text)
        except Exception as ex:
            return ok_({"raw": text, "error": f"Parse-Fehler: {ex}", "tokens": tokens})
        log_audit(p, "ai_action", "target", tid, {"action": action, "tokens": tokens})
        return ok_(data | {"tokens": tokens})

    # --- Aktion: Match-Begruendung ---
    if action == "match-begruendung":
        tid = body.get("targetId", "")
        kid = body.get("kontaktId", "")
        if not (tid and kid):
            return err_("targetId und kontaktId erforderlich", 400)
        try:
            t = table_("targets").get_entity("target", tid)
            k = table_("kontakte").get_entity("kontakt", kid)
        except Exception:
            return err_("Target oder Kontakt nicht gefunden", 404)
        try:
            suchprofil = json.loads(t.get("suchprofilJson", "{}") or "{}")
        except Exception:
            suchprofil = {}

        system = "Du bist Match-Analystin im M&A-Bereich."
        user = (
            "Bewerte wie gut dieser Kontakt zu dem Suchprofil eines Käufer-Mandanten passt.\n\n"
            f"Suchprofil:\n{json.dumps(suchprofil, ensure_ascii=False, indent=2)}\n\n"
            f"Kontakt:\n{json.dumps({k_: k.get(k_, '') for k_ in ['firma','branche','plz','ort','mitarbeiter','umsatzTeur','ebitMarge','bietet']}, ensure_ascii=False, indent=2)}\n\n"
            "Antworte als JSON:\n"
            '{ "score": 0-100, "pro": ["...", "..."], "contra": ["..."], "begruendung": "kurz, max 2 Saetze" }'
        )
        text, tokens = _call_claude(system, user, max_tokens=500)
        try:
            if "```" in text:
                text = text.split("```", 2)[1].lstrip("json").strip()
                if "```" in text:
                    text = text.split("```", 1)[0].strip()
            data = json.loads(text)
        except Exception as ex:
            return ok_({"raw": text, "error": f"Parse-Fehler: {ex}", "tokens": tokens})
        log_audit(p, "ai_action", "target", tid, {"action": action, "kontaktId": kid, "tokens": tokens})
        return ok_(data | {"tokens": tokens})

    return err_(f"Unbekannte action: {action}", 400)


@app.route(route="ai-config", methods=["GET", "OPTIONS"])
def ai_config(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert den Compliance-Status der KI-Analyse:
    - aktiv: ist der globale Schalter im Azure-Setting an?
    - keyVorhanden: ist ANTHROPIC_API_KEY gesetzt?
    Beide muessen true sein, damit ein User die KI-Analyse nutzen kann."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    return ok_({
        "globalAktiv": os.environ.get("AI_ANALYSE_AKTIV", "false").lower() == "true",
        "keyVorhanden": bool(os.environ.get("ANTHROPIC_API_KEY", "")),
        "hinweis": "Aktivierung erfolgt durch Setzen von AI_ANALYSE_AKTIV=true in Azure-Function-App-Settings. Vor Aktivierung: AVV mit Anthropic, DSFA, Mandanten-Information.",
    })


@app.route(route="ai-analyze-document", methods=["POST", "OPTIONS"])
def ai_analyze_document(req: func.HttpRequest) -> func.HttpResponse:
    """Analysiert ein hochgeladenes Dokument (PDF) mit Claude und schlaegt
    extrahierte Werte vor. Schreibt NICHTS in die DB - liefert nur Vorschlaege.
    Der Admin uebernimmt die Werte dann selbst per Knopfdruck.

    Body: { targetId, blobName, kind?='auto' } - blobName ist der relative
    Pfad im 'datenraum'-Container.
    """
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return err_("KI-Analyse ist noch nicht konfiguriert. Bitte ANTHROPIC_API_KEY in Azure-Function-App-Settings hinterlegen.", 503)
    # Globaler Sicherheits-Schalter: KI-Analyse muss in Settings explizit aktiviert sein.
    # Default = aus, bis AVV + DSFA abgeschlossen sind.
    if os.environ.get("AI_ANALYSE_AKTIV", "false").lower() != "true":
        return err_("KI-Analyse ist im Dashboard deaktiviert (Compliance-Schalter). Aktivierung durch Admin in Einstellungen.", 403)
    body = req.get_json() or {}
    tid = (body.get("targetId") or "").strip()
    blob_name = (body.get("blobName") or "").strip()
    if not (tid and blob_name):
        return err_("targetId + blobName erforderlich", 400)
    # Pro-Akte-Opt-In: User muss diese Akte explizit fuer KI-Analyse freigegeben haben
    try:
        target_ent = dict(table_("targets").get_entity("target", tid))
    except Exception:
        return err_("Target nicht gefunden", 404)
    if not target_ent.get("kiAnalyseErlaubt"):
        return err_("Diese Akte ist nicht fuer KI-Analyse freigegeben. Bitte in der Akte oben den KI-Schalter aktivieren.", 403)
    # PDF aus Blob laden
    try:
        from azure.storage.blob import BlobServiceClient
        svc = BlobServiceClient.from_connection_string(TABLE_CONN)
        blob = svc.get_blob_client("datenraum", blob_name)
        pdf_bytes = blob.download_blob().readall()
    except Exception as ex:
        return err_(f"Dokument nicht ladbar: {ex}", 404)
    # PDF-Limit auf 10 MB reduziert (vorher 30): bei groesseren Dateien
    # ist die Wahrscheinlichkeit hoeher, dass sensible Anhaenge enthalten sind,
    # die nicht zur reinen Kennzahlen-Analyse gebraucht werden.
    if len(pdf_bytes) > 10 * 1024 * 1024:
        return err_("PDF zu gross (max 10 MB fuer KI-Analyse). Bitte gezielt auswaehlen.", 400)

    # Claude aufrufen
    try:
        import anthropic
        import base64 as _b64
        client = anthropic.Anthropic(api_key=api_key)
        pdf_b64 = _b64.b64encode(pdf_bytes).decode()
        prompt = (
            "Du bekommst ein deutsches Geschaeftsdokument (BWA, Jahresabschluss, "
            "Handelsregisterauszug, Unternehmens-Exposé o.ä.). Extrahiere folgende Felder "
            "und gib NUR strukturiertes JSON zurueck (keine Erklaerung, kein Fließtext).\n\n"
            "JSON-Schema:\n"
            "{\n"
            '  "geschaeftsfuehrer": "Vor + Nachname, oder leer",\n'
            '  "branche": "z.B. IT-Systemhaus, Softwareentwicklung, etc.",\n'
            '  "mitarbeiter": Zahl oder null,\n'
            '  "umsatzTeur": Zahl in Tausend Euro oder null (z.B. 2500 für 2,5 Mio),\n'
            '  "ebitMarge": Zahl in % oder null,\n'
            '  "recurringPct": Zahl in % wiederkehrender Umsaetze oder null,\n'
            '  "rechtsform": "GmbH, AG, etc.",\n'
            '  "gruendungsjahr": Zahl oder null,\n'
            '  "kennzahlenText": "Knappe Zusammenfassung der wichtigsten Kennzahlen (max 3 Saetze)",\n'
            '  "dokumentTyp": "BWA | Jahresabschluss | Handelsregister | Expose | Sonstige"\n'
            "}\n\n"
            "Wichtig: Wenn ein Feld nicht zweifelsfrei erkennbar ist, setze null/leer. "
            "Keine Schaetzungen, nur was klar im Dokument steht."
        )
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        raw_text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        # JSON aus der Antwort extrahieren (Claude umrahmt manchmal mit ```json)
        import re as _re
        m = _re.search(r"\{[\s\S]*\}", raw_text)
        if not m:
            return err_(f"KI hat keine strukturierte Antwort geliefert. Roh: {raw_text[:300]}", 500)
        extracted = json.loads(m.group(0))
    except json.JSONDecodeError as ex:
        return err_(f"KI-Antwort nicht parsebar: {ex}", 500)
    except Exception as ex:
        return err_(f"KI-Analyse fehlgeschlagen: {ex}", 500)

    log_audit(p, "ai_analyze", "target", tid, {
        "blobName": blob_name,
        "dokumentTyp": extracted.get("dokumentTyp", ""),
        "tokens": getattr(msg, "usage", {}).input_tokens if hasattr(msg, "usage") else 0,
    })
    return ok_({
        "extracted": extracted,
        "dokumentTyp": extracted.get("dokumentTyp", ""),
        "tokens": {
            "input": msg.usage.input_tokens if hasattr(msg, "usage") else 0,
            "output": msg.usage.output_tokens if hasattr(msg, "usage") else 0,
        },
    })


@app.route(route="ai-stats", methods=["GET", "OPTIONS"])
def ai_stats(req: func.HttpRequest) -> func.HttpResponse:
    """Health-Check + Quota-Info fuer KI-Service-Account."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") not in ("ai-agent", "admin"):
        return err_("Nicht autorisiert", 401)
    # Heute schon laufende ai_update-Eintraege zaehlen
    today_iso = datetime.utcnow().date().isoformat()
    count_today = 0
    try:
        for e in table_("auditlog").list_entities():
            if e.get("action") == "ai_update" and (e.get("ts", "") or "").startswith(today_iso):
                count_today += 1
    except Exception:
        pass
    return ok_({
        "user": p.get("name", ""),
        "role": p.get("role", ""),
        "updatesToday": count_today,
        "dailyLimit": 1000,
        "writableKontaktFields": sorted(AI_WRITABLE_KONTAKT_FIELDS),
        "writableTargetFields": sorted(AI_WRITABLE_TARGET_FIELDS),
    })


# ============================================================
# DRIP-SEQUENZEN — automatische Mail-Folge an Interessenten
# ============================================================
# Datenmodell:
# - Tabelle 'dripsequenzen': PartitionKey='seq', RowKey=uuid
#     name, schritte (JSON-Array: [{tag, vorlageRowKey, name}])
# - Interessent-Felder:
#     dripSequenzId, dripGestartetAm, dripPausiert, dripNaechsterSchritt,
#     dripLetzterVersandAm

@app.route(route="dripsequenzen", methods=["GET", "POST", "OPTIONS"])
def dripsequenzen_route(req: func.HttpRequest) -> func.HttpResponse:
    """GET: alle Drip-Sequenzen. POST: anlegen/aktualisieren."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    tc = table_("dripsequenzen")
    if req.method == "GET":
        items = [dict(i) for i in tc.list_entities()]
        # Default-Sequenz seeden falls noch keine vorhanden
        if not items:
            default = {
                "PartitionKey": "seq", "RowKey": str(uuid.uuid4()),
                "name": "Standard 3-Stufen-Folge (3 / 7 / 14 Tage)",
                "beschreibung": "Erste Erinnerung nach 3 Tagen, dann 7, dann 14 — automatisch via Tagestakt",
                "schritte": json.dumps([
                    {"tag": 3, "name": "Tag 3: freundliche Erinnerung", "vorlageRowKey": ""},
                    {"tag": 7, "name": "Tag 7: zweiter Hinweis", "vorlageRowKey": ""},
                    {"tag": 14, "name": "Tag 14: letzte Erinnerung", "vorlageRowKey": ""},
                ], ensure_ascii=False),
                "updatedAt": datetime.utcnow().isoformat(),
            }
            try:
                tc.create_entity(default)
                items = [default]
            except Exception:
                pass
        for it in items:
            try: it["schritte"] = json.loads(it.get("schritte", "[]") or "[]")
            except: it["schritte"] = []
        return ok_(items)
    # POST – Sequenz anlegen/aktualisieren
    body = req.get_json() or {}
    sid = (body.get("id") or str(uuid.uuid4()))
    schritte = body.get("schritte") or []
    if not isinstance(schritte, list) or not schritte:
        return err_("schritte erforderlich", 400)
    ent = {
        "PartitionKey": "seq", "RowKey": sid,
        "name": body.get("name", "Unbenannt"),
        "beschreibung": body.get("beschreibung", ""),
        "schritte": json.dumps(schritte, ensure_ascii=False),
        "updatedAt": datetime.utcnow().isoformat(),
    }
    try:
        tc.upsert_entity(ent)
        log_audit(p, "upsert", "dripsequenz", sid, {"schritte": len(schritte)})
        return ok_({"id": sid, "ok": True})
    except Exception as ex:
        return err_(f"Speichern fehlgeschlagen: {ex}", 500)


@app.route(route="dripsequenz-delete", methods=["POST", "OPTIONS"])
def dripsequenz_delete(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    sid = body.get("id") or ""
    if not sid: return err_("id erforderlich", 400)
    try:
        table_("dripsequenzen").delete_entity("seq", sid)
        log_audit(p, "delete", "dripsequenz", sid)
        return ok_({"deleted": sid})
    except Exception as ex:
        return err_(f"Loeschen fehlgeschlagen: {ex}", 500)


@app.route(route="drip-start", methods=["POST", "OPTIONS"])
def drip_start(req: func.HttpRequest) -> func.HttpResponse:
    """Startet eine Drip-Sequenz fuer einen Interessenten."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    interessent_id = body.get("interessentId") or ""
    sid = body.get("sequenzId") or ""
    if not (interessent_id and sid):
        return err_("interessentId + sequenzId erforderlich", 400)
    tc = table_("interessenten")
    try:
        # Interessent suchen (PartitionKey ist variabel)
        i_ent = None
        for i in tc.list_entities():
            if i.get("RowKey") == interessent_id:
                i_ent = dict(i)
                break
        if not i_ent:
            return err_("Interessent nicht gefunden", 404)
        i_ent["dripSequenzId"] = sid
        i_ent["dripGestartetAm"] = datetime.utcnow().isoformat()
        i_ent["dripNaechsterSchritt"] = 0
        i_ent["dripPausiert"] = False
        i_ent["dripLetzterVersandAm"] = ""
        tc.update_entity(i_ent)
        log_audit(p, "start", "drip", interessent_id, {"sequenzId": sid})
        return ok_({"ok": True})
    except Exception as ex:
        return err_(f"Start fehlgeschlagen: {ex}", 500)


@app.route(route="drip-pause", methods=["POST", "OPTIONS"])
def drip_pause(req: func.HttpRequest) -> func.HttpResponse:
    """Pausiert oder stoppt eine Drip-Sequenz."""
    if req.method == "OPTIONS":
        return opt_()
    p = auth_user(req)
    if not p or p.get("role") != "admin":
        return err_("Nicht autorisiert", 401)
    body = req.get_json() or {}
    interessent_id = body.get("interessentId") or ""
    action = body.get("action") or "pause"  # pause/resume/stop
    if not interessent_id: return err_("interessentId erforderlich", 400)
    tc = table_("interessenten")
    try:
        i_ent = None
        for i in tc.list_entities():
            if i.get("RowKey") == interessent_id:
                i_ent = dict(i)
                break
        if not i_ent: return err_("Interessent nicht gefunden", 404)
        if action == "pause": i_ent["dripPausiert"] = True
        elif action == "resume": i_ent["dripPausiert"] = False
        elif action == "stop":
            i_ent["dripSequenzId"] = ""
            i_ent["dripPausiert"] = False
        tc.update_entity(i_ent)
        log_audit(p, action, "drip", interessent_id)
        return ok_({"ok": True})
    except Exception as ex:
        return err_(f"Update fehlgeschlagen: {ex}", 500)


@app.timer_trigger(schedule="0 0 8 * * *", arg_name="dripTimer", run_on_startup=False, use_monitor=True)
def daily_drip_send(dripTimer: func.TimerRequest) -> None:
    """Laeuft taeglich 08:00 UTC. Pruefe alle Interessenten mit aktiver
    Drip-Sequenz und sende den naechsten Schritt wenn die Tage erreicht sind."""
    logging.info("[DRIP] daily_drip_send start")
    if not ACS_CONN:
        logging.warning("[DRIP] ACS_CONN fehlt, breche ab")
        return
    today = datetime.utcnow().date()
    # Sequenzen laden
    sequenzen = {}
    try:
        for s in table_("dripsequenzen").list_entities():
            try: schritte = json.loads(s.get("schritte", "[]") or "[]")
            except: schritte = []
            sequenzen[s["RowKey"]] = {
                "name": s.get("name", ""),
                "schritte": schritte,
            }
    except Exception as ex:
        logging.error(f"[DRIP] Sequenzen nicht ladbar: {ex}")
        return
    # Mailvorlagen
    vorlagen = {}
    try:
        for v in table_("mailvorlagen").list_entities():
            vorlagen[v["RowKey"]] = dict(v)
    except Exception:
        pass

    tc_i = table_("interessenten")
    sent = 0
    try:
        from azure.communication.email import EmailClient
        client = EmailClient.from_connection_string(ACS_CONN)
    except Exception as ex:
        logging.error(f"[DRIP] ACS-Client init fehlgeschlagen: {ex}")
        return

    for i in tc_i.list_entities():
        sid = i.get("dripSequenzId", "") or ""
        if not sid: continue
        if i.get("dripPausiert"): continue
        seq = sequenzen.get(sid)
        if not seq: continue
        schritte = seq.get("schritte", [])
        naechster = int(i.get("dripNaechsterSchritt", 0) or 0)
        if naechster >= len(schritte):
            # Sequenz beendet → Feld zurücksetzen
            try:
                i_full = dict(i)
                i_full["dripSequenzId"] = ""
                tc_i.update_entity(i_full)
            except Exception: pass
            continue
        schritt = schritte[naechster]
        try:
            gestartet = datetime.fromisoformat(i.get("dripGestartetAm", "")[:19]).date()
        except Exception:
            continue
        tage_seit_start = (today - gestartet).days
        if tage_seit_start < int(schritt.get("tag", 0) or 0):
            continue  # noch nicht dran
        # Versenden
        empfaenger = i.get("email", "") or ""
        if not empfaenger:
            continue
        vorlage = vorlagen.get(schritt.get("vorlageRowKey", "")) or {}
        # Variablen-Ersetzung
        target_id = i.get("targetId", "")
        target = {}
        try:
            target = dict(table_("targets").get_entity("target", target_id))
        except Exception: pass
        vars_ = {
            "firma": i.get("firma", "") or "",
            "name": i.get("name", "") or "",
            "vorname": (i.get("name", "") or "").split(" ")[0],
            "mbNr": target.get("mbNr", ""),
            "absender": "mibeca",
        }
        def sub(s):
            import re as _r
            return _r.sub(r"\{\{(\w+)\}\}", lambda m: vars_.get(m.group(1), ""), s or "")
        subj = sub(vorlage.get("betreff", schritt.get("name", "Folge-Information")))
        body_txt = sub(vorlage.get("body", ""))
        html_body = f"<html><body style='font-family:Arial,sans-serif;color:#161e2a;line-height:1.5'><pre style='font-family:Arial;white-space:pre-wrap'>{body_txt}</pre></body></html>"
        try:
            client.begin_send({
                "senderAddress": ACS_SENDER,
                "recipients": {"to": [{"address": empfaenger}]},
                "content": {"subject": subj, "plainText": body_txt, "html": html_body},
            })
            sent += 1
            # Update Interessent
            i_full = dict(i)
            i_full["dripNaechsterSchritt"] = naechster + 1
            i_full["dripLetzterVersandAm"] = datetime.utcnow().isoformat()
            tc_i.update_entity(i_full)
            # Verlauf-Eintrag
            if target_id:
                try:
                    t_full = dict(table_("targets").get_entity("target", target_id))
                    verlauf = json.loads(t_full.get("kommunikationJson", "[]") or "[]")
                    verlauf.append({
                        "id": "drip" + str(int(datetime.utcnow().timestamp() * 1000)),
                        "typ": "mail_out",
                        "datum": datetime.utcnow().isoformat(),
                        "autor": "Drip-Sequenz",
                        "betreff": f"Drip: {subj}",
                        "beschreibung": f"Automatischer Versand (Schritt {naechster+1}/{len(schritte)}) an {empfaenger}",
                        "beteiligte": i.get("firma", "") or i.get("name", ""),
                        "createdBy": "system",
                    })
                    t_full["kommunikationJson"] = json.dumps(verlauf, ensure_ascii=False)
                    table_("targets").update_entity(t_full)
                except Exception as ex:
                    logging.warning(f"[DRIP] Verlauf-Eintrag fehlgeschlagen: {ex}")
        except Exception as ex:
            logging.warning(f"[DRIP] Versand fehlgeschlagen an {empfaenger}: {ex}")
    logging.info(f"[DRIP] fertig, {sent} Mails verschickt")
