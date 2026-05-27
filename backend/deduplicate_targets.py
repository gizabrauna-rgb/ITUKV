"""
Dedupliziert die Targets-Tabelle nach mb-Nr.
Pro mb-Nr wird der Eintrag mit dem hoechsten Score behalten,
die anderen werden geloescht.
"""
import os
import sys
import json
from datetime import datetime
from azure.data.tables import TableServiceClient

CONN = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING")
if not CONN:
    sys.exit("AZURE_TABLE_STORAGE_CONNECTION_STRING fehlt.")

DRY_RUN = "--dry" in sys.argv
svc = TableServiceClient.from_connection_string(CONN)
tc = svc.get_table_client("targets")

print(f"Lade Targets… (DRY_RUN={DRY_RUN})")
all_t = [dict(t) for t in tc.list_entities()]
print(f"  {len(all_t)} Targets geladen")


def score(t):
    """Hoeher = wertvoller. Wir wollen den Record mit den meisten gepflegten Daten behalten."""
    s = 0
    # Wichtigste Indikatoren fuer „User hat hier gearbeitet":
    try:
        phasen = json.loads(t.get("phasenJson", "[]") or "[]")
        # Aufgaben mit done=True zaehlen
        for ph in phasen:
            for a in ph.get("aufgaben", []) or []:
                if a.get("done"): s += 50
                if a.get("notiz"): s += 5
            if ph.get("notiz"): s += 10
    except Exception:
        pass
    try:
        if json.loads(t.get("kommunikationJson", "[]") or "[]"): s += 30
    except Exception: pass
    try:
        if json.loads(t.get("termineJson", "[]") or "[]"): s += 30
    except Exception: pass
    try:
        if json.loads(t.get("vertragJson", "{}") or "{}"): s += 20
    except Exception: pass
    try:
        if json.loads(t.get("loiJson", "{}") or "{}"): s += 20
    except Exception: pass
    try:
        if json.loads(t.get("exposeJson", "{}") or "{}"): s += 15
    except Exception: pass
    try:
        if json.loads(t.get("landingJson", "{}") or "{}"): s += 10
    except Exception: pass
    if t.get("mandatStart"): s += 10
    if t.get("fragebogenStatus"): s += 5
    if t.get("wiedervorlage"): s += 5
    if t.get("umsatz"): s += 2
    if t.get("beschreibung"): s += 1
    # Tiebreaker: aelterer = stabiler (User hatte mehr Zeit damit)
    try:
        ts = t.get("createdAt", "") or ""
        if ts:
            d = datetime.fromisoformat(ts[:19])
            # je aelter desto besser (umgekehrt), nur als minimaler Tiebreaker
            s += max(0, 100 - (datetime.utcnow() - d).days)
    except Exception:
        pass
    return s


# Gruppiere nach mbNr
groups = {}
for t in all_t:
    mb = (t.get("mbNr") or "").strip().lower()
    if not mb:
        mb = f"orphan::{t['RowKey']}"
    groups.setdefault(mb, []).append(t)

to_delete = []
keepers_summary = []
groups_with_dups = 0
for mb, members in groups.items():
    if len(members) == 1:
        keepers_summary.append((mb, members[0].get('verkaueferName'), 0, score(members[0])))
        continue
    groups_with_dups += 1
    members.sort(key=score, reverse=True)
    keeper = members[0]
    keepers_summary.append((mb, keeper.get('verkaueferName'), len(members) - 1, score(keeper)))
    for m in members[1:]:
        to_delete.append(m)

print(f"\nmb-Gruppen: {len(groups)}")
print(f"  mit Duplikaten: {groups_with_dups}")
print(f"  zu loeschen:    {len(to_delete)}")
print(f"  zu behalten:    {len(groups)}")
print()
print("Behalten-Übersicht (mbNr | Name | gelöscht | score):")
for mb, name, deletes, sc in sorted(keepers_summary, key=lambda x: x[0]):
    print(f"  {mb:8s} | {(name or '-'):30s} | -{deletes:2d} | score={sc}")

if DRY_RUN:
    print("\n--- DRY RUN, keine Loeschung ---")
    sys.exit(0)

print("\nLoesche Duplikate…")
deleted = 0
for d in to_delete:
    try:
        tc.delete_entity("target", d["RowKey"])
        deleted += 1
    except Exception as ex:
        print(f"  ERROR {d.get('mbNr')}: {ex}")
print(f"\n✓ Fertig: {deleted} geloescht, {len(groups)} Targets behalten.")
