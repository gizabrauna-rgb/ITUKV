import azure.functions as func
import json
import logging
import os
import uuid
import hmac
import hashlib
import base64
import secrets
import csv
import io
from datetime import datetime, timedelta
from azure.data.tables import TableServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

TABLE_CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, x-functions-key",
    "Content-Type": "application/json",
}

CHECKLISTEN_PER_TYP = {
    "UVE Target": [
        {"id": "1", "label": "Unternehmensbewertung", "done": False},
        {"id": "2", "label": "Fragebogen Unternehmensbewertung", "done": False},
        {"id": "3", "label": "Exposé erstellt", "done": False},
        {"id": "4", "label": "Mandat unterschrieben", "done": False},
        {"id": "5", "label": "Element-Raum eröffnet", "done": False},
        {"id": "6", "label": "Target beworben", "done": False},
        {"id": "7", "label": "Eingehende NDAs geprüft", "done": False},
        {"id": "8", "label": "Alle Dokumente vollständig", "done": False},
    ],
    "Projekt Target": [
        {"id": "1", "label": "Unternehmensbewertung", "done": False},
        {"id": "2", "label": "Fragebogen Unternehmensbewertung", "done": False},
        {"id": "3", "label": "Exposé erstellt", "done": False},
        {"id": "4", "label": "Mandat unterschrieben", "done": False},
        {"id": "5", "label": "Element-Raum eröffnet", "done": False},
        {"id": "6", "label": "Target beworben", "done": False},
        {"id": "7", "label": "Alle Dokumente vollständig", "done": False},
    ],
    "MC Target": [
        {"id": "1", "label": "M&A-Mandat unterschrieben", "done": False},
        {"id": "2", "label": "Unternehmensbewertung", "done": False},
        {"id": "3", "label": "Detail-Exposé erstellt", "done": False},
        {"id": "4", "label": "Datenraum vorbereitet", "done": False},
        {"id": "5", "label": "Käufer-Longlist erstellt", "done": False},
        {"id": "6", "label": "Ansprache durchgeführt", "done": False},
        {"id": "7", "label": "NDAs geprüft", "done": False},
        {"id": "8", "label": "Erstgespräche geführt", "done": False},
    ],
    "Projekt Investoren": [
        {"id": "1", "label": "NDA unterzeichnet", "done": False},
        {"id": "2", "label": "Leadliste zusammenstellen", "done": False},
        {"id": "3", "label": "Element-Raum eröffnen", "done": False},
    ],
    "MC Investoren": [
        {"id": "1", "label": "NDA unterzeichnet", "done": False},
        {"id": "2", "label": "Investmentprofil festgelegt", "done": False},
        {"id": "3", "label": "Leadliste zusammenstellen", "done": False},
        {"id": "4", "label": "Element-Raum / Datenraum geöffnet", "done": False},
        {"id": "5", "label": "Erstgespräch mit Verkäufer", "done": False},
        {"id": "6", "label": "Indikatives Angebot abgegeben", "done": False},
    ],
}
DEFAULT_CHECKLISTE = CHECKLISTEN_PER_TYP["Projekt Target"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def ok(data, status=200):
    return func.HttpResponse(json.dumps(data, default=str), status_code=status, headers=CORS)

def err(msg, status=400):
    return func.HttpResponse(json.dumps({"error": msg}), status_code=status, headers=CORS)

def opt():
    return func.HttpResponse("", status_code=204, headers=CORS)

def table(name):
    svc = TableServiceClient.from_connection_string(TABLE_CONN)
    svc.create_table_if_not_exists(name)
    return svc.get_table_client(name)

def new_id():
    return str(uuid.uuid4())

def now():
    return datetime.utcnow().isoformat()


# ── JWT (stdlib) ─────────────────────────────────────────────────────────────

def _b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode('ascii')

def _b64ud(s):
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def jwt_encode(payload, key):
    header = {"alg": "HS256", "typ": "JWT"}
    clean = {k: (int(v.timestamp()) if isinstance(v, datetime) else v) for k, v in payload.items()}
    h = _b64u(json.dumps(header, separators=(',',':')).encode())
    p = _b64u(json.dumps(clean, separators=(',',':'), default=str).encode())
    sig = hmac.new(key.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64u(sig)}"

def jwt_decode(token, key):
    h, p, s = token.split('.')
    expected = hmac.new(key.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64ud(s), expected):
        raise Exception("Invalid signature")
    payload = json.loads(_b64ud(p))
    if 'exp' in payload and datetime.utcnow().timestamp() > payload['exp']:
        raise Exception("Token expired")
    return payload


def make_jwt(uid, role, name, email, extra=None):
    payload = {"id": uid, "role": role, "name": name, "email": email,
               "exp": datetime.utcnow() + timedelta(days=7)}
    if extra:
        payload.update(extra)
    return jwt_encode(payload, JWT_SECRET)


def auth_user(req):
    a = req.headers.get("Authorization", "")
    if not a.startswith("Bearer "):
        return None
    try:
        return jwt_decode(a[7:], JWT_SECRET)
    except Exception:
        return None

def auth(req, roles=None):
    p = auth_user(req)
    if not p:
        return None, err("Nicht autorisiert", 401)
    if roles and p.get("role") not in roles:
        return None, err("Keine Berechtigung", 403)
    return p, None


# ── Password hashing (PBKDF2 stdlib) ─────────────────────────────────────────

def hash_password(pw):
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 100000)
    return "pbkdf2$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(h).decode()

def check_password(pw, hashed):
    try:
        prefix, salt_b64, hash_b64 = hashed.split("$")
        if prefix != "pbkdf2":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        actual = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 100000)
        return hmac.compare_digest(expected, actual)
    except Exception:
        return False


# ── Health Check ─────────────────────────────────────────────────────────────

@app.route(route="ping", methods=["GET"])
def ping(req: func.HttpRequest) -> func.HttpResponse:
    return ok({"status": "ok", "time": now()})


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.route(route="auth/resolve", methods=["POST", "OPTIONS"])
def auth_resolve(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    try:
        body = req.get_json()
        email = body.get("email", "").lower().strip()
        name = body.get("name", "")
        if not email:
            return err("E-Mail erforderlich", 400)
        tc = table("users")
        users = list(tc.query_entities(f"email eq '{email}'"))
        if users:
            u = users[0]
            extra = {}
            if u.get("targetId"):
                extra["targetId"] = u["targetId"]
            token = make_jwt(u["RowKey"], u["role"], u.get("name", name), email, extra)
            return ok({"token": token, "role": u["role"], "name": u.get("name", name),
                       "id": u["RowKey"], **extra})
        uid = new_id()
        entity = {
            "PartitionKey": "user", "RowKey": uid, "email": email,
            "passwordHash": "", "role": "admin", "name": name,
            "targetId": "", "customerId": "",
            "createdAt": now(), "loginVia": "microsoft",
        }
        tc.create_entity(entity)
        return ok({"token": make_jwt(uid, "admin", name, email),
                   "role": "admin", "name": name, "id": uid})
    except Exception as e:
        logging.error(str(e))
        return err(f"Interner Fehler: {e}", 500)


@app.route(route="login", methods=["POST", "OPTIONS"])
def login(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    try:
        body = req.get_json()
        email = body.get("email", "").lower().strip()
        password = body.get("password", "")
        tc = table("users")
        users = list(tc.query_entities(f"email eq '{email}'"))
        if not users:
            return err("E-Mail oder Passwort falsch", 401)
        u = users[0]
        if not check_password(password, u.get("passwordHash", "")):
            return err("E-Mail oder Passwort falsch", 401)
        extra = {}
        if u.get("targetId"):
            extra["targetId"] = u["targetId"]
        token = make_jwt(u["RowKey"], u["role"], u.get("name", ""), email, extra)
        return ok({"token": token, "role": u["role"], "name": u.get("name", ""),
                   "id": u["RowKey"], **extra})
    except Exception as e:
        logging.error(str(e))
        return err("Interner Fehler", 500)


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.route(route="stats", methods=["GET", "OPTIONS"])
def stats(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    try:
        t_count = sum(1 for _ in table("targets").list_entities())
        k_count = sum(1 for _ in table("kontakte").list_entities())
        ndas = sum(1 for i in table("interessenten").list_entities() if i.get("ndaStatus") == "gesendet")
        deals = sum(1 for i in table("targets").list_entities() if i.get("status") == "verkauft")
        return ok({"aktiveTargets": t_count, "offeneNdas": ndas,
                   "investorenGesamt": k_count, "dealsAbgeschlossen": deals})
    except Exception as e:
        logging.error(str(e))
        return ok({"aktiveTargets": 0, "offeneNdas": 0, "investorenGesamt": 0, "dealsAbgeschlossen": 0})


# ── Targets ──────────────────────────────────────────────────────────────────

@app.route(route="targets", methods=["GET", "POST", "OPTIONS"])
def targets(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("targets")
    if req.method == "GET":
        items = [dict(i) for i in tc.list_entities()]
        return ok(items)
    body = req.get_json()
    tid = new_id()
    projekttyp = body.get("projekttyp", "Projekt Target")
    checkliste = CHECKLISTEN_PER_TYP.get(projekttyp, DEFAULT_CHECKLISTE)
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
        "projekttyp": projekttyp,
        "status": "verfuegbar",
        "checklisteJson": json.dumps(checkliste),
        "createdAt": now(),
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


@app.route(route="targets/{target_id}", methods=["GET", "PATCH", "OPTIONS"])
def target_detail(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p = auth_user(req)
    if not p:
        return err("Nicht autorisiert", 401)
    tc = table("targets")
    try:
        entity = tc.get_entity("target", target_id)
    except Exception:
        return err("Target nicht gefunden", 404)
    if req.method == "GET":
        return ok(dict(entity))
    body = req.get_json()
    for k, v in body.items():
        if k not in ("PartitionKey", "RowKey"):
            entity[k] = v
    tc.update_entity(dict(entity))
    return ok(dict(entity))


@app.route(route="targets/{target_id}/checkliste", methods=["PATCH", "OPTIONS"])
def checkliste_update(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p = auth_user(req)
    if not p:
        return err("Nicht autorisiert", 401)
    tc = table("targets")
    try:
        entity = tc.get_entity("target", target_id)
    except Exception:
        return err("Target nicht gefunden", 404)
    body = req.get_json()
    items = json.loads(entity.get("checklisteJson", "[]"))
    for item in items:
        if item["id"] == body.get("id"):
            item["done"] = body.get("done", item["done"])
    entity["checklisteJson"] = json.dumps(items)
    tc.update_entity(dict(entity))
    return ok(items)


# ── Kontakte (CRM) ────────────────────────────────────────────────────────────

@app.route(route="kontakte", methods=["GET", "POST", "OPTIONS"])
def kontakte(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("kontakte")
    if req.method == "GET":
        items = [dict(i) for i in tc.list_entities()]
        typ = req.params.get("typ")
        plz = req.params.get("plz")
        search = req.params.get("search", "").lower()
        if typ:
            items = [i for i in items if i.get("typ") == typ]
        if plz:
            items = [i for i in items if str(i.get("plz", "")).startswith(plz)]
        if search:
            items = [i for i in items if search in (i.get("firma","") + i.get("name","") + i.get("email","")).lower()]
        return ok(items)
    body = req.get_json()
    kid = new_id()
    entity = {
        "PartitionKey": "kontakt", "RowKey": kid,
        "name": body.get("name", ""), "firma": body.get("firma", ""),
        "email": body.get("email", ""), "telefon": body.get("telefon", ""),
        "plz": body.get("plz", ""), "ort": body.get("ort", ""),
        "typ": body.get("typ", "Sonstige"),
        "sucht": body.get("sucht", ""), "bietet": body.get("bietet", ""),
        "kommentar": body.get("kommentar", ""),
        "herkunft": body.get("herkunft", ""),
        "createdAt": now(), "updatedAt": now(),
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


@app.route(route="kontakte/{kid}", methods=["PATCH", "OPTIONS"])
def kontakt_update(req: func.HttpRequest, kid: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("kontakte")
    try:
        entity = tc.get_entity("kontakt", kid)
    except Exception:
        return err("Kontakt nicht gefunden", 404)
    body = req.get_json()
    for k, v in body.items():
        if k not in ("PartitionKey", "RowKey"):
            entity[k] = v
    entity["updatedAt"] = now()
    tc.update_entity(dict(entity))
    return ok(dict(entity))


@app.route(route="kontakte/export", methods=["GET", "OPTIONS"])
def kontakte_export(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    items = [dict(i) for i in table("kontakte").list_entities()]
    out = io.StringIO() if False else __import__('io').StringIO()
    fields = ["firma","name","email","telefon","plz","ort","typ","sucht","bietet","kommentar","herkunft"]
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(items)
    return func.HttpResponse(
        out.getvalue(),
        status_code=200,
        headers={**CORS, "Content-Type": "text/csv",
                 "Content-Disposition": "attachment; filename=kontakte.csv"}
    )


# ── Users ─────────────────────────────────────────────────────────────────────

@app.route(route="users", methods=["GET", "POST", "OPTIONS"])
def users_list(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("users")
    if req.method == "GET":
        items = [dict(u) for u in tc.list_entities()]
        for u in items:
            u.pop("passwordHash", None)
        items.sort(key=lambda x: x.get("createdAt",""), reverse=True)
        return ok(items)
    body = req.get_json()
    email = body.get("email","").lower().strip()
    if not email:
        return err("E-Mail erforderlich", 400)
    existing = list(tc.query_entities(f"email eq '{email}'"))
    if existing:
        return err("E-Mail bereits registriert", 409)
    import string
    pw = body.get("password") or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    uid = new_id()
    entity = {
        "PartitionKey": "user", "RowKey": uid, "email": email,
        "passwordHash": hash_password(pw),
        "role": body.get("role", "target"),
        "name": body.get("name", ""),
        "targetId": body.get("targetId", ""),
        "customerId": body.get("customerId", ""),
        "createdAt": now(), "loginVia": "password",
    }
    tc.create_entity(entity)
    result = {k: v for k, v in entity.items() if k != "passwordHash"}
    result["initialPassword"] = pw
    return ok(result, 201)


@app.route(route="users/{uid}", methods=["GET", "PATCH", "DELETE", "OPTIONS"])
def user_detail(req: func.HttpRequest, uid: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("users")
    try:
        entity = tc.get_entity("user", uid)
    except Exception:
        return err("Benutzer nicht gefunden", 404)
    if req.method == "GET":
        out = dict(entity); out.pop("passwordHash", None)
        return ok(out)
    if req.method == "DELETE":
        tc.delete_entity("user", uid)
        return ok({"deleted": True})
    body = req.get_json()
    for k, v in body.items():
        if k in ("PartitionKey", "RowKey", "passwordHash"):
            continue
        entity[k] = v
    entity["updatedAt"] = now()
    tc.update_entity(dict(entity))
    out = dict(entity); out.pop("passwordHash", None)
    return ok(out)


@app.route(route="users/{uid}/reset-password", methods=["POST", "OPTIONS"])
def user_reset_password(req: func.HttpRequest, uid: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("users")
    try:
        entity = tc.get_entity("user", uid)
    except Exception:
        return err("Benutzer nicht gefunden", 404)
    import string
    body = req.get_json() or {}
    pw = body.get("password") or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    entity["passwordHash"] = hash_password(pw)
    entity["updatedAt"] = now()
    tc.update_entity(dict(entity))
    return ok({"email": entity.get("email"), "newPassword": pw})


# ── Settings / Webhook-Info ───────────────────────────────────────────────────

@app.route(route="settings/webhook", methods=["GET", "OPTIONS"])
def settings_webhook(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    return ok({
        "url": "https://itukv-func-v2.azurewebsites.net/api/webhook/kunde",
        "token": WEBHOOK_SECRET,
        "headerName": "X-Webhook-Token",
    })


# ── Webhook für Kunden-Import ─────────────────────────────────────────────────

@app.route(route="webhook/kunde", methods=["POST", "OPTIONS"])
def webhook_kunde(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    token = req.headers.get("X-Webhook-Token", "") or req.params.get("token", "")
    if not WEBHOOK_SECRET or token != WEBHOOK_SECRET:
        return err("Ungültiger Webhook-Token", 401)
    try:
        body = req.get_json()
        items = body if isinstance(body, list) else [body]
        import re
        tc_k = table("kontakte"); tc_t = table("targets")
        targets_count = 0; kontakte_count = 0
        for item in items:
            email = (item.get("email","") or "").lower().strip()
            mbNr_raw = item.get("mbNr","") or ""
            mbNr = ""
            if mbNr_raw:
                m = re.search(r"mb-?(\d+)", str(mbNr_raw), re.IGNORECASE)
                if m: mbNr = f"mb-{m.group(1)}"
            name = item.get("name","") or f"{item.get('vorname','')} {item.get('nachname','')}".strip()
            firma = item.get("firma","") or item.get("firmenname","")
            if mbNr:
                existing = list(tc_t.query_entities(f"mbNr eq '{mbNr}'"))
                if existing:
                    entity = existing[0]
                else:
                    entity = {"PartitionKey": "target", "RowKey": new_id(), "mbNr": mbNr,
                              "checklisteJson": json.dumps(DEFAULT_CHECKLISTE),
                              "createdAt": now(), "status": "verfuegbar",
                              "projekttyp": item.get("projekttyp","Projekt Target")}
                entity.update({"verkaueferName": name or firma, "firma": firma, "email": email,
                               "telefon": item.get("telefon",""), "plz": item.get("plz",""),
                               "region": item.get("region","") or item.get("ort",""),
                               "branche": item.get("branche","IT-Systemhaus"),
                               "mitarbeiter": str(item.get("mitarbeiter","")),
                               "umsatz": item.get("umsatz",""),
                               "beschreibung": item.get("beschreibung","") or item.get("notizen",""),
                               "updatedAt": now()})
                tc_t.upsert_entity(entity)
                targets_count += 1
                continue
            if not email:
                continue
            existing = list(tc_k.query_entities(f"email eq '{email}'"))
            if existing:
                entity = existing[0]
            else:
                entity = {"PartitionKey": "kontakt", "RowKey": new_id(), "createdAt": now()}
            entity.update({"name": name, "firma": firma, "email": email,
                           "telefon": item.get("telefon",""), "website": item.get("website",""),
                           "plz": item.get("plz",""), "ort": item.get("ort",""),
                           "typ": item.get("typ","Sonstige"), "sucht": item.get("sucht",""),
                           "bietet": item.get("bietet",""),
                           "kommentar": item.get("notizen","") or item.get("kommentar",""),
                           "herkunft": item.get("herkunft","Webhook"),
                           "kundenstatus": item.get("kundenstatus",""),
                           "kundennummer": item.get("kundennummer",""),
                           "updatedAt": now()})
            tc_k.upsert_entity(entity)
            kontakte_count += 1
        return ok({"success": True, "targets": targets_count, "kontakte": kontakte_count})
    except Exception as e:
        logging.error(str(e))
        return err(f"Fehler: {e}", 500)


# ── Interessenten ─────────────────────────────────────────────────────────────

@app.route(route="targets/{target_id}/interessenten", methods=["GET", "POST", "OPTIONS"])
def interessenten(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    tc = table("interessenten")
    if req.method == "GET":
        p = auth_user(req)
        if not p: return err("Nicht autorisiert", 401)
        items = [dict(i) for i in tc.query_entities(f"targetId eq '{target_id}'")]
        return ok(items)
    body = req.get_json()
    iid = new_id()
    entity = {
        "PartitionKey": target_id, "RowKey": iid, "targetId": target_id,
        "name": body.get("name", ""), "firma": body.get("firma", ""),
        "email": body.get("email", ""), "telefon": body.get("telefon", ""),
        "plz": body.get("plz", ""), "ort": body.get("ort", ""),
        "nachricht": body.get("nachricht", ""),
        "ndaStatus": "ausstehend", "pipelineStatus": "neu",
        "rating": 0, "veto": False, "vetoBegruendung": "",
        "aktuellesGebot": "", "notizen": "", "ansprache": "Sie",
        "freigegebenFuerKontakt": False,
        "timestampRegistrierung": now(),
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


@app.route(route="targets/{target_id}/interessenten/{iid}", methods=["PATCH", "OPTIONS"])
def interessent_update(req: func.HttpRequest, target_id: str, iid: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p = auth_user(req)
    if not p: return err("Nicht autorisiert", 401)
    tc = table("interessenten")
    try:
        entity = tc.get_entity(target_id, iid)
    except Exception:
        return err("Interessent nicht gefunden", 404)
    body = req.get_json()
    for k, v in body.items():
        if k not in ("PartitionKey", "RowKey"):
            entity[k] = v
    tc.update_entity(dict(entity))
    return ok(dict(entity))


# ── Kontakte Locations (DACH-Karte) ───────────────────────────────────────────

_PLZ_COORDS = None
def get_plz_coords():
    global _PLZ_COORDS
    if _PLZ_COORDS is not None:
        return _PLZ_COORDS
    _PLZ_COORDS = {}
    try:
        csv_path = os.path.join(os.path.dirname(__file__), "plz_geocoord.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                country = (row.get("country") or "DE").strip()
                plz = (row.get("plz") or "").strip()
                if not plz:
                    continue
                try:
                    _PLZ_COORDS[f"{country}:{plz}"] = (float(row["lat"]), float(row["lon"]))
                    if country == "DE" and plz not in _PLZ_COORDS:
                        _PLZ_COORDS[plz] = (float(row["lat"]), float(row["lon"]))
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        logging.error(f"PLZ-CSV: {e}")
    return _PLZ_COORDS


@app.route(route="kontakte/locations", methods=["GET", "OPTIONS"])
def kontakte_locations(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    coords = get_plz_coords()
    items = [dict(i) for i in table("kontakte").list_entities()]
    with_coords = []
    without_coords = 0
    for k in items:
        plz = str(k.get("plz","")).strip()
        c = coords.get(f"DE:{plz}") or coords.get(plz)
        if c:
            with_coords.append({
                "id": k.get("RowKey"),
                "firma": k.get("firma","") or k.get("name",""),
                "name": k.get("name",""), "email": k.get("email",""),
                "telefon": k.get("telefon",""),
                "plz": k.get("plz",""), "ort": k.get("ort",""),
                "typ": k.get("typ",""),
                "lat": c[0], "lon": c[1],
            })
        else:
            without_coords += 1
    return ok({"kontakte": with_coords, "total": len(items), "withoutCoords": without_coords})


# ── Checkliste-Vorlage ────────────────────────────────────────────────────────

@app.route(route="checkliste-vorlage/{typ}", methods=["GET", "OPTIONS"])
def checkliste_vorlage(req: func.HttpRequest, typ: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return opt()
    p = auth_user(req)
    if not p: return err("Nicht autorisiert", 401)
    return ok(CHECKLISTEN_PER_TYP.get(typ, DEFAULT_CHECKLISTE))
