"""
Importiert einen Element/Matrix-Raum-Export (JSON) in den Verlauf einer Mandate-Akte.

Aufruf:
  export AZURE_TABLE_STORAGE_CONNECTION_STRING="..."
  python import_element.py <pfad-zur-element-export.json> <target-id>

Optional:
  --dry-run         Nur anzeigen, NICHTS speichern
  --mibeca-user @user:matrix.org   Welcher Sender = mibeca-Berater?
                                    Diese Nachrichten werden als 'mail_out' getaggt,
                                    alle anderen als 'mail_in'.
  --target-mbnr mb-219   Statt targetId die mb-Nummer verwenden (sucht das Target)

Was es macht:
- Liest die JSON-Datei
- Extrahiert alle Text-Nachrichten (m.room.message, msgtype=m.text)
- Mapped jede Nachricht auf einen Verlauf-Eintrag:
    typ = 'mail_in' oder 'mail_out' je nach Sender
    datum = aus origin_server_ts (millisekunden)
    autor = sender_name oder sender-ID
    betreff = '(Element-Import)' wenn leer
    beschreibung = Nachrichten-Text
    importedFromElement = True (Marker)
- Haengt sortiert an kommunikationJson des Targets an
- Doppel-Schutz: Eintraege mit identischer event_id werden nicht erneut importiert
"""
import os
import sys
import json
import argparse
from datetime import datetime
from azure.data.tables import TableServiceClient


def parse_args():
    p = argparse.ArgumentParser(description="Element-JSON in ITUKV-Verlauf importieren")
    p.add_argument("json_file", help="Pfad zur Element-Export-JSON-Datei")
    p.add_argument("target_id", nargs="?", help="RowKey des Targets")
    p.add_argument("--target-mbnr", help="mb-Nummer statt RowKey (Target wird gesucht)")
    p.add_argument("--mibeca-user", help="Matrix-User-ID des mibeca-Beraters (z.B. @jenny:matrix.org)")
    p.add_argument("--dry-run", action="store_true", help="Nichts speichern, nur Vorschau")
    return p.parse_args()


def get_table_service():
    conn = os.environ.get("AZURE_TABLE_STORAGE_CONNECTION_STRING")
    if not conn:
        raise SystemExit("FEHLER: Umgebungsvariable AZURE_TABLE_STORAGE_CONNECTION_STRING ist nicht gesetzt.")
    return TableServiceClient.from_connection_string(conn)


def find_target(svc, target_id=None, target_mbnr=None):
    tc = svc.get_table_client("targets")
    if target_id:
        try:
            return dict(tc.get_entity("target", target_id))
        except Exception as ex:
            raise SystemExit(f"FEHLER: Target mit RowKey '{target_id}' nicht gefunden: {ex}")
    if target_mbnr:
        for t in tc.list_entities():
            if (t.get("mbNr") or "").lower() == target_mbnr.lower():
                return dict(t)
        raise SystemExit(f"FEHLER: Target mit mbNr '{target_mbnr}' nicht gefunden.")
    raise SystemExit("FEHLER: Entweder target_id oder --target-mbnr angeben.")


def load_element_json(path):
    if not os.path.exists(path):
        raise SystemExit(f"FEHLER: Datei nicht gefunden: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_messages(export, mibeca_user=None):
    """Element-Export kann verschiedene Formate haben - tolerante Erkennung."""
    msgs = []
    # Verschiedene moegliche Layouts:
    # 1. { "messages": [ {...}, ... ] }
    # 2. Liste von Events direkt
    # 3. { "chunk": [ ... ] }
    candidates = []
    if isinstance(export, list):
        candidates = export
    elif isinstance(export, dict):
        for key in ("messages", "chunk", "events", "items"):
            if isinstance(export.get(key), list):
                candidates = export[key]
                break

    for ev in candidates:
        if not isinstance(ev, dict):
            continue
        ev_type = ev.get("type", "")
        if ev_type and ev_type != "m.room.message":
            continue
        content = ev.get("content") or {}
        body = content.get("body") or content.get("formatted_body") or ""
        if not body:
            continue
        msgtype = content.get("msgtype", "m.text")
        # Nicht-Text-Nachrichten ueberspringen (Bilder, Dateien)
        if msgtype not in ("m.text", "m.notice", "m.emote", ""):
            continue
        sender_id = ev.get("sender", "")
        sender_name = ev.get("sender_name") or ev.get("display_name") or sender_id
        ts_ms = ev.get("origin_server_ts") or ev.get("timestamp") or 0
        try:
            datum_iso = datetime.utcfromtimestamp(ts_ms / 1000).isoformat() if ts_ms else ""
        except Exception:
            datum_iso = ""
        event_id = ev.get("event_id") or ev.get("id") or ""
        ist_mibeca = (mibeca_user and sender_id == mibeca_user)
        msgs.append({
            "event_id": event_id,
            "datum": datum_iso,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "body": body[:5000],  # Cap an Laenge
            "typ": "chat_out" if ist_mibeca else "chat_in",
        })
    return msgs


def append_to_verlauf(target_ent, msgs, svc):
    try:
        verlauf = json.loads(target_ent.get("kommunikationJson") or "[]")
        if not isinstance(verlauf, list):
            verlauf = []
    except Exception:
        verlauf = []
    # Existierende event_ids ermitteln
    existing_event_ids = {e.get("elementEventId") for e in verlauf if isinstance(e, dict)}
    neu = 0
    for m in msgs:
        if m["event_id"] and m["event_id"] in existing_event_ids:
            continue
        verlauf.append({
            "id": "el" + (m["event_id"][-12:] if m["event_id"] else str(int(datetime.utcnow().timestamp() * 1000))),
            "typ": m["typ"],
            "datum": m["datum"],
            "autor": m["sender_name"],
            "betreff": "(Element-Import)",
            "beschreibung": m["body"],
            "elementEventId": m["event_id"],
            "elementSender": m["sender_id"],
            "importedFromElement": True,
        })
        neu += 1
    # Sortieren chronologisch
    verlauf.sort(key=lambda e: e.get("datum", "") or "")
    target_ent["kommunikationJson"] = json.dumps(verlauf, ensure_ascii=False)
    svc.get_table_client("targets").update_entity(target_ent)
    return neu


def main():
    args = parse_args()
    svc = get_table_service()
    target = find_target(svc, args.target_id, args.target_mbnr)
    print(f"Target gefunden: {target.get('mbNr', '?')} - {target.get('firma') or target.get('verkaueferName', '')}")
    export = load_element_json(args.json_file)
    msgs = extract_messages(export, mibeca_user=args.mibeca_user)
    print(f"Gefundene Text-Nachrichten: {len(msgs)}")
    if not msgs:
        print("Nichts zu importieren.")
        return
    # Vorschau
    print("\n--- Vorschau erste 5 Nachrichten ---")
    for m in msgs[:5]:
        print(f"  [{m['datum']}] {m['sender_name']} ({m['typ']}): {m['body'][:80]}{'…' if len(m['body']) > 80 else ''}")
    if args.dry_run:
        print(f"\n[DRY-RUN] Es wuerden {len(msgs)} Nachrichten angehaengt. Kein Schreibzugriff.")
        return
    answer = input(f"\n{len(msgs)} Nachrichten in Verlauf des Targets schreiben? [y/N] ").strip().lower()
    if answer != "y":
        print("Abgebrochen.")
        return
    neu = append_to_verlauf(target, msgs, svc)
    print(f"\n✅ Fertig: {neu} neue Eintraege im Verlauf (Doubletten via event_id uebersprungen).")


if __name__ == "__main__":
    main()
