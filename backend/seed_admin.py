"""
Einmaliges Skript zum Anlegen des Admin-Users.
Aufruf: python seed_admin.py
"""
import os
import uuid
import bcrypt
from datetime import datetime
from azure.data.tables import TableServiceClient

CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING")
if not CONN:
    raise ValueError("Bitte Umgebungsvariable AZURE_TABLE_STORAGE_CONNECTION_STRING setzen.")

EMAIL = "ab@mike-bergmann.de"
NAME = "Anna Giza-Braun"
PASSWORD = input("Passwort für ab@mike-bergmann.de eingeben: ")

svc = TableServiceClient.from_connection_string(CONN)
svc.create_table_if_not_exists("users")
tc = svc.get_table_client("users")

existing = list(tc.query_entities(f"email eq '{EMAIL}'"))
if existing:
    print(f"User {EMAIL} existiert bereits. Passwort wird aktualisiert.")
    entity = existing[0]
    entity["passwordHash"] = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    tc.update_entity(entity)
else:
    pw_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    entity = {
        "PartitionKey": "user",
        "RowKey": str(uuid.uuid4()),
        "email": EMAIL,
        "passwordHash": pw_hash,
        "role": "admin",
        "name": NAME,
        "targetId": "",
        "customerId": "",
        "createdAt": datetime.utcnow().isoformat(),
    }
    tc.create_entity(entity)
    print(f"Admin-User {EMAIL} erfolgreich angelegt.")
