"""
Dedupliziert die Kontakte-Tabelle:
- Gruppiert Kontakte nach Firma (case-insensitive)
- Behaelt pro Gruppe den Eintrag mit dem hoechsten Score
- Score: Kunde > Ex-Kunde > Investor > hat Email > hat GF > hat Branche > hat Notiz > neuer
- Loescht die anderen
- Zusaetzlich: dedupliziert auch nach Email allein (Kontakte ohne Firma)
"""
import os
import sys
import json
from datetime import datetime
from azure.data.tables import TableServiceClient, UpdateMode

CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING")
if not CONN:
    sys.exit("AZURE_TABLE_STORAGE_CONNECTION_STRING fehlt.")

DRY_RUN = "--dry" in sys.argv

svc = TableServiceClient.from_connection_string(CONN)
tc = svc.get_table_client("kontakte")

print(f"Lade Kontakte… (DRY_RUN={DRY_RUN})")
all_k = [dict(k) for k in tc.list_entities()]
print(f"  {len(all_k)} Kontakte geladen")


def score(k):
    s = 0
    ks = (k.get("kundenstatus") or "").lower().strip()
    if ks == "kunde":
        s += 1000
    elif "ex-kunde" in ks:
        s += 800
    elif "investor" in ks:
        s += 600
    elif "partner" in ks:
        s += 500
    elif "potenz" in ks:
        s += 300
    elif ks == "nichtkunde" or not ks:
        s += 100
    if k.get("email"):
        s += 50
    if k.get("geschaeftsfuehrer"):
        s += 20
    if k.get("branche"):
        s += 10
    if k.get("telefon"):
        s += 10
    if k.get("kommentar"):
        s += 5
    if k.get("website"):
        s += 5
    # Updated-At als Tiebreaker
    try:
        ts = k.get("updatedAt") or k.get("createdAt") or ""
        if ts:
            d = datetime.fromisoformat(ts[:19])
            s += int(d.timestamp() / 86400)  # Tage seit 1970, als Tiebreaker
    except Exception:
        pass
    return s


# Gruppiere nach Firma (lower), Fallback: Email
groups = {}
for k in all_k:
    firma = (k.get("firma") or "").strip().lower()
    email = (k.get("email") or "").strip().lower()
    key = f"firma::{firma}" if firma else (f"email::{email}" if email else f"orphan::{k['RowKey']}")
    groups.setdefault(key, []).append(k)

# Per Gruppe entscheiden
to_delete = []
to_keep = 0
groups_with_dups = 0
to_merge = []  # [(keeper_rowkey, [list_of_ansprechpartner_dicts_to_add])]
for key, members in groups.items():
    if len(members) == 1:
        to_keep += 1
        continue
    groups_with_dups += 1
    # Sortiere nach Score absteigend
    members.sort(key=score, reverse=True)
    keeper = members[0]
    to_keep += 1
    # Ansprechpartner aus Duplikaten in keeper uebernehmen, dann loeschen
    extra_ansprechpartner = []
    try:
        existing_aps = json.loads(keeper.get("ansprechpartnerJson", "[]") or "[]")
    except Exception:
        existing_aps = []
    existing_emails = {(ap.get("email") or "").lower() for ap in existing_aps}
    existing_emails.add((keeper.get("email") or "").lower())
    for m in members[1:]:
        m_email = (m.get("email") or "").lower()
        if m_email and m_email not in existing_emails:
            existing_emails.add(m_email)
            extra_ansprechpartner.append({
                "name": m.get("name", "") or m.get("geschaeftsfuehrer", ""),
                "position": "",
                "email": m.get("email", ""),
                "telefon": m.get("telefon", ""),
            })
        to_delete.append(m)
    if extra_ansprechpartner:
        merged_aps = existing_aps + extra_ansprechpartner
        to_merge.append((keeper["RowKey"], merged_aps))

print(f"\nGruppen gesamt: {len(groups)}")
print(f"  ohne Duplikate (1 Eintrag): {len(groups) - groups_with_dups}")
print(f"  mit Duplikaten:             {groups_with_dups}")
print(f"\nZu behaltende Kontakte:      {to_keep}")
print(f"Zu loeschende Duplikate:     {len(to_delete)}")

if DRY_RUN:
    print("\n--- DRY RUN, keine Loeschung ---")
    print("Beispiel-Duplikate die geloescht wuerden:")
    for d in to_delete[:5]:
        print(f"  {d.get('firma')!r} - {d.get('email')!r} - status={d.get('kundenstatus')!r}")
    sys.exit(0)

print(f"\nMerge: {len(to_merge)} Keeper bekommen weitere Ansprechpartner")
print("\nUebertrage Ansprechpartner…")
merged = 0
for keeper_rk, aps in to_merge:
    try:
        ent = tc.get_entity("kontakt", keeper_rk)
        ent["ansprechpartnerJson"] = json.dumps(aps, ensure_ascii=False)
        tc.update_entity(dict(ent), mode=UpdateMode.MERGE)
        merged += 1
    except Exception as ex:
        print(f"  ERROR merge {keeper_rk}: {ex}")
print(f"  {merged} Keeper aktualisiert")

print("\nLoesche Duplikate…")
deleted = 0
errors = 0
for d in to_delete:
    try:
        tc.delete_entity("kontakt", d["RowKey"])
        deleted += 1
        if deleted % 200 == 0:
            print(f"  … {deleted} geloescht")
    except Exception as ex:
        errors += 1
        print(f"  ERROR {d.get('firma')}: {ex}")

print(f"\n✓ Fertig: {deleted} geloescht, {errors} Fehler, {to_keep} behalten, {merged} mit Zusatz-Ansprechpartnern.")
