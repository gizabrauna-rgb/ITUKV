"""
Einmaliger Import der Kunden-Excel in die ITUKV-Datenbank.
- Zeilen mit mb-Nummer → Targets
- Zeilen mit Kundenstatus = "Kunde" → Kontakte (CRM)
"""
import os
import sys
import uuid
import json
from datetime import datetime
from openpyxl import load_workbook
from azure.data.tables import TableServiceClient

EXCEL_PATH = "/Users/annagiza-braun/Downloads/Kunden und Ex-Kunden.xlsx"
CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING")
if not CONN:
    sys.exit("Umgebungsvariable AZURE_TABLE_STORAGE_CONNECTION_STRING nicht gesetzt.")

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

now = datetime.utcnow().isoformat()
svc = TableServiceClient.from_connection_string(CONN)
svc.create_table_if_not_exists("targets")
svc.create_table_if_not_exists("kontakte")
tc_targets = svc.get_table_client("targets")
tc_kontakte = svc.get_table_client("kontakte")

print("Lade Excel…")
wb = load_workbook(EXCEL_PATH, read_only=True, data_only=True)
ws = wb["Sheet1"]
rows = ws.iter_rows(values_only=True)
header = next(rows)

def idx(name):
    for i, h in enumerate(header):
        if h and name.lower() in str(h).lower():
            return i
    return None

# Spalten-Indizes
COL_VORNAME = idx("Vorname")
COL_NACHNAME = idx("Nachname")
COL_EMAIL = idx("E-Mail-Adresse") if idx("E-Mail-Adresse") is not None else idx("E-Mail")
COL_TELEFON = idx("Telefonnummer") if idx("Telefonnummer") is not None else idx("Telefon")
COL_FIRMA = idx("Firmenname") if idx("Firmenname") is not None else idx("Firma")
COL_WEBSITE = idx("Website")
COL_PLZ = idx("PLZ")
COL_STADT = idx("Stadt")
COL_LAND = idx("Land")
COL_KUNDENSTATUS = idx("Kundenstatus")
COL_KUNDENNR = idx("Kundennummer")
COL_MBNR = idx("ITUKV ProjNr")
COL_NOTIZEN = idx("Notizen Salesliste") if idx("Notizen Salesliste") is not None else idx("Notizen")
COL_BEMERKUNG_ITUKV = idx("Bemerkung ITUKV")
COL_LEAD_HERKUNFT = idx("Leadherkunft")

# UVE-Felder (Verkäufer-Infos)
COL_UVE_WANN = idx("Wann verkaufen")
COL_UVE_PREIS = idx("Preisvorstellung")
COL_UVE_WERT = idx("Wert")
# Investor-Felder
COL_INV_REGION = idx("Region zukaufen") if idx("Region zukaufen") is not None else idx("Region")
COL_INV_MA = idx("MA-Anzahl") if idx("MA-Anzahl") is not None else idx("Mitarbeiter")
COL_INV_TX = idx("Transaktionsgröße") if idx("Transaktionsgröße") is not None else idx("Transaktion")

print(f"Indizes: Vorname={COL_VORNAME}, Email={COL_EMAIL}, Firma={COL_FIRMA}, mbNr={COL_MBNR}")

targets_created = 0
targets_seen_mbnr = set()
kontakte_created = 0
kontakte_seen_email = set()

for row_idx, row in enumerate(rows, start=2):
    if not row:
        continue
    def g(col):
        if col is None or col >= len(row):
            return ""
        v = row[col]
        return str(v).strip() if v is not None else ""

    vorname = g(COL_VORNAME)
    nachname = g(COL_NACHNAME)
    email = g(COL_EMAIL).lower()
    firma = g(COL_FIRMA)
    mbNr_raw = g(COL_MBNR)
    kundenstatus = g(COL_KUNDENSTATUS)
    notizen = g(COL_NOTIZEN)
    bemerkung_itukv = g(COL_BEMERKUNG_ITUKV)

    # Skip leere Zeilen
    if not (email or firma or mbNr_raw):
        continue

    name = f"{vorname} {nachname}".strip()
    plz = g(COL_PLZ)
    ort = g(COL_STADT)
    telefon = g(COL_TELEFON)
    website = g(COL_WEBSITE)
    herkunft = g(COL_LEAD_HERKUNFT)

    # mb-Nummer extrahieren (kann "mb-317" oder nur "317" sein)
    mbNr = ""
    if mbNr_raw:
        import re
        m = re.search(r"mb-?(\d+)", mbNr_raw, re.IGNORECASE)
        if m:
            mbNr = f"mb-{m.group(1)}"
        elif mbNr_raw.isdigit():
            mbNr = f"mb-{mbNr_raw}"

    # === TARGETS ===
    if mbNr and mbNr not in targets_seen_mbnr:
        # Nur anlegen wenn auch sinnvolle Daten vorhanden
        if firma or name:
            targets_seen_mbnr.add(mbNr)
            tid = str(uuid.uuid4())
            entity = {
                "PartitionKey": "target", "RowKey": tid,
                "mbNr": mbNr,
                "verkaueferName": name or firma,
                "firma": firma,
                "email": email,
                "telefon": telefon,
                "website": website,
                "region": ort,
                "plz": plz,
                "branche": "IT-Systemhaus",
                "mitarbeiter": "",
                "umsatz": g(COL_UVE_WERT) or g(COL_UVE_PREIS),
                "beschreibung": (bemerkung_itukv + " " + notizen).strip(),
                "projekttyp": "Projekt Target",
                "status": "verfuegbar",
                "checklisteJson": json.dumps(DEFAULT_CHECKLISTE),
                "createdAt": now,
            }
            try:
                tc_targets.upsert_entity(entity)
                targets_created += 1
                print(f"  TARGET: {mbNr} – {entity['verkaueferName']} ({firma})")
            except Exception as e:
                print(f"  ERROR Target {mbNr}: {e}")

    # === KONTAKTE (CRM) ===
    # Nur Kunden / Ex-Kunden mit echter E-Mail importieren
    if email and email not in kontakte_seen_email and "kunde" in kundenstatus.lower():
        kontakte_seen_email.add(email)
        kid = str(uuid.uuid4())

        # Typ bestimmen
        typ = "Sonstige"
        sucht_text = ""
        bietet_text = ""
        if g(COL_INV_REGION) or g(COL_INV_TX):
            typ = "Strategisch"
            sucht_text = f"{g(COL_INV_REGION)} {g(COL_INV_MA)} {g(COL_INV_TX)}".strip()
        elif g(COL_UVE_WANN) or g(COL_UVE_PREIS):
            typ = "Verkäufer-Interesse"
            bietet_text = f"verkaufen: {g(COL_UVE_WANN)} {g(COL_UVE_PREIS)}".strip()

        entity = {
            "PartitionKey": "kontakt", "RowKey": kid,
            "name": name,
            "firma": firma,
            "email": email,
            "telefon": telefon,
            "website": website,
            "plz": plz,
            "ort": ort,
            "typ": typ,
            "sucht": sucht_text,
            "bietet": bietet_text,
            "kommentar": notizen,
            "herkunft": herkunft or "Excel-Import",
            "kundenstatus": kundenstatus,
            "kundennummer": g(COL_KUNDENNR),
            "createdAt": now,
            "updatedAt": now,
        }
        try:
            tc_kontakte.upsert_entity(entity)
            kontakte_created += 1
        except Exception as e:
            print(f"  ERROR Kontakt {email}: {e}")

print(f"\n✓ Fertig:")
print(f"  Targets angelegt: {targets_created}")
print(f"  Kontakte angelegt: {kontakte_created}")
