"""
Setzt das phasenJson aller Targets zurueck (loescht das Feld), damit beim
naechsten Laden im Frontend die aktuelle Phasen-Vorlage aus phasenTemplates.js
greift.

Achtung: ALLE manuell abgehakten Aufgaben in Phasen gehen verloren!
Daher nur fuer Test-Targets verwenden.

Aufruf:
  export AZURE_TABLE_STORAGE_CONNECTION_STRING="..."
  python reset_phasen.py            # Listet auf, fragt nach Bestaetigung
  python reset_phasen.py --confirm  # Reset ohne Rueckfrage (Skript-Modus)
"""
import os, sys
from azure.data.tables import TableServiceClient

CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING")
if not CONN:
    raise SystemExit("Bitte Umgebungsvariable AZURE_TABLE_STORAGE_CONNECTION_STRING setzen.")

svc = TableServiceClient.from_connection_string(CONN)
tc = svc.get_table_client("targets")

alle = list(tc.list_entities())
mit_phasen = [t for t in alle if t.get("phasenJson")]

print(f"Insgesamt {len(alle)} Targets, davon {len(mit_phasen)} mit gespeichertem phasenJson.\n")
for t in mit_phasen:
    name = t.get("verkaueferName") or t.get("firma") or "(ohne Name)"
    mb = t.get("mbNr") or "(keine mb-Nr)"
    print(f"  - {mb}  {name}  ({t.get('projekttyp', '?')})")

if not mit_phasen:
    print("Nichts zu tun.")
    sys.exit(0)

if "--confirm" not in sys.argv:
    a = input("\nAlle obigen Targets zuruecksetzen (phasenJson leeren)? [y/N] ").strip().lower()
    if a != "y":
        print("Abgebrochen.")
        sys.exit(0)

for t in mit_phasen:
    ent = dict(t)
    ent["phasenJson"] = ""
    tc.update_entity(ent)
    print(f"  ✓ {ent.get('mbNr') or ent['RowKey']}")

print(f"\n✅ Fertig. {len(mit_phasen)} Targets zurueckgesetzt – beim naechsten Frontend-Laden greift die aktuelle Vorlage.")
