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


def auth_user(req):
    a = req.headers.get("Authorization", "")
    if not a.startswith("Bearer "):
        return None
    try:
        h, p, s = a[7:].split('.')
        expected = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64ud(s), expected):
            return None
        return json.loads(_b64ud(p))
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
    return ok_({"id": uid, "email": email, "role": entity["role"], "name": entity["name"], "initialPassword": pw}, 201)


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
    return ok_({"email": entity.get("email"), "newPassword": pw})


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
    for k in kontakte_items:
        plz = str(k.get("plz","")).strip()
        c = coords.get(plz)
        if c:
            kontakte_out.append({
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
            })
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
