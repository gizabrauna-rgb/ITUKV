# KI im ITUKV-Dashboard – was geht alles?

**Stand:** 2026-05-28
**Zielgruppe:** Anna, Jenny, Geschäftsführung, DSB
**Voraussetzung:** KI-Funktion ist global aktiv (`AI_ANALYSE_AKTIV=true`)

---

## Übersicht: Es gibt zwei KI-Bereiche

Die mibeca nutzt KI an **zwei unterschiedlichen Stellen**:

| | KI-Analyse (im Dashboard) | KI-Coworker (außerhalb) |
|---|---|---|
| **Was ist es?** | „KI-Analyse"-Button im Datenraum | Jennys externer KI-Assistent |
| **Wer löst aus?** | Admin (Mensch klickt) | Jenny mit ihrer eigenen KI |
| **Worauf wirkt es?** | Einzelnes Dokument | Stammdaten + Verlauf |
| **Datenfluss** | Dashboard → Anthropic | Externer Assistent → ITUKV-API |
| **Beispielanwendung** | BWA hochladen → Kennzahlen extrahieren | „Recherchier mir die Top-50-Investoren in NRW und ergänze sie im CRM" |

Beide nutzen **denselben Anthropic-API-Key**, aber sind funktional getrennt.

---

## Bereich 1: KI-Analyse im Dashboard (Anna + Jenny)

### Was kannst du damit machen?

Du lädst ein PDF-Dokument in den Datenraum hoch (z. B. BWA, Jahresabschluss, Exposé,
Handelsregister-Auszug). Klick auf **„KI-Analyse"** – das System schickt das PDF an
Anthropic Claude und bekommt strukturierte Daten zurück, die du dann auf Knopfdruck
in die Mandate-Akte übernehmen kannst.

### Schritt-für-Schritt

1. **Admin-Akte öffnen** → Tab **Dokumente**
2. PDF hochladen oder vorhandenes auswählen
3. Klick auf den **„KI-Analyse"-Button** neben dem Dokument (lila, mit Funken-Symbol)
   - Bei großen PDFs (>5 MB) wird der Button **gelb** und warnt vor möglichen Token-Limits
4. Modal öffnet sich – Anthropic erhält das PDF und antwortet (typisch 5–30 Sek)
5. Im Modal werden die extrahierten Werte als **Vorschläge** angezeigt:
   - **Pro Feld** ein Häkchen „Übernehmen?"
   - **Pro Feld** ein Vergleich „aktuell im Dashboard" vs. „KI-Vorschlag"
6. **Du wählst manuell aus**, welche Werte übernommen werden – pro Feld
7. **„Übernehmen"** klicken → Werte werden gespeichert + Verlauf-Eintrag „KI-Analyse"
   wird angelegt

### Welche Felder extrahiert die KI?

Die KI kann folgende Felder aus typischen Geschäftsdokumenten erkennen:

- Firmenname, Rechtsform, Gründungsjahr, Sitz
- Geschäftsführer (Name + Funktion)
- Mitarbeiterzahl, Umsatz, EBIT, EBIT-Marge
- Wiederkehrender Umsatz-Anteil
- Branchenzuordnung
- Region / PLZ
- Frei strukturierte Notizen / Kennzahlen-Zusammenfassung

### Was die KI NICHT macht

- **Keine automatische Übernahme** – du bestätigst jeden Wert manuell
- **Keine Beratung** – sie macht nur Vorschläge auf Basis des PDFs
- **Keine Bewertung** – sie sagt nicht „Unternehmen ist X Mio wert"
- **Kein E-Mail-Schreiben** – sie verfasst keine Texte für Mandanten
- **Kein PDF-Editing** – das Original bleibt unverändert im Datenraum

### Pro-Akte-Opt-In

Bevor die KI auf einer **einzelnen** Mandate-Akte überhaupt loslegen darf, musst du
einmalig pro Akte den **„KI-Analyse für diese Akte erlauben"**-Schalter umlegen.
Bestätigungsdialog zwingt zur expliziten Entscheidung – verhindert versehentliche
Nutzung. Der Mandant kann jederzeit den Opt-In zurückziehen (Anna oder Jenny
schaltet ihn aus).

### Audit-Log

Jeder KI-Aufruf erzeugt einen Audit-Eintrag mit:

- Wer hat es ausgelöst (Anna oder Jenny)
- Wann (Zeitstempel)
- Welches Dokument
- Token-Verbrauch (Kostenkontrolle)
- Welche Werte vorgeschlagen / übernommen wurden

Einsehbar im Tab **„Audit & Backup"**.

### Notfall-Aus

In Azure App-Settings den Schalter `AI_ANALYSE_AKTIV` auf `false` setzen. Sofort
keine KI-Aufrufe mehr möglich. Bereits gespeicherte Werte bleiben erhalten.

---

## Bereich 2: KI-Coworker (Jennys externer Assistent)

### Was ist das?

Jenny nutzt einen **externen KI-Assistenten** (Claude-basiert), der mit dem ITUKV-
Dashboard über eine API spricht. Sie sagt dem Assistenten z. B.:

> *„Recherchier mir 50 IT-Systemhäuser in Bayern mit 10–30 Mitarbeitern und
> trag sie als potenzielle Investoren ins CRM ein."*

Der Assistent kann dann mit einem speziellen **Service-Account** (`ai-agent`)
Daten ins Dashboard schreiben – allerdings nur in **streng begrenzten Feldern**.

### Was kann der KI-Coworker konkret?

#### Kontakte (CRM) anreichern
Der Coworker darf folgende Felder bei Kontakten setzen oder ergänzen:

- Geschäftsführer (Name)
- Telefon, Mail, Website
- PLZ, Ort, Region, Branche
- Mitarbeiterzahl, Umsatz, EBIT-Marge, Recurring-Anteil
- Stichworte „bietet" / „sucht"
- Kommentar-Felder
- Strukturierte JSON-Blobs (z. B. Ansprechpartner-Listen, Handelsregister-Daten)

Bulk-Update: bis zu **500 Einträge pro Aufruf**.

#### Mandate anreichern
- Region, PLZ, Branche, Mitarbeiter, Umsatz, EBIT-Marge, Recurring-Anteil
- Rechtsform, Gründungsjahr
- Geschäftsführer (Name)
- Beschreibungs-Text
- Bewertungs-JSON, Fragebogen-JSON, Suchprofil-JSON

#### Verlauf-Einträge anhängen
- Typ „Notiz" oder „KI-Analyse" mit Betreff + Beschreibung
- Z. B. „KI hat folgende Northdata-Daten zu Firma X recherchiert: …"
- Wird in der Akte mit **„KI-Coworker"**-Marker angezeigt

#### Listen abrufen
- Alle Mandate (lesend)
- Alle Kontakte (lesend)
- Status, Stammdaten, Beziehungen

### Was kann der KI-Coworker NICHT?

- **Keine mb-Nummer, Status, Projekttyp ändern** – organisationsseitig vergebene
  Felder sind gesperrt (auch für die KI)
- **Keine Verträge anlegen oder bearbeiten**
- **Keine User anlegen oder Passwörter setzen**
- **Keine Dokumente hochladen/löschen** im Datenraum
- **Kein Mail-Versand** über die mibeca-Mail-Infrastruktur
- **Kein Audit-Log einsehen oder löschen**
- **Keine Berechtigungen erweitern**

### Wie ist der Service-Account abgesichert?

- **Eigene Rolle `ai-agent`** mit minimalen Schreibrechten
- **Eigene API-Endpoints** (`/ai-bulk-update`, `/ai-verlauf-add`) mit Schreib-Allowlist
- **Doppelter Mass-Assignment-Schutz** – selbst innerhalb der Allowlist greift die
  Admin-Only-Sperre
- **Jeder Aufruf wird im Audit-Log mit Aktion `ai_update` protokolliert**
- **Bulk-Limit:** max. 500 Einträge pro Aufruf
- **Rate-Limit:** über Azure Functions-Default geregelt

### Typische Anwendungsfälle für Jenny

| Aufgabe | Was Jenny sagt | Was passiert |
|---|---|---|
| „Long-List anreichern" | „Hol mir Stammdaten zu allen Kontakten ohne Umsatz-Angabe" | Coworker recherchiert + füllt `umsatzTeur` |
| „Investoren-Suche" | „Finde alle PE-Firmen die letzte 3 Jahre in DACH IT-Unternehmen gekauft haben" | Coworker recherchiert Web + legt Kontakte an |
| „Verlauf-Notizen verschriften" | „Schreib mir die Eckpunkte des Gesprächs mit Müller GmbH zusammen" | Coworker fasst zusammen + hängt Verlauf-Eintrag an |
| „Match-Analyse" | „Welche Kontakte aus dem CRM passen zu mb-316?" | Coworker liest beide + erstellt einen Verlauf-Eintrag mit Vorschlägen |

### Was Jenny IMMER manuell macht

- **Mandate anlegen** (mit mb-Nummer-Vergabe)
- **Verträge erstellen** (NDA, Mandatsvertrag, Kaufvertrag)
- **Phasen-Status setzen** (Mandate in nächste Phase schicken)
- **Mandanten direkt anschreiben**
- **VETO-Prüfung mit Verkäufer**
- **Finale Bewertung der Vorschläge**

Die KI ist **Beraterin / Helferin**, nicht Entscheiderin.

---

## Kosten-Kontrolle

| Bereich | Wer zahlt? | Limit |
|---|---|---|
| KI-Analyse (Dashboard) | mibeca direkt an Anthropic | gemeinsam mit Coworker |
| KI-Coworker | mibeca direkt an Anthropic | empfohlen 50 USD/Monat (siehe Vorlage 5) |

Pro KI-Aufruf wird der Token-Verbrauch im Audit-Log gespeichert. Anna behält den
Überblick über das Monatsbudget.

---

## Datenschutz – Was muss der Mandant wissen?

Mandanten werden über die KI-Nutzung informiert (Vorlage 1: Mandanten-Information).
Wichtige Punkte:

- Anthropic ist Auftragsverarbeiter (AVV läuft)
- Daten werden in den USA verarbeitet (DPF + SCCs)
- Daten **nicht** zum Modell-Training verwendet (vertraglich zugesichert)
- Anthropic-Speicherung max. 30 Tage
- Mandant kann **pro Akte widersprechen** (Opt-Out)

---

## Wenn etwas schiefläuft

| Problem | Reaktion |
|---|---|
| KI-Antwort macht keinen Sinn | Vorschlag verwerfen, manuell eintragen. Im Audit notieren. |
| KI ist offline / langsam | Manuelle Bearbeitung möglich – KI ist nur Hilfsmittel |
| Budget-Limit erreicht | Anna setzt es kurzfristig hoch oder wartet auf nächsten Monat |
| Coworker macht etwas Unerwartetes | Audit-Log prüfen, Coworker-Anweisung präzisieren, im Notfall API-Key revoken |
| Mandant widerspricht | Pro-Akte-Opt-In zurücknehmen, alle KI-Verlauf-Einträge dieser Akte löschen |

---

## Wer hilft bei Fragen?

| Frage | An wen |
|---|---|
| KI macht Quatsch / falsche Werte | Anna (technisch) + Jenny (fachlich) |
| Kann die KI XY? | Anna |
| Datenschutz-Frage zur KI | DSB + Anna |
| Coworker-Anweisungen formulieren | Jenny (sie kennt ihren Assistenten am besten) |
| API-Key, Konfiguration, Limits | Anna |
