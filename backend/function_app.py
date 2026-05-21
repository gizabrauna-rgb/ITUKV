import azure.functions as func
import json
import logging
import os
import uuid
import csv
import io
import jwt
import bcrypt
from datetime import datetime, timedelta
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

TABLE_CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING", "")
BLOB_CONN  = os.environ.get("AZURE_BLOB_STORAGE_CONNECTION_STRING", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
BLOB_CONTAINER = "dokumente"

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, x-functions-key",
    "Content-Type": "application/json",
}

# PLZ → Koordinaten (lazy geladen aus CSV)
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
                    lat = float(row["lat"])
                    lon = float(row["lon"])
                    _PLZ_COORDS[f"{country}:{plz}"] = (lat, lon)
                    # auch ohne country-prefix
                    if country == "DE" and plz not in _PLZ_COORDS:
                        _PLZ_COORDS[plz] = (lat, lon)
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        logging.error(f"PLZ-CSV laden fehlgeschlagen: {e}")
    return _PLZ_COORDS

def plz_to_coords(plz, country="DE"):
    if not plz:
        return None
    coords = get_plz_coords()
    plz_clean = str(plz).strip()
    return coords.get(f"{country}:{plz_clean}") or coords.get(plz_clean)


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
        {"id": "9", "label": "Gebote erhalten", "done": False},
        {"id": "10", "label": "Due Diligence vorbereitet", "done": False},
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
        {"id": "7", "label": "Due Diligence durchgeführt", "done": False},
    ],
}
DEFAULT_CHECKLISTE = CHECKLISTEN_PER_TYP["Projekt Target"]


def get_checkliste_for_typ(projekttyp):
    return CHECKLISTEN_PER_TYP.get(projekttyp, DEFAULT_CHECKLISTE)

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

def decode_token(req):
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        return jwt.decode(auth[7:], JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None

def auth(req, roles=None):
    p = decode_token(req)
    if not p:
        return None, err("Nicht autorisiert", 401)
    if roles and p.get("role") not in roles:
        return None, err("Keine Berechtigung", 403)
    return p, None

def make_jwt(uid, role, name, email, extra=None):
    payload = {"id": uid, "role": role, "name": name, "email": email,
               "exp": datetime.utcnow() + timedelta(days=7)}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def new_id():
    return str(uuid.uuid4())

def now():
    return datetime.utcnow().isoformat()

# ── Auth ─────────────────────────────────────────────────────────────────────

@app.route(route="auth/resolve", methods=["POST", "OPTIONS"])
def auth_resolve(req: func.HttpRequest) -> func.HttpResponse:
    """Nach Microsoft-Login: User in DB suchen und Rolle zurückgeben.
    Wenn nicht vorhanden → admin (mibeca-Team)."""
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
            if u.get("targetId"): extra["targetId"] = u["targetId"]
            if u.get("customerId"): extra["customerId"] = u["customerId"]
            token = make_jwt(u["RowKey"], u["role"], u.get("name", name), email, extra)
            return ok({"token": token, "role": u["role"],
                       "name": u.get("name", name), "id": u["RowKey"], **extra})
        # Nicht in DB → automatisch Admin (mibeca-Team)
        uid = new_id()
        entity = {
            "PartitionKey": "user", "RowKey": uid,
            "email": email, "passwordHash": "",
            "role": "admin", "name": name,
            "targetId": "", "customerId": "",
            "createdAt": now(), "loginVia": "microsoft",
        }
        tc.create_entity(entity)
        token = make_jwt(uid, "admin", name, email)
        return ok({"token": token, "role": "admin", "name": name, "id": uid})
    except Exception as e:
        logging.error(str(e))
        return err("Interner Fehler", 500)


@app.route(route="login", methods=["POST", "OPTIONS"])
def login(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    try:
        body = req.get_json()
        email = body.get("email", "").lower().strip()
        password = body.get("password", "")
        tc = table("users")
        users = list(tc.query_entities(f"email eq '{email}'"))
        if not users:
            return err("E-Mail oder Passwort falsch", 401)
        u = users[0]
        if not bcrypt.checkpw(password.encode(), u["passwordHash"].encode()):
            return err("E-Mail oder Passwort falsch", 401)
        extra = {}
        if u.get("targetId"): extra["targetId"] = u["targetId"]
        if u.get("customerId"): extra["customerId"] = u["customerId"]
        token = make_jwt(u["RowKey"], u["role"], u["name"], email, extra)
        return ok({"token": token, "role": u["role"], "name": u["name"],
                   "id": u["RowKey"], **extra})
    except Exception as e:
        logging.error(str(e))
        return err("Interner Fehler", 500)


@app.route(route="register", methods=["POST", "OPTIONS"])
def register(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    try:
        body = req.get_json()
        email = body.get("email", "").lower().strip()
        tc = table("users")
        existing = list(tc.query_entities(f"email eq '{email}'"))
        if existing:
            return err("E-Mail bereits registriert", 409)
        pw_hash = bcrypt.hashpw(body["password"].encode(), bcrypt.gensalt()).decode()
        uid = new_id()
        entity = {
            "PartitionKey": "user", "RowKey": uid,
            "email": email, "passwordHash": pw_hash,
            "role": body.get("role", "investor"),
            "name": body.get("name", ""),
            "targetId": body.get("targetId", ""),
            "customerId": body.get("customerId", ""),
            "createdAt": now(),
        }
        tc.create_entity(entity)
        return ok({"id": uid, "email": email, "role": entity["role"]}, 201)
    except Exception as e:
        logging.error(str(e))
        return err("Interner Fehler", 500)


# ── User Management (Admin) ───────────────────────────────────────────────────

@app.route(route="users", methods=["GET", "POST", "OPTIONS"])
def users_list(req: func.HttpRequest) -> func.HttpResponse:
    """Liste aller Benutzer (admin only) + neuer Benutzer anlegen."""
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("users")
    if req.method == "GET":
        items = [dict(u) for u in tc.list_entities()]
        # Passwort-Hash niemals zurückgeben
        for u in items:
            u.pop("passwordHash", None)
        items.sort(key=lambda x: x.get("createdAt",""), reverse=True)
        return ok(items)
    # POST – Neuer User mit Initial-Passwort
    body = req.get_json()
    email = body.get("email","").lower().strip()
    if not email:
        return err("E-Mail erforderlich", 400)
    existing = list(tc.query_entities(f"email eq '{email}'"))
    if existing:
        return err("E-Mail bereits registriert", 409)
    # Initial-Passwort: vom Admin gesetzt oder zufällig generiert
    import secrets, string
    pw = body.get("password") or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    uid = new_id()
    entity = {
        "PartitionKey": "user", "RowKey": uid,
        "email": email,
        "passwordHash": pw_hash,
        "role": body.get("role", "target"),
        "name": body.get("name", ""),
        "targetId": body.get("targetId", ""),
        "customerId": body.get("customerId", ""),
        "createdAt": now(),
        "loginVia": "password",
    }
    tc.create_entity(entity)
    result = {k: v for k, v in entity.items() if k != "passwordHash"}
    result["initialPassword"] = pw  # nur einmal beim Anlegen zurückgeben
    return ok(result, 201)


@app.route(route="users/{uid}", methods=["GET", "PATCH", "DELETE", "OPTIONS"])
def user_detail(req: func.HttpRequest, uid: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("users")
    try:
        entity = tc.get_entity("user", uid)
    except Exception:
        return err("Benutzer nicht gefunden", 404)
    if req.method == "GET":
        out = dict(entity)
        out.pop("passwordHash", None)
        return ok(out)
    if req.method == "DELETE":
        tc.delete_entity("user", uid)
        return ok({"deleted": True})
    # PATCH
    body = req.get_json()
    for k, v in body.items():
        if k in ("PartitionKey", "RowKey", "passwordHash"):
            continue
        entity[k] = v
    entity["updatedAt"] = now()
    tc.update_entity(dict(entity))
    out = dict(entity)
    out.pop("passwordHash", None)
    return ok(out)


@app.route(route="users/{uid}/reset-password", methods=["POST", "OPTIONS"])
def user_reset_password(req: func.HttpRequest, uid: str) -> func.HttpResponse:
    """Generiert ein neues Passwort für einen Benutzer und gibt es einmal zurück."""
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("users")
    try:
        entity = tc.get_entity("user", uid)
    except Exception:
        return err("Benutzer nicht gefunden", 404)
    import secrets, string
    body = req.get_json() or {}
    pw = body.get("password") or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    entity["passwordHash"] = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    entity["updatedAt"] = now()
    tc.update_entity(dict(entity))
    return ok({"email": entity.get("email"), "newPassword": pw})


# ── Targets ──────────────────────────────────────────────────────────────────

@app.route(route="targets", methods=["GET", "POST", "OPTIONS"])
def targets(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("targets")
    if req.method == "GET":
        items = [dict(i) for i in tc.list_entities()]
        return ok(items)
    body = req.get_json()
    tid = new_id()
    projekttyp = body.get("projekttyp", "Projekt Target")
    checkliste = json.dumps(get_checkliste_for_typ(projekttyp))
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
        "checklisteJson": checkliste,
        "createdAt": now(),
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


# Default-Checkliste pro Projekttyp abrufen
@app.route(route="checkliste-vorlage/{typ}", methods=["GET", "OPTIONS"])
def checkliste_vorlage(req: func.HttpRequest, typ: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    return ok(get_checkliste_for_typ(typ))


# ── Links (pro Target / Investor) ────────────────────────────────────────────

@app.route(route="targets/{target_id}/links", methods=["GET", "POST", "OPTIONS"])
def links(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    tc = table("links")
    if req.method == "GET":
        items = [dict(i) for i in tc.query_entities(f"targetId eq '{target_id}'")]
        items.sort(key=lambda x: x.get("createdAt",""))
        return ok(items)
    body = req.get_json()
    lid = new_id()
    entity = {
        "PartitionKey": target_id,
        "RowKey": lid,
        "targetId": target_id,
        "titel": body.get("titel",""),
        "url": body.get("url",""),
        "beschreibung": body.get("beschreibung",""),
        "kategorie": body.get("kategorie","Allgemein"),
        "createdAt": now(),
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


@app.route(route="targets/{target_id}/links/{lid}", methods=["PATCH", "DELETE", "OPTIONS"])
def link_detail(req: func.HttpRequest, target_id: str, lid: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    tc = table("links")
    try:
        entity = tc.get_entity(target_id, lid)
    except Exception:
        return err("Link nicht gefunden", 404)
    if req.method == "DELETE":
        tc.delete_entity(target_id, lid)
        return ok({"deleted": True})
    body = req.get_json()
    for k, v in body.items():
        if k not in ("PartitionKey", "RowKey"):
            entity[k] = v
    tc.update_entity(dict(entity))
    return ok(dict(entity))


@app.route(route="targets/{target_id}", methods=["GET", "PATCH", "OPTIONS"])
def target_detail(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
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
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
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


# ── Interessenten ─────────────────────────────────────────────────────────────

@app.route(route="targets/{target_id}/interessenten", methods=["GET", "POST", "OPTIONS"])
def interessenten(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    if req.method == "GET":
        p, e = auth(req, roles=["admin", "target"])
        if e: return e
        tc = table("interessenten")
        items = [dict(i) for i in tc.query_entities(f"targetId eq '{target_id}'")]
        return ok(items)
    # POST – öffentlich (Investor registriert Interesse)
    try:
        body = req.get_json()
        iid = new_id()
        tc = table("interessenten")
        entity = {
            "PartitionKey": target_id, "RowKey": iid,
            "targetId": target_id,
            "name": body.get("name", ""),
            "firma": body.get("firma", ""),
            "email": body.get("email", ""),
            "telefon": body.get("telefon", ""),
            "plz": body.get("plz", ""),
            "ort": body.get("ort", ""),
            "nachricht": body.get("nachricht", ""),
            "ndaStatus": "ausstehend",
            "ndaZohoSignId": "",
            "pipelineStatus": "neu",
            "rating": 0,
            "veto": False,
            "vetoBegruendung": "",
            "aktuellesGebot": "",
            "notizen": "",
            "bemerkungen": "",
            "ansprache": "Sie",
            "freigegebenFuerKontakt": False,
            "timestampRegistrierung": now(),
        }
        tc.create_entity(entity)
        return ok(dict(entity), 201)
    except Exception as ex:
        logging.error(str(ex))
        return err("Fehler beim Registrieren", 500)


@app.route(route="targets/{target_id}/interessenten/{iid}", methods=["PATCH", "OPTIONS"])
def interessent_update(req: func.HttpRequest, target_id: str, iid: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin", "target"])
    if e: return e
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


# ── CRM / Kontakte ────────────────────────────────────────────────────────────

@app.route(route="kontakte", methods=["GET", "POST", "OPTIONS"])
def kontakte(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("kontakte")
    if req.method == "GET":
        items = [dict(i) for i in tc.list_entities()]
        # Filter
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
        "name": body.get("name", ""),
        "firma": body.get("firma", ""),
        "email": body.get("email", ""),
        "telefon": body.get("telefon", ""),
        "plz": body.get("plz", ""),
        "ort": body.get("ort", ""),
        "typ": body.get("typ", "Sonstige"),
        "sucht": body.get("sucht", ""),
        "bietet": body.get("bietet", ""),
        "kommentar": body.get("kommentar", ""),
        "herkunft": body.get("herkunft", ""),
        "createdAt": now(),
        "updatedAt": now(),
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


@app.route(route="kontakte/import", methods=["POST", "OPTIONS"])
def kontakte_import(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    try:
        body = req.get_json()
        items = body if isinstance(body, list) else body.get("items", [])
        tc = table("kontakte")
        count = 0
        for item in items:
            rid = item.pop("id", new_id())
            entity = {"PartitionKey": "kontakt", "RowKey": rid, "updatedAt": now()}
            entity.update({k: v for k, v in item.items() if k not in ("PartitionKey","RowKey")})
            tc.upsert_entity(entity)
            count += 1
        return ok({"imported": count})
    except Exception as ex:
        logging.error(str(ex))
        return err("Import fehlgeschlagen", 500)


@app.route(route="kontakte/locations", methods=["GET", "OPTIONS"])
def kontakte_locations(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert Kontakte mit lat/lon (für DACH-Karte). Filterbar nach typ, kategorie."""
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("kontakte")
    items = [dict(i) for i in tc.list_entities()]
    typ = req.params.get("typ")
    if typ:
        items = [i for i in items if i.get("typ") == typ]
    total = len(items)
    with_coords = []
    without_coords = 0
    for k in items:
        c = plz_to_coords(k.get("plz",""))
        if c:
            with_coords.append({
                "id": k.get("RowKey"),
                "firma": k.get("firma","") or k.get("name",""),
                "name": k.get("name",""),
                "email": k.get("email",""),
                "telefon": k.get("telefon",""),
                "plz": k.get("plz",""),
                "ort": k.get("ort",""),
                "typ": k.get("typ",""),
                "kundenstatus": k.get("kundenstatus",""),
                "lat": c[0], "lon": c[1],
            })
        else:
            without_coords += 1
    return ok({"kontakte": with_coords, "total": total, "withoutCoords": without_coords})


@app.route(route="kontakte/export", methods=["GET", "OPTIONS"])
def kontakte_export(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("kontakte")
    items = [dict(i) for i in tc.list_entities()]
    output = io.StringIO()
    fields = ["firma","name","email","telefon","plz","ort","typ","sucht","bietet","kommentar","herkunft"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(items)
    return func.HttpResponse(
        output.getvalue(),
        status_code=200,
        headers={**CORS, "Content-Type": "text/csv",
                 "Content-Disposition": "attachment; filename=kontakte.csv"}
    )


@app.route(route="kontakte/{kid}", methods=["PATCH", "OPTIONS"])
def kontakt_update(req: func.HttpRequest, kid: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("kontakte")
    try:
        entity = tc.get_entity("kontakt", kid)
    except Exception:
        return err("Kontakt nicht gefunden", 404)
    body = req.get_json()
    for k, v in body.items():
        if k not in ("PartitionKey","RowKey"):
            entity[k] = v
    entity["updatedAt"] = now()
    tc.update_entity(dict(entity))
    return ok(dict(entity))


# ── Ausschreibungen ───────────────────────────────────────────────────────────

@app.route(route="ausschreibungen", methods=["GET", "POST", "OPTIONS"])
def ausschreibungen(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    tc = table("ausschreibungen")
    if req.method == "GET":
        items = [dict(i) for i in tc.query_entities("status eq 'aktiv'")]
        # Für Investoren anonymisieren
        if p.get("role") == "investor":
            for item in items:
                item.pop("verkaueferName", None)
        return ok(items)
    # POST – admin only
    if p.get("role") != "admin":
        return err("Keine Berechtigung", 403)
    body = req.get_json()
    aid = new_id()
    entity = {
        "PartitionKey": "ausschreibung", "RowKey": aid,
        "targetId": body.get("targetId",""),
        "mbNr": body.get("mbNr",""),
        "titel": body.get("titel",""),
        "kurzprofil": body.get("kurzprofil",""),
        "region": body.get("region",""),
        "mitarbeiter": str(body.get("mitarbeiter","")),
        "umsatz": body.get("umsatz",""),
        "branche": body.get("branche",""),
        "status": "aktiv",
        "exposeFile": "",
        "datenraumFreigaben": "",
        "createdAt": now(),
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


@app.route(route="ausschreibungen/{aid}", methods=["GET", "PATCH", "OPTIONS"])
def ausschreibung_detail(req: func.HttpRequest, aid: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    tc = table("ausschreibungen")
    try:
        entity = tc.get_entity("ausschreibung", aid)
    except Exception:
        return err("Ausschreibung nicht gefunden", 404)
    if req.method == "GET":
        return ok(dict(entity))
    if p.get("role") != "admin":
        return err("Keine Berechtigung", 403)
    body = req.get_json()
    for k, v in body.items():
        if k not in ("PartitionKey","RowKey"):
            entity[k] = v
    tc.update_entity(dict(entity))
    return ok(dict(entity))


@app.route(route="ausschreibungen/{aid}/expose", methods=["POST", "OPTIONS"])
def request_expose(req: func.HttpRequest, aid: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    try:
        body = req.get_json()
        # Interessenten-Eintrag erstellen und NDA senden (Zoho Sign Platzhalter)
        tc_a = table("ausschreibungen")
        ausschr = tc_a.get_entity("ausschreibung", aid)
        target_id = ausschr.get("targetId", aid)

        zoho_id = f"ZOHO-{new_id()[:8].upper()}"
        iid = new_id()
        tc_i = table("interessenten")
        entity = {
            "PartitionKey": target_id, "RowKey": iid,
            "targetId": target_id,
            "ausschreibungId": aid,
            "name": body.get("name", p.get("name","")),
            "firma": body.get("firma",""),
            "email": body.get("email", p.get("email","")),
            "telefon": body.get("telefon",""),
            "plz": body.get("plz",""),
            "ort": body.get("ort",""),
            "nachricht": "",
            "ndaStatus": "gesendet",
            "ndaZohoSignId": zoho_id,
            "pipelineStatus": "nda",
            "rating": 0, "veto": False, "vetoBegruendung": "",
            "aktuellesGebot": "", "notizen": "", "bemerkungen": "",
            "ansprache": "Sie", "freigegebenFuerKontakt": False,
            "timestampRegistrierung": now(),
        }
        tc_i.create_entity(entity)
        return ok({"message": "NDA wurde per E-Mail gesendet.", "ndaId": zoho_id, "interessentId": iid})
    except Exception as ex:
        logging.error(str(ex))
        return err("Fehler", 500)


@app.route(route="ausschreibungen/{aid}/datenraum/freigabe", methods=["POST", "OPTIONS"])
def datenraum_freigabe(req: func.HttpRequest, aid: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    body = req.get_json()
    investor_id = body.get("investorId","")
    tc = table("ausschreibungen")
    entity = tc.get_entity("ausschreibung", aid)
    freigaben = entity.get("datenraumFreigaben","")
    ids = [i for i in freigaben.split(",") if i]
    if investor_id not in ids:
        ids.append(investor_id)
    entity["datenraumFreigaben"] = ",".join(ids)
    tc.update_entity(dict(entity))
    return ok({"datenraumFreigaben": ids})


# ── NDA ───────────────────────────────────────────────────────────────────────

@app.route(route="nda/{ausschreibung_id}", methods=["GET", "OPTIONS"])
def nda_status(req: func.HttpRequest, ausschreibung_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    tc = table("interessenten")
    items = list(tc.query_entities(f"ausschreibungId eq '{ausschreibung_id}' and email eq '{p.get('email','')}'"))
    if not items:
        return ok({"status": "keine_anfrage"})
    return ok({"status": items[0].get("ndaStatus","ausstehend"), "id": items[0]["RowKey"]})


@app.route(route="nda/webhook", methods=["POST", "OPTIONS"])
def nda_webhook(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    try:
        body = req.get_json()
        zoho_id = body.get("documentId","")
        status = body.get("status","")
        tc = table("interessenten")
        # Alle partitionen durchsuchen (vereinfacht)
        for pk in ["interessent"]:
            items = list(tc.query_entities(f"ndaZohoSignId eq '{zoho_id}'"))
            for item in items:
                item["ndaStatus"] = "unterzeichnet" if status == "completed" else "abgelehnt"
                tc.update_entity(dict(item))
        return ok({"updated": True})
    except Exception as ex:
        logging.error(str(ex))
        return ok({"updated": False})


# ── Dokumente ─────────────────────────────────────────────────────────────────

@app.route(route="targets/{target_id}/dokumente", methods=["GET", "OPTIONS"])
def dokumente_list(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    tc = table("dokumente")
    items = [dict(i) for i in tc.query_entities(f"targetId eq '{target_id}'")]
    ordner = req.params.get("ordner")
    if ordner:
        items = [i for i in items if i.get("ordner") == ordner]
    return ok(items)


@app.route(route="targets/{target_id}/dokumente/upload", methods=["POST", "OPTIONS"])
def dokument_upload(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    try:
        ordner = req.params.get("ordner", "Diverses")
        dateiname = req.params.get("dateiname", f"datei_{new_id()[:8]}")
        blob_path = f"{target_id}/{ordner}/{dateiname}"
        blob_svc = BlobServiceClient.from_connection_string(BLOB_CONN)
        container = blob_svc.get_container_client(BLOB_CONTAINER)
        container.upload_blob(blob_path, req.get_body(), overwrite=True)
        did = new_id()
        tc = table("dokumente")
        entity = {
            "PartitionKey": target_id, "RowKey": did,
            "targetId": target_id, "ordner": ordner,
            "dateiname": dateiname, "blobPath": blob_path,
            "hochgeladenVon": p.get("name",""),
            "hochgeladenAm": now(),
            "groesse": str(len(req.get_body())),
        }
        tc.create_entity(entity)
        return ok(dict(entity), 201)
    except Exception as ex:
        logging.error(str(ex))
        return err("Upload fehlgeschlagen", 500)


@app.route(route="targets/{target_id}/dokumente/{did}/download", methods=["GET", "OPTIONS"])
def dokument_download(req: func.HttpRequest, target_id: str, did: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req)
    if e: return e
    tc = table("dokumente")
    try:
        entity = tc.get_entity(target_id, did)
    except Exception:
        return err("Dokument nicht gefunden", 404)
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    from azure.storage.blob import BlobServiceClient as BSC
    import re
    conn = BLOB_CONN
    account_match = re.search(r'AccountName=([^;]+)', conn)
    key_match = re.search(r'AccountKey=([^;]+)', conn)
    account_name = account_match.group(1) if account_match else ""
    account_key = key_match.group(1) if key_match else ""
    sas = generate_blob_sas(
        account_name=account_name,
        container_name=BLOB_CONTAINER,
        blob_name=entity["blobPath"],
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1),
    )
    url = f"https://{account_name}.blob.core.windows.net/{BLOB_CONTAINER}/{entity['blobPath']}?{sas}"
    return ok({"url": url, "dateiname": entity["dateiname"]})


@app.route(route="targets/{target_id}/dokumente/{did}", methods=["DELETE", "OPTIONS"])
def dokument_delete(req: func.HttpRequest, target_id: str, did: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin", "target"])
    if e: return e
    tc = table("dokumente")
    try:
        entity = tc.get_entity(target_id, did)
        blob_svc = BlobServiceClient.from_connection_string(BLOB_CONN)
        blob_svc.get_blob_client(BLOB_CONTAINER, entity["blobPath"]).delete_blob()
        tc.delete_entity(target_id, did)
        return ok({"deleted": True})
    except Exception as ex:
        logging.error(str(ex))
        return err("Löschen fehlgeschlagen", 500)


# ── Webhook CRM Sync ──────────────────────────────────────────────────────────

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

def check_webhook_secret(req):
    """Prüft Webhook-Token im Header X-Webhook-Token oder Query-Param ?token=."""
    token = req.headers.get("X-Webhook-Token", "") or req.params.get("token", "")
    if not WEBHOOK_SECRET:
        return False, err("WEBHOOK_SECRET nicht konfiguriert", 500)
    if token != WEBHOOK_SECRET:
        return False, err("Ungültiger Webhook-Token", 401)
    return True, None


@app.route(route="webhook/kunde", methods=["POST", "OPTIONS"])
def webhook_kunde(req: func.HttpRequest) -> func.HttpResponse:
    """
    Webhook für neue/aktualisierte Kunden aus deinem CRM.

    Authentifizierung: Header `X-Webhook-Token: <secret>` ODER ?token=<secret>

    Body: Einzelnes Objekt oder Array von Objekten mit den Feldern:
    - email (Pflicht – wird zum Deduplizieren genutzt)
    - firma, vorname, nachname, name
    - telefon, website
    - plz, ort, land
    - kundennummer, kundenstatus
    - mbNr (optional – wenn vorhanden, wird ein Target angelegt)
    - notizen, beschreibung, herkunft
    - sucht, bietet, typ (PE/Systemhausgruppe/Strategisch/Sonstige)

    Antwort: { "targets": N, "kontakte": N, "details": [...] }
    """
    if req.method == "OPTIONS": return opt()
    ok_secret, err_resp = check_webhook_secret(req)
    if not ok_secret: return err_resp

    try:
        body = req.get_json()
        items = body if isinstance(body, list) else [body]

        tc_kontakte = table("kontakte")
        tc_targets = table("targets")

        result_targets = 0
        result_kontakte = 0
        details = []

        import re
        for item in items:
            email = (item.get("email","") or "").lower().strip()
            mbNr_raw = item.get("mbNr","") or ""

            # mb-Nummer normalisieren
            mbNr = ""
            if mbNr_raw:
                m = re.search(r"mb-?(\d+)", str(mbNr_raw), re.IGNORECASE)
                if m:
                    mbNr = f"mb-{m.group(1)}"

            name = item.get("name","") or f"{item.get('vorname','')} {item.get('nachname','')}".strip()
            firma = item.get("firma","") or item.get("firmenname","")

            # === TARGET wenn mb-Nummer vorhanden ===
            if mbNr:
                # Existiert bereits?
                existing = list(tc_targets.query_entities(f"mbNr eq '{mbNr}'"))
                if existing:
                    target_id = existing[0]["RowKey"]
                    entity = existing[0]
                else:
                    target_id = new_id()
                    entity = {
                        "PartitionKey": "target",
                        "RowKey": target_id,
                        "mbNr": mbNr,
                        "checklisteJson": json.dumps(DEFAULT_CHECKLISTE),
                        "createdAt": now(),
                        "status": "verfuegbar",
                        "projekttyp": item.get("projekttyp","Projekt Target"),
                    }
                # Felder updaten/setzen
                entity.update({
                    "verkaueferName": name or firma,
                    "firma": firma,
                    "email": email,
                    "telefon": item.get("telefon",""),
                    "website": item.get("website",""),
                    "region": item.get("ort","") or item.get("region",""),
                    "plz": item.get("plz",""),
                    "branche": item.get("branche","IT-Systemhaus"),
                    "mitarbeiter": str(item.get("mitarbeiter","")),
                    "umsatz": item.get("umsatz",""),
                    "beschreibung": item.get("beschreibung","") or item.get("notizen",""),
                    "updatedAt": now(),
                })
                tc_targets.upsert_entity(entity)
                result_targets += 1
                details.append({"type": "target", "mbNr": mbNr, "id": target_id})
                continue

            # === KONTAKT (CRM) ===
            if not email:
                details.append({"type": "skipped", "reason": "no email"})
                continue

            existing = list(tc_kontakte.query_entities(f"email eq '{email}'"))
            if existing:
                kontakt_id = existing[0]["RowKey"]
                entity = existing[0]
            else:
                kontakt_id = new_id()
                entity = {
                    "PartitionKey": "kontakt",
                    "RowKey": kontakt_id,
                    "createdAt": now(),
                }
            entity.update({
                "name": name,
                "firma": firma,
                "email": email,
                "telefon": item.get("telefon",""),
                "website": item.get("website",""),
                "plz": item.get("plz",""),
                "ort": item.get("ort",""),
                "typ": item.get("typ","Sonstige"),
                "sucht": item.get("sucht",""),
                "bietet": item.get("bietet",""),
                "kommentar": item.get("notizen","") or item.get("kommentar",""),
                "herkunft": item.get("herkunft","Webhook"),
                "kundenstatus": item.get("kundenstatus",""),
                "kundennummer": item.get("kundennummer",""),
                "updatedAt": now(),
            })
            tc_kontakte.upsert_entity(entity)
            result_kontakte += 1
            details.append({"type": "kontakt", "email": email, "id": kontakt_id})

        return ok({
            "success": True,
            "targets": result_targets,
            "kontakte": result_kontakte,
            "total": len(items),
            "details": details,
        })

    except Exception as ex:
        logging.error(f"webhook/kunde: {ex}")
        return err(f"Webhook fehlgeschlagen: {ex}", 500)


# Alter Endpoint bleibt aus Kompatibilitäts-Gründen
@app.route(route="webhook/crm", methods=["POST", "OPTIONS"])
def webhook_crm(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    ok_secret, err_resp = check_webhook_secret(req)
    if not ok_secret: return err_resp
    try:
        body = req.get_json()
        items = body if isinstance(body, list) else body.get("items", [])
        tc = table("kontakte")
        count = 0
        for item in items:
            rid = item.pop("id", new_id())
            entity = {"PartitionKey": "kontakt", "RowKey": rid, "updatedAt": now()}
            entity.update({k: v for k, v in item.items() if k not in ("PartitionKey","RowKey")})
            tc.upsert_entity(entity)
            count += 1
        return ok({"synced": count})
    except Exception as ex:
        logging.error(str(ex))
        return err("Webhook fehlgeschlagen", 500)


# ── Erfolgsmeldungen / PR-Mitteilungen ────────────────────────────────────────

@app.route(route="pr-mitteilungen", methods=["GET", "POST", "OPTIONS"])
def pr_mitteilungen(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("prmitteilungen")
    if req.method == "GET":
        items = [dict(i) for i in tc.list_entities()]
        items.sort(key=lambda x: x.get("createdAt",""), reverse=True)
        return ok(items)
    body = req.get_json()
    pid = new_id()
    entity = {
        "PartitionKey": "pr", "RowKey": pid,
        "targetId": body.get("targetId",""),
        "mbNr": body.get("mbNr",""),
        "titel": body.get("titel",""),
        "kurzText": body.get("kurzText",""),
        "langText": body.get("langText",""),
        "linkedInText": body.get("linkedInText",""),
        "anonymisiert": body.get("anonymisiert", True),
        "status": "entwurf",
        "createdAt": now(),
        "versendetAm": "",
        "empfaengerCount": 0,
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


@app.route(route="pr-mitteilungen/{pid}", methods=["GET", "PATCH", "DELETE", "OPTIONS"])
def pr_mitteilung_detail(req: func.HttpRequest, pid: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("prmitteilungen")
    try:
        entity = tc.get_entity("pr", pid)
    except Exception:
        return err("PR-Mitteilung nicht gefunden", 404)
    if req.method == "GET":
        return ok(dict(entity))
    if req.method == "DELETE":
        tc.delete_entity("pr", pid)
        return ok({"deleted": True})
    body = req.get_json()
    for k, v in body.items():
        if k not in ("PartitionKey","RowKey"):
            entity[k] = v
    tc.update_entity(dict(entity))
    return ok(dict(entity))


@app.route(route="pr-mitteilungen/{pid}/generate", methods=["POST", "OPTIONS"])
def pr_generate(req: func.HttpRequest, pid: str) -> func.HttpResponse:
    """Generiert Text-Vorschlag aus Target-Daten (Vorlage – KI später)."""
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    body = req.get_json() or {}
    target_id = body.get("targetId","")
    anonym = body.get("anonymisiert", True)
    if not target_id:
        return err("targetId erforderlich", 400)
    try:
        target = dict(table("targets").get_entity("target", target_id))
    except Exception:
        return err("Target nicht gefunden", 404)

    mbNr = target.get("mbNr","")
    branche = target.get("branche","IT-Systemhaus") or "IT-Systemhaus"
    region = target.get("region","")
    mitarbeiter = target.get("mitarbeiter","")
    umsatz = target.get("umsatz","")
    verkaeufer = target.get("verkaueferName","") if not anonym else ""

    # Titel
    titel = f"Erfolgreicher Unternehmensverkauf abgeschlossen"
    if mbNr:
        titel += f" ({mbNr})"

    # Kurz-Text (für LinkedIn, Newsletter-Header)
    kurz_parts = [f"Wir freuen uns mitteilen zu dürfen, dass ein weiterer Unternehmensverkauf im IT-Sektor erfolgreich abgeschlossen wurde."]
    if region:
        kurz_parts.append(f"Das verkaufte Unternehmen ist im Raum {region} ansässig.")
    if mitarbeiter:
        kurz_parts.append(f"Es beschäftigt {mitarbeiter} Mitarbeitende.")
    kurz = " ".join(kurz_parts)

    # Lang-Text (für Pressemitteilung / Newsletter)
    lang_lines = [
        f"PRESSEMITTEILUNG",
        f"",
        f"Erfolgreicher Verkauf eines IT-Unternehmens im Raum {region or '[Region]'}",
        f"",
        f"Die mibeca GmbH freut sich, einen weiteren erfolgreichen Unternehmensverkauf im deutschen IT-Sektor bekanntzugeben. Das von uns beratene {branche}{f' aus dem Raum {region}' if region else ''} hat einen passenden Käufer gefunden und der Kaufvertrag wurde planmäßig unterzeichnet.",
        f"",
        f"Eckdaten des Unternehmens:",
        f"• Branche: {branche}",
    ]
    if region: lang_lines.append(f"• Standort: {region}")
    if mitarbeiter: lang_lines.append(f"• Mitarbeitende: {mitarbeiter}")
    if umsatz: lang_lines.append(f"• Jahresumsatz: {umsatz}")
    if not anonym and verkaeufer:
        lang_lines.append(f"• Verkäufer: {verkaeufer}")
    lang_lines.extend([
        f"",
        f"Mike Bergmann, Geschäftsführer der mibeca GmbH: „Wir freuen uns sehr, dass wir den Verkäufer auf diesem wichtigen Schritt begleiten durften. Der gefundene Käufer passt sowohl strategisch als auch kulturell hervorragend, sodass die Mitarbeitenden und Kunden auch in Zukunft optimal betreut werden."",
        f"",
        f"Über mibeca GmbH:",
        f"Die mibeca GmbH ist auf M&A-Beratung für IT-Unternehmen im DACH-Raum spezialisiert. Mit langjähriger Branchenerfahrung begleitet das Team von Mike Bergmann Verkäufer und Käufer durch alle Phasen des Transaktionsprozesses – von der Erstbewertung bis zum erfolgreichen Closing.",
        f"",
        f"Kontakt:",
        f"mibeca GmbH",
        f"Mike Bergmann · Geschäftsführer",
        f"E-Mail: mb@mike-bergmann.de",
        f"Web: www.itukv.de",
    ])
    lang = "\n".join(lang_lines)

    # LinkedIn-Entwurf
    linkedin = f"🎉 Erfolg im IT-M&A-Markt!\n\nGerade haben wir einen weiteren erfolgreichen Verkauf eines {branche}s "
    if region: linkedin += f"im Raum {region} "
    linkedin += "abgeschlossen. "
    if mitarbeiter: linkedin += f"Das Unternehmen mit {mitarbeiter} Mitarbeitenden "
    linkedin += "hat einen passenden Nachfolger gefunden – strategisch und kulturell stimmig.\n\nMehr als ein Deal: Eine Lebensentscheidung, die wir respektvoll begleitet haben. 🤝\n\n#MundA #ITUnternehmen #Nachfolge #mibeca"

    return ok({"titel": titel, "kurzText": kurz, "langText": lang, "linkedInText": linkedin})


@app.route(route="pr-mitteilungen/{pid}/send", methods=["POST", "OPTIONS"])
def pr_send(req: func.HttpRequest, pid: str) -> func.HttpResponse:
    """Versendet PR-Mitteilung an Verteiler (Platzhalter – ACS-Integration optional)."""
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    body = req.get_json() or {}
    empfaenger = body.get("empfaenger", [])
    tc = table("prmitteilungen")
    try:
        entity = tc.get_entity("pr", pid)
    except Exception:
        return err("PR-Mitteilung nicht gefunden", 404)
    # TODO: Hier ACS-Integration für echten E-Mail-Versand
    entity["status"] = "versendet"
    entity["versendetAm"] = now()
    entity["empfaengerCount"] = len(empfaenger)
    tc.update_entity(dict(entity))
    return ok({"sent": len(empfaenger), "message": f"PR-Mitteilung an {len(empfaenger)} Empfänger versendet (Platzhalter – ACS-Integration folgt)"})


# ── Verteiler (Distribution List) ─────────────────────────────────────────────

@app.route(route="verteiler", methods=["GET", "POST", "OPTIONS"])
def verteiler(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("verteiler")
    if req.method == "GET":
        items = [dict(i) for i in tc.list_entities()]
        return ok(items)
    body = req.get_json()
    vid = new_id()
    entity = {
        "PartitionKey": "verteiler", "RowKey": vid,
        "email": body.get("email","").lower().strip(),
        "name": body.get("name",""),
        "firma": body.get("firma",""),
        "kategorie": body.get("kategorie","Allgemein"),  # Presse / Investoren / Newsletter / Allgemein
        "createdAt": now(),
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


@app.route(route="verteiler/{vid}", methods=["PATCH", "DELETE", "OPTIONS"])
def verteiler_detail(req: func.HttpRequest, vid: str) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    tc = table("verteiler")
    try:
        entity = tc.get_entity("verteiler", vid)
    except Exception:
        return err("Eintrag nicht gefunden", 404)
    if req.method == "DELETE":
        tc.delete_entity("verteiler", vid)
        return ok({"deleted": True})
    body = req.get_json()
    for k, v in body.items():
        if k not in ("PartitionKey","RowKey"):
            entity[k] = v
    tc.update_entity(dict(entity))
    return ok(dict(entity))


# ── Einstellungen / Webhook-Info ──────────────────────────────────────────────

@app.route(route="settings/webhook", methods=["GET", "OPTIONS"])
def settings_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Liefert Webhook-URL und Token für die Admin-UI."""
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    return ok({
        "url": "https://itukv-func.azurewebsites.net/api/webhook/kunde",
        "token": WEBHOOK_SECRET,
        "headerName": "X-Webhook-Token",
    })


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.route(route="stats", methods=["GET", "OPTIONS"])
def stats(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
    p, e = auth(req, roles=["admin"])
    if e: return e
    try:
        targets_count = sum(1 for _ in table("targets").list_entities())
        kontakte_count = sum(1 for _ in table("kontakte").list_entities())
        nda_count = sum(1 for i in table("interessenten").list_entities()
                        if i.get("ndaStatus") == "gesendet")
        deals_count = sum(1 for i in table("targets").list_entities()
                          if i.get("status") == "verkauft")
        return ok({
            "aktiveTargets": targets_count,
            "offeneNdas": nda_count,
            "investorenGesamt": kontakte_count,
            "dealsAbgeschlossen": deals_count,
        })
    except Exception as ex:
        logging.error(str(ex))
        return ok({"aktiveTargets": 0, "offeneNdas": 0, "investorenGesamt": 0, "dealsAbgeschlossen": 0})
