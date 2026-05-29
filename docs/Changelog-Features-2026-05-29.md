# Was ist neu im ITUKV Dashboard – Stand 2026-05-29

**Zielgruppe:** Jenny, Anna, Geschäftsführung, DSB
**Zweck:** Übersicht aller Verbesserungen vom 29.05.2026 (Phase-2-Block).

Vorgängerversion siehe `Changelog-Features-2026-05-28.md`.

---

## Für mibeca-Berater (Anna, Jenny)

### ✅ KI „Mit Assistent anreichern" in der Kundenakte
**Was:** Lila Button im Akten-Header. Klick → Assistent recherchiert aus dem Wissen über die Firma Stammdaten-Vorschläge (Geschäftsführer, Branche, PLZ/Ort, Mitarbeiter, Umsatz, Website).
**Modal:** Konfidenz-Badge (hoch/mittel/niedrig) + Tabelle mit Vorschlägen + Häkchen pro Feld + „Übernehmen"-Button.
**Warum:** Spart Recherche-Arbeit beim Anlegen oder Anreichern von Kontakten.

### ✅ KI „Suchprofil schärfen" für Käufer
**Was:** Im Suchprofil-Tab gibt es einen lila Button „Mit Assistent schärfen". Assistent stellt 3–5 konkrete Rückfragen, die das Suchprofil präziser machen.
**Warum:** Jenny kann ihrem Käufer-Mandanten gezielte Beratungsfragen liefern, statt mit Allgemein-Plätzen zu arbeiten.

### ✅ KI „Match-Begründung" pro Long-List-Kandidat
**Was:** Sparkles-Icon pro Kandidat in der Long-List. Klick → Assistent bewertet das Match zwischen Suchprofil und Kandidat: Score (0–100, farbcodiert), Pro-Argumente, Contra-Argumente, Begründung.
**Warum:** Schnelle objektive Einschätzung vor manueller Bewertung.

### ✅ Mehrere E-Mails + Telefone pro Kontakt
**Was:** Im CRM-Edit-Modal kannst du jetzt zusätzliche E-Mails und Telefon-Nummern erfassen — jeweils mit Label (z.B. „mobil", „büro", „privat"). Werden in der KundenAkte unter den Standard-Feldern als klickbare Links angezeigt.
**Warum:** Realität ist, dass Ansprechpartner mehrere Kontaktwege haben — die kannst du jetzt sauber abbilden.

### ✅ Browser-Push-Benachrichtigungen (Admin)
**Was:** In **Einstellungen → Browser-Benachrichtigungen** ein neuer Toggle. Aktivieren → Browser fragt Erlaubnis → du wirst sofort benachrichtigt, sobald ein Mandant im Verlauf schreibt.
**Warum:** Schnellere Reaktion auf Mandanten-Nachrichten ohne ständiges Reinklicken.

---

## Für Mandanten (Verkäufer + Käufer)

### ✅ Browser-Push-Benachrichtigungen
**Was:** In „Mein Projekt" am Ende ein Toggle „Benachrichtigungen". Aktivieren → Browser-Erlaubnis → bei neuer Nachricht von Jenny erscheint Desktop-Benachrichtigung.
**Warum:** Mandant verpasst keine wichtige Nachricht mehr.

---

## Für die Compliance / Datenschutz

### ✅ VAPID-Keys für Push-Notifications
**Was:** Neue Azure-App-Settings `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`. Notwendig für signierte Web-Push-Nachrichten nach dem VAPID-Standard (RFC 8292).
**Warum:** Schließt Spam aus, identifiziert mibeca als Absender beim Push-Service (Google FCM / Apple APNs / Mozilla).

### ✅ Neue Tabelle `pushsubs`
**Was:** Speichert Browser-Subscriptions (endpoint, p256dh-key, auth-key) pro User. Wird beim Toggle „on" angelegt, beim „off" wieder gelöscht.

### ✅ Neue API-Endpoints (4)
- `GET /api/push-config` — Public-Key abrufen
- `POST /api/push-subscribe` — Subscription speichern
- `POST /api/push-unsubscribe` — Subscription löschen
- `POST /api/push-test` — Test-Push an eigenen Account

### ✅ Service Worker
**Was:** `/sw.js` läuft im Browser des Mandanten/Admins und empfängt Push-Nachrichten auch wenn der Tab geschlossen ist.

### ✅ Vier weitere KI-Aktionen dokumentiert
Die `/api/ai-action`-Route unterstützt jetzt 5 statt 1 Aktion (siehe Security-Konzept §1a).
Audit-Aktion `ai_action` mit Sub-Typ in Details-JSON.

---

## Was offen ist

Aktuell **nichts mehr aus der Phase-2-Liste**. Die nächsten Themen sind anlass-getrieben (aus Praxis-Erkenntnissen der nächsten Wochen).

Punkte für DSB / Geschäftsführung (organisatorisch, kein Code) siehe `docs/0-README.md`:
- AVV mit Anthropic
- DSFA durchführen
- Mandanten-Info-Beilage finalisieren
- Anthropic-Budget-Limit setzen
- API-Key rotieren (optional)
