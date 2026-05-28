# Anleitung: Anthropic API-Key rotieren

**Ziel:** Den aktuellen Anthropic-API-Key sicher gegen einen neuen austauschen,
ohne dass die KI-Funktion ausfällt.
**Aufwand:** ca. 10 Minuten.
**Notwendig:** Zugriff auf Anthropic Console + Azure Portal (oder Azure CLI).

---

## Wann rotieren?

- **Sofort:** wenn der Key versehentlich in einer Mail, einem Screenshot, einem Chat
  oder Logfile sichtbar wurde
- Mindestens **alle 6 Monate** als Hygiene-Maßnahme
- Bei Wechsel des verantwortlichen Mitarbeiters
- Wenn der Anthropic-Account Mitglieder verliert oder bekommt

---

## Schritt 1: Neuen Key in Anthropic anlegen

1. Browser → https://console.anthropic.com
2. Login (Owner / Admin der Organisation)
3. Menü links → **„API Keys"**
4. Klick auf **„Create Key"**
5. Name vergeben, sinnvoll: `itukv-prod-2026-05-28` (Datum hilft beim Tracking)
6. Workspace = Production wählen, falls Workspace-Trennung
7. **„Create"** klicken
8. **Wichtig:** Den Key sofort kopieren – Anthropic zeigt ihn nur einmal an.

---

## Schritt 2: Neuen Key in Azure setzen

### Variante A: Azure Portal (klickend)

1. https://portal.azure.com öffnen
2. Suchen nach `itukv-func-v2` (Azure Function App)
3. Links → **„Configuration"** → **„Application Settings"**
4. Eintrag `ANTHROPIC_API_KEY` suchen → **„Edit"**
5. Den neuen Key einfügen (Wert ersetzen)
6. **„OK"** → oben **„Save"** klicken
7. Azure startet die Function App automatisch neu (~30 Sek)

### Variante B: Azure CLI (schneller, terminal-basiert)

```bash
az functionapp config appsettings set \
  --name itukv-func-v2 \
  --resource-group itukv \
  --settings "ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXX..."
```

Die Function App wird automatisch neu gestartet.

---

## Schritt 3: Funktion testen

1. Im ITUKV Dashboard einloggen (Admin)
2. Eine beliebige Akte öffnen
3. Datenraum → eine PDF anklicken → **„KI-Analyse"** auslösen
4. Wenn die Antwort kommt → der neue Key funktioniert ✅
5. Wenn HTTP 401 / „Invalid API Key" → der alte Key ist noch aktiv oder neuer Key
   wurde falsch kopiert. Schritt 2 wiederholen.

---

## Schritt 4: Alten Key sperren

**Erst nach erfolgreichem Test!**

1. Zurück in https://console.anthropic.com → **„API Keys"**
2. Den alten Key (z. B. `itukv-prod-2026-04-...`) finden
3. **„Revoke"** klicken → Bestätigung
4. Der alte Key ist ab sofort tot und kann nicht mehr missbraucht werden.

---

## Schritt 5: Dokumentation

1. Im Anthropic-Account: alter Key bleibt im Audit-Log sichtbar (Datum revoked)
2. In mibeca-Dokumentation:
   - `docs/legal/key-rotations.md` (falls nicht existent: anlegen) ergänzen:
     ```
     2026-05-28 – Rotation durch Anna Giza-Braun
     Grund: initialer Key war in Kontext-Output sichtbar
     Alter Key: …agpies6…ZEHPQAA (revoked)
     Neuer Key: …XXXXXX (aktiv)
     ```
3. Im AI-Security-Konzept (§1a Compliance-Tabelle) den Punkt
   **„API-Key-Rotation"** auf ✅ setzen und Datum eintragen.

---

## Notfall: Key kompromittiert

Wenn ein Key gerade kompromittiert wurde (z. B. öffentlich auf GitHub):

1. **Sofort revoken** (Schritt 4 vorziehen), auch vor Erzeugen des neuen Keys
2. Dann Schritte 1–3 in normaler Reihenfolge
3. Anthropic-Support informieren bei Missbrauchsverdacht (für eventuelle Gutschrift)
4. mibeca-DSB informieren (potenzielles meldepflichtiges Daten-Ereignis)

---

## Was passiert während des Rotation-Fensters?

- Sobald der neue Key in Azure gesetzt ist und die Function neu gestartet hat
  (ca. 30 Sek), läuft die KI mit dem neuen Key.
- Solange der alte Key noch nicht revoked ist, wären theoretisch beide gleichzeitig
  gültig. Anthropic erlaubt das bewusst, damit man **zero-downtime** rotieren kann.
- Daher: erst neuen Key setzen + testen, dann alten Key revoken.

---

*Letzte Prüfung dieser Anleitung: 2026-05-28.*
