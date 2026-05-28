"""
Prueft alle Investoren/Kauf-Mandat-Targets auf fehlende mbNr.
Aufruf:  python check_mbnr_investoren.py
"""
import os
from azure.data.tables import TableServiceClient

CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING")
if not CONN:
    raise SystemExit("Bitte Umgebungsvariable AZURE_TABLE_STORAGE_CONNECTION_STRING setzen.")

INVEST_TYPS = {"Projekt Investoren", "MC Investoren", "Kauf-Mandat"}

svc = TableServiceClient.from_connection_string(CONN)
tc = svc.get_table_client("targets")

alle = list(tc.list_entities())
investoren = [t for t in alle if (t.get("projekttyp") or "") in INVEST_TYPS]

print(f"Insgesamt {len(alle)} Targets, davon {len(investoren)} Investoren/Kauf-Mandate.\n")

fehlt = []
vorhanden = []
for t in investoren:
    mb = (t.get("mbNr") or "").strip()
    if not mb:
        fehlt.append(t)
    else:
        vorhanden.append(t)

print(f"Mit mbNr:   {len(vorhanden)}")
print(f"Ohne mbNr:  {len(fehlt)}\n")

if fehlt:
    print("--- Investoren OHNE mbNr ---")
    for t in fehlt:
        name = t.get("verkaueferName") or t.get("firma") or "(ohne Name)"
        print(f"  RowKey={t['RowKey']}  Projekttyp={t.get('projekttyp')}  Name={name}")
else:
    print("Alle Investoren haben eine mbNr. ✅")
