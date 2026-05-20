import azure.functions as func
import json
import logging
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# ── Config ──────────────────────────────────────────────────────────────────
TABLE_CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING", "")
BLOB_CONN = os.environ.get("AZURE_BLOB_STORAGE_CONNECTION_STRING", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
FUNC_KEY = os.environ.get("FUNC_KEY", "")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, x-functions-key",
    "Content-Type": "application/json",
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def ok(data, status=200):
    return func.HttpResponse(json.dumps(data, default=str), status_code=status, headers=CORS_HEADERS)

def err(msg, status=400):
    return func.HttpResponse(json.dumps({"error": msg}), status_code=status, headers=CORS_HEADERS)

def options_response():
    return func.HttpResponse("", status_code=204, headers=CORS_HEADERS)

def get_table_client(table_name):
    service = TableServiceClient.from_connection_string(TABLE_CONN)
    service.create_table_if_not_exists(table_name)
    return service.get_table_client(table_name)

def decode_token(req):
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        return jwt.decode(auth[7:], JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None

def require_auth(req, roles=None):
    payload = decode_token(req)
    if not payload:
        return None, err("Nicht autorisiert", 401)
    if roles and payload.get("role") not in roles:
        return None, err("Keine Berechtigung", 403)
    return payload, None

def make_jwt(user_id, role, name, email):
    payload = {
        "id": user_id,
        "role": role,
        "name": name,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.route(route="login", methods=["POST", "OPTIONS"])
def login(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()
    try:
        body = req.get_json()
        email = body.get("email", "").lower().strip()
        password = body.get("password", "")
        tc = get_table_client("users")
        users = list(tc.query_entities(f"email eq '{email}'"))
        if not users:
            return err("E-Mail oder Passwort falsch", 401)
        user = users[0]
        if not bcrypt.checkpw(password.encode(), user["passwordHash"].encode()):
            return err("E-Mail oder Passwort falsch", 401)
        token = make_jwt(user["RowKey"], user["role"], user["name"], email)
        return ok({"token": token, "role": user["role"], "name": user["name"], "id": user["RowKey"]})
    except Exception as e:
        logging.error(str(e))
        return err("Interner Fehler", 500)


# ── Targets ──────────────────────────────────────────────────────────────────

@app.route(route="targets", methods=["GET", "POST", "OPTIONS"])
def targets(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()
    payload, error = require_auth(req, roles=["admin"])
    if error:
        return error
    tc = get_table_client("targets")
    if req.method == "GET":
        items = [dict(e) for e in tc.list_entities()]
        return ok(items)
    if req.method == "POST":
        body = req.get_json()
        import uuid
        row_key = str(uuid.uuid4())
        entity = {
            "PartitionKey": "target",
            "RowKey": row_key,
            "mbNr": body.get("mbNr", ""),
            "verkaueferName": body.get("verkaueferName", ""),
            "region": body.get("region", ""),
            "status": "verfuegbar",
            "projekttyp": body.get("projekttyp", "Projekt Target"),
            "createdAt": datetime.utcnow().isoformat(),
        }
        tc.create_entity(entity)
        return ok(entity, 201)


@app.route(route="targets/{target_id}", methods=["GET", "PATCH", "OPTIONS"])
def target_detail(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()
    payload, error = require_auth(req)
    if error:
        return error
    tc = get_table_client("targets")
    if req.method == "GET":
        try:
            entity = tc.get_entity("target", target_id)
            return ok(dict(entity))
        except Exception:
            return err("Target nicht gefunden", 404)
    if req.method == "PATCH":
        body = req.get_json()
        entity = tc.get_entity("target", target_id)
        for key, val in body.items():
            entity[key] = val
        tc.update_entity(entity)
        return ok(dict(entity))


# ── Kontakte (CRM) ────────────────────────────────────────────────────────────

@app.route(route="kontakte", methods=["GET", "POST", "OPTIONS"])
def kontakte(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()
    payload, error = require_auth(req, roles=["admin"])
    if error:
        return error
    tc = get_table_client("kontakte")
    if req.method == "GET":
        items = [dict(e) for e in tc.list_entities()]
        return ok(items)
    if req.method == "POST":
        body = req.get_json()
        import uuid
        entity = {
            "PartitionKey": "kontakt",
            "RowKey": str(uuid.uuid4()),
            **{k: body[k] for k in body if k not in ("PartitionKey", "RowKey")},
            "createdAt": datetime.utcnow().isoformat(),
        }
        tc.create_entity(entity)
        return ok(entity, 201)


@app.route(route="kontakte/import", methods=["POST", "OPTIONS"])
def kontakte_import(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()
    payload, error = require_auth(req, roles=["admin"])
    if error:
        return error
    # Webhook-Import: empfängt Liste von Kontakten und upserted sie
    try:
        body = req.get_json()
        items = body if isinstance(body, list) else body.get("items", [])
        tc = get_table_client("kontakte")
        import uuid
        count = 0
        for item in items:
            entity = {
                "PartitionKey": "kontakt",
                "RowKey": item.get("id", str(uuid.uuid4())),
                **{k: v for k, v in item.items() if k not in ("PartitionKey", "RowKey")},
                "updatedAt": datetime.utcnow().isoformat(),
            }
            tc.upsert_entity(entity)
            count += 1
        return ok({"imported": count})
    except Exception as e:
        logging.error(str(e))
        return err("Import fehlgeschlagen", 500)


# ── Ausschreibungen ───────────────────────────────────────────────────────────

@app.route(route="ausschreibungen", methods=["GET", "OPTIONS"])
def ausschreibungen(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()
    payload, error = require_auth(req)
    if error:
        return error
    tc = get_table_client("ausschreibungen")
    items = [dict(e) for e in tc.query_entities("status eq 'aktiv'")]
    return ok(items)


# ── NDA ───────────────────────────────────────────────────────────────────────

@app.route(route="nda/send", methods=["POST", "OPTIONS"])
def nda_send(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()
    payload, error = require_auth(req)
    if error:
        return error
    # Zoho Sign Integration – Platzhalter, wird in Phase 4 implementiert
    return ok({"message": "NDA-Versand via Zoho Sign – kommt in Phase 4"})


# ── Dokumente ─────────────────────────────────────────────────────────────────

@app.route(route="targets/{target_id}/dokumente", methods=["GET", "OPTIONS"])
def dokumente(req: func.HttpRequest, target_id: str) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()
    payload, error = require_auth(req)
    if error:
        return error
    tc = get_table_client("dokumente")
    items = [dict(e) for e in tc.query_entities(f"targetId eq '{target_id}'")]
    return ok(items)
