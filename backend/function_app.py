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

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

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

DEFAULT_CHECKLISTE = [
    {"id": "1", "label": "Unternehmensbewertung", "done": False},
    {"id": "2", "label": "Fragebogen Unternehmensbewertung", "done": False},
    {"id": "3", "label": "Exposé erstellt", "done": False},
    {"id": "4", "label": "Mandat unterschrieben", "done": False},
    {"id": "5", "label": "Element-Raum eröffnet", "done": False},
    {"id": "6", "label": "Target beworben", "done": False},
    {"id": "7", "label": "Eingehende NDAs geprüft", "done": False},
    {"id": "8", "label": "Alle Dokumente vollständig", "done": False},
]

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
    checkliste = json.dumps(DEFAULT_CHECKLISTE)
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
        "checklisteJson": checkliste,
        "createdAt": now(),
    }
    tc.create_entity(entity)
    return ok(dict(entity), 201)


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

@app.route(route="webhook/crm", methods=["POST", "OPTIONS"])
def webhook_crm(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS": return opt()
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
