# Element → Dashboard: Anleitung für eine KI (autonomer Import)

**Adressat:** Eine KI/Agent, die für Jenny den Element-Chat-Verlauf
automatisch ins ITUKV-Dashboard übertragen soll.

Diese Datei kannst du der KI als Kontext mitgeben (z. B. via System-Prompt,
Wissensbasis oder MCP-Resource). Sie enthält alles, was die KI für den
Ende-zu-Ende-Ablauf braucht.

---

## 1. Überblick

Das mibeca-Team kommuniziert mit Käufern und Verkäufern in Element/Matrix-Räumen
(E2E-verschlüsselt). Für die mibeca-Akte im **ITUKV-Dashboard** sollen diese
Verläufe importiert werden, damit alles zentral nachvollziehbar ist.

Heute macht das ein Mensch manuell:
1. In Element den Raum öffnen → „Export Chat" → JSON exportieren
2. Im Dashboard auf die Akte → Verlauf → „Element-Verlauf importieren" → JSON hochladen

**Ziel der Automatisierung:** Die KI soll diesen Schritt selbständig übernehmen,
sobald Jenny einen neuen Raum als „importwürdig" markiert oder regelmäßig
(z. B. einmal pro Stunde).

---

## 2. Was die KI braucht (Setup, einmalig)

### 2.1 Zugang zu Element/Matrix

- **Homeserver**: `https://matrix.mb-ak.de` (das ist der mibeca-Element-Server)
- **Bot-Account** mit eigener User-ID, z. B. `@dashboard-bot:matrix.mb-ak.de`
  - Mike oder ein Admin muss diesen Bot-Account anlegen
  - Bot muss in **alle relevanten Räume eingeladen** werden
  - Empfehlung: dedizierter Bot statt Jennys persönlicher Account (Audit/Trennung)
- **Access Token** für den Bot
  - Bekommt man via Login: `POST /_matrix/client/v3/login` mit `type=m.login.password`
  - Oder über das Element-Web-Interface: Einstellungen → Hilfe & Informationen →
    Erweitert → „Access Token"
- **Verschlüsselungs-Setup**: weil alle Räume E2E sind, braucht die KI **Megolm-Keys**.
  - **Einfachste Lösung: [Pantalaimon](https://github.com/matrix-org/pantalaimon)**
    als lokaler Proxy. Pantalaimon sitzt zwischen KI und Matrix, übernimmt
    die Verschlüsselung transparent. Die KI spricht dann unverschlüsselt mit
    Pantalaimon, Pantalaimon mit Matrix.
  - **Alternative**: matrix-nio (Python-Library) mit eigener Key-Verwaltung —
    aufwendiger, aber kein Proxy nötig.

### 2.2 Zugang zum Dashboard

- **Dashboard-Backend**: `https://itukv-func-v2.azurewebsites.net/api/`
  - Custom-Domain: `https://dashboard.itukv.de` (Frontend), Backend wie oben
- **Authentifizierung**: JWT-Token via Login
  - Endpoint: `POST /api/login` mit `{ email, password }`
  - Antwort enthält `token`, der als `Authorization: Bearer <token>` mitgesendet werden muss
  - Empfehlung: Dedizierter **API-User** mit Rolle `admin` für die KI (Mike oder Anna kann den anlegen)
  - Plus **Functions-Key**-Header: `x-functions-key: <key>` (aus den Azure App Settings, ENV `MIBECA_API_KEY`)
- **Element-Import-Endpoint**: `POST /api/element-import`

  Body:
  ```json
  {
    "targetId": "619fc88c-2d22-4477-941c-a961880a22d2",
    "fileData": "<base64-kodierte JSON-Datei mit dem Raum-Export>",
    "mibecaSenderId": "@jennifer.kaplan:matrix.mb-ak.de",
    "dryRun": false
  }
  ```

  Antwort:
  ```json
  { "imported": 42, "skipped": 3 }
  ```

  - `imported` = Anzahl neuer Verlauf-Einträge
  - `skipped` = Doubletten (anhand `event_id` erkannt)
  - Mit `dryRun: true` werden Nachrichten nur geparst, nicht gespeichert (Test-Modus)

- **Body-Limit**: 25 MB. Bei größeren Räumen vorher splitten.

---

## 3. Format-Spezifikation: Element-Export-JSON

Element exportiert pro Raum eine JSON-Datei in einem von zwei Formaten:

### Variante A — direkte Liste
```json
[
  {
    "type": "m.room.message",
    "sender": "@jennifer.kaplan:matrix.mb-ak.de",
    "origin_server_ts": 1735862400000,
    "event_id": "$abcdef...",
    "content": {
      "msgtype": "m.text",
      "body": "Hallo, hier kommt die NDA …"
    }
  },
  ...
]
```

### Variante B — eingewickelt
```json
{
  "messages": [ ... ],
  "events": [ ... ],   // alternativ
  "chunk": [ ... ]     // alternativ (kommt aus /messages-API)
}
```

Das Backend akzeptiert beide Varianten und sucht die Liste unter den Keys
`messages`, `events`, `chunk`, `items` oder nimmt sie direkt, wenn der Body
schon ein Array ist.

### Erwartete Felder pro Nachricht
- `type` = `"m.room.message"` (alles andere wird ignoriert)
- `content.body` (oder `content.formatted_body`) = Nachrichten-Text
- `content.msgtype` ∈ `m.text`, `m.notice`, `m.emote` (sonst übersprungen)
- `sender` = Matrix-User-ID des Absenders
- `origin_server_ts` oder `timestamp` = Unix-Timestamp in **Millisekunden**
- `event_id` = Eindeutige ID (für Dedup)

### mibeca-Identifikation
Das Backend kennt diese Matrix-IDs als „mibeca":
```
@jennifer.kaplan:matrix.mb-ak.de
@m.bergmann:matrix.mb-ak.de
@mb:matrix.mb-ak.de
@cb:matrix.mb-ak.de
@wielad.micheel:matrix.mb-ak.de
@michaela.boyer:matrix.mb-ak.de
@so:matrix.mb-ak.de
@kw:matrix.mb-ak.de
```
Diese Nachrichten werden als `chat_out` (mibeca → Kunde) markiert.
Alle anderen sind `chat_in` (Kunde → mibeca).

Das Feld `mibecaSenderId` im Request darf zusätzlich gesetzt werden, falls für
einen speziellen Raum eine andere mibeca-ID gilt.

---

## 4. Ablauf der KI (Pseudocode)

```python
# 1. Login bei Dashboard
resp = http.post(
  "https://itukv-func-v2.azurewebsites.net/api/login",
  json={"email": "ki-bot@mibeca-intern.de", "password": "<aus Vault>"},
  headers={"x-functions-key": "<aus Vault>"},
)
jwt = resp.json()["token"]

# 2. Welche Räume gibt es? → Matrix-Client API über Pantalaimon
rooms = http.get("http://localhost:8009/_matrix/client/v3/joined_rooms",
                 headers={"Authorization": f"Bearer {matrix_access_token}"}).json()["joined_rooms"]

# 3. Für jeden Raum: Mapping Raum → targetId (mb-Nr)
#    Mapping pflegt Jenny, z. B. in einer kleinen Tabelle/Notion/JSON:
#    { "!roomA:matrix.mb-ak.de": "619fc88c-..." (= mb-000), ... }

# 4. Pro Raum: Messages-Endpoint abfragen
messages = []
token = None
while True:
    params = {"dir": "b", "limit": 500}
    if token: params["from"] = token
    r = http.get(
        f"http://localhost:8009/_matrix/client/v3/rooms/{room_id}/messages",
        params=params,
        headers={"Authorization": f"Bearer {matrix_access_token}"}
    ).json()
    messages.extend(r["chunk"])
    if not r.get("end") or r["end"] == token: break
    token = r["end"]

# 5. Sortieren nach origin_server_ts aufsteigend, dann als JSON-Datei
export = {"messages": sorted(messages, key=lambda e: e.get("origin_server_ts", 0))}

# 6. An Dashboard senden
import base64, json as _json
file_b64 = base64.b64encode(_json.dumps(export).encode()).decode()
http.post(
  "https://itukv-func-v2.azurewebsites.net/api/element-import",
  json={"targetId": target_id, "fileData": file_b64},
  headers={
    "Authorization": f"Bearer {jwt}",
    "x-functions-key": "<aus Vault>",
  },
)
```

Das Backend ist **idempotent** — wiederholtes Senden derselben Nachrichten
erzeugt keine Duplikate (Dedup via `event_id`).

---

## 5. Empfohlener Trigger

- **Manuell**: Jenny markiert in einer kleinen Steuer-Liste (z. B. Excel/Notion/Airtable)
  pro Raum die `targetId`. KI liest die Liste, importiert, schreibt „letzter Import"
  zurück.
- **Cron** (z. B. stündlich): KI prüft alle gemappten Räume auf neue Nachrichten
  seit dem letzten Import und überträgt nur das Delta.

---

## 6. Sicherheits-Hinweise

- **Access Token niemals committen** — nur in einem Secrets-Manager (Azure Key Vault,
  GitHub Secrets, 1Password etc.)
- Bot-Account hat Zugriff auf E2E-Räume — Compromise wäre kritisch. Token regelmäßig rotieren.
- Pantalaimon-Daten (`~/.local/share/pantalaimon`) enthalten Megolm-Schlüssel — wie ein Server-Key behandeln.
- Dashboard-Request wird nur akzeptiert, wenn der JWT zu einem Admin-User gehört.

---

## 7. Wer hilft bei Problemen

- **Element/Matrix-Konto**: Mike Bergmann
- **Dashboard-API + Endpoints**: Anna Giza-Braun (`ab@mike-bergmann.de`)
- **Architektur-Fragen**: dieses Doc + die Implementierung in
  `backend/function_app.py` → `def element_import`
