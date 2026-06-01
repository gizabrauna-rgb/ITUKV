# Nutzerhandbuch: Admin (mibeca-Berater)

**Stand:** 2026-05-29
**Zielgruppe:** Anna, Jenny und ggf. weitere mibeca-Berater
**Voraussetzung:** Admin-Account ist angelegt

---

## Inhalt

1. Login
2. Aufbau des Admin-Portals
3. Übersicht-Tab – dein Tages-Cockpit
4. Projekte-Tab – alle Mandate verwalten
5. Eine einzelne Akte arbeiten
6. CRM-Tab – Kontakte verwalten
7. KI-Funktionen nutzen (detailliert)
8. Veröffentlichte Mandate (Landing-Pages)
9. E-Mail-Vorlagen + Drip-Sequenzen
10. Controlling + Beirats-Bericht
11. Benutzer-Verwaltung
12. Audit & Backup
13. Tipps & Tricks

---

## 1. Login

1. Browser → **https://dashboard.itukv.de**
2. **„Mit Microsoft anmelden"** klicken
3. Mibeca-Microsoft-Konto wählen (z. B. `ab@mike-bergmann.de`)
4. Du landest in der **Übersicht**

Kein Passwort nötig – läuft über Microsoft Entra ID.

---

## 2. Aufbau des Admin-Portals

Sidebar links zeigt die Hauptbereiche:

| Tab | Was findest du? |
|---|---|
| **Übersicht** | Tages-Cockpit: was wartet auf dich, letzte Aktivitäten, Termine |
| **Projekte** | Alle Mandate als Tabelle (Cockpit + Liste in einer Ansicht) |
| **Kontakte** | CRM mit Karten-Ansicht (Investoren, Käufer, Verkäufer) |
| **Veröffentlichte Mandate** | Anonyme Landing-Pages für Marktansprache |
| **Dokumente** | Globale Dokumenten-Übersicht |
| **E-Mail-Vorlagen** | Drip-Sequenzen + Vorlagen |
| **Controlling** | Pipeline-Auswertung, Beirats-Bericht |
| **Benutzer** | User anlegen / verwalten |
| **Audit & Backup** | Was wurde gemacht? + Backups |
| **Einstellungen** | Compliance-Schalter, KI-Konfiguration |

Oben rechts: Glocke für ungelesene Nachrichten + Logout.

---

## 3. Übersicht-Tab – dein Tages-Cockpit

### Was du hier siehst

- **Stats:** Aktive Mandate, offene NDAs, Investoren, abgeschlossene Deals
- **„Wartet auf mich":** alle akuten To-dos in Listenform mit Klick-Direktlink:
  - Vertrag gegenzeichnen
  - NDA prüfen
  - Wiedervorlage fällig
  - Mandate läuft aus
  - Pressetext genehmigen
  - Ungelesene Nachrichten
  - Fragebogen auswerten
  - Exposé-Korrektur / Freigabe-wartend
- **Letzte Aktivitäten** der Mandanten (chronologischer Feed)
- **Anstehende Termine** (aus den Mandaten)

### Wofür?

Morgens reinschauen → siehst sofort, was an einem Tag zu tun ist. Klick auf jede
Karte → öffnet direkt die richtige Stelle in der jeweiligen Akte.

---

## 4. Projekte-Tab – alle Mandate verwalten

### Wie die Tabelle aufgebaut ist

| Spalte | Inhalt |
|---|---|
| WV-Punkt (farbig) | Status der Wiedervorlage (rot = überfällig, gelb = heute) |
| mb-Nr | Mandate-Nummer + NEU-Badge wenn Mandant <3 Tage aktiv |
| Name / Firma | Wer ist das |
| Region | Wo |
| Typ | UVE Target / Projekt Target / Kauf-Mandat / … |
| Aktuelle Phase | Titel + Fortschritts-Balken |
| Mandant zuletzt | Was hat der Mandant zuletzt gemacht? |
| Nächster Schritt für dich | mibeca-Aufgabe in der aktuellen Phase (gelb wenn dringend) |
| Status | Verfügbar / In Verhandlung / Verkauft / … |
| Wiedervorlage | Termin mit Farb-Markierung |
| Aktion | Löschen |

### Was du tun kannst

- **+ Neues Projekt** (oben rechts) → Modal mit Pflichtfeldern
- **Klick auf Zeile** → öffnet die volle Akte des Mandates
- **Status inline ändern** → Dropdown direkt in der Zelle
- **Wiedervorlage setzen/löschen** → Datums-Picker in der Zelle
- **Filter:** Suche, Status, Mandat-Richtung (Verkauf/Kauf), Projekttyp
- **Mandate löschen** → Trash-Icon (kommt Bestätigungsdialog)
- **Farb-System (seit 29.05.):**
  - 🟠 Orange = Verkäufer-/Target-Mandate
  - 🟢 Grün = Käufer-/Investor-Mandate
  - 🟣 Lila = nur Assistent-Funktionen
  - 🔵 Mibeca-Blau = Standard-Buttons

### Tipp

Schau morgens drauf, sortier nach „Mandant zuletzt = neu" → direkt erkennen, wer
gerade aktiv ist und mit dir kommunizieren möchte.

---

## 4a. Verkaufs-Pipeline (seit 30.05.2026)

Kanban über **alle Verkaufs-Mandate**. Spalten = die 15 Master-Phasen, Karten =
einzelne Mandate. Auf einen Blick siehst du, wo welcher Verkäufer hängt und wie
viele Mandate in welcher Phase sind.

**Funktionen:**
- Umschalten Kanban ↔ Tabelle
- Filter: Status, Firma / mb-Nr-Suche
- Klick auf eine Karte öffnet die Akte direkt im Master-Prozess-Tab
- Aktuelle Phase wird automatisch errechnet (erste nicht-abgehakte Phase)
- Counter pro Spalte zeigt die Mandate-Anzahl

**Wann nutzen?** Tägliche Verlaufskontrolle, Bottleneck-Erkennung („alle stehen
in Phase 8 — warum?"), Planungsgespräch mit dem Team.

---

## 4b. Akquisitions-Pipeline (seit 30.05.2026)

Genauso wie die Verkaufs-Pipeline, nur für die **Käufer-Seite**: Kanban über alle
Akquisitionen aller Investoren (über alle mb-Nrn hinweg). Spalten = die 11
Akquisitions-Phasen.

**Pro Karte siehst du:**
- mb-Nr des Investors
- Firma des Targets
- Status-Badge
- Offene Aufgaben (Anzahl)

**Filter:** Status, Investor, Firmen-Suche.

**Klick auf eine Karte** öffnet die Akte des Investors direkt im neuen
„Akquisitionen"-Tab.

### Wo finde ich diesen Tab?

In der Käufer-Akte (mb-Nr mit Projekttyp „Kauf-Mandat") gibt es den Tab
„Akquisitionen" (Tab-Gruppe „Marktansprache"). Dort siehst du alle Akquisitionen
dieses Investors als Karten-Liste mit Phase + Status + offenen Aufgaben.

**Klick auf eine Karte** öffnet das **Akquisitions-Detail** mit 6 Sub-Tabs:
- **Übersicht** – Stammdaten, Phase-Wechsel (Dropdown), Status, Mandat-Position
  (Verkäufer/Käufer/beidseitig — wichtig für Provisions-Abrechnung)
- **Aufgaben** – Standard-Aufgaben werden beim Phase-Wechsel automatisch
  angelegt; eigene können hinzugefügt werden
- **Verlauf** – Chat zwischen mibeca und Käufer pro Akquisition; Phase-/Status-
  Wechsel werden automatisch als System-Eintrag dokumentiert
- **Termine** – Erstgespräch, DD-Workshop, Notartermin, … mit Datum/Ort/
  Teilnehmern
- **Dokumente** – Links zu NDA, Exposé, LOI, DD-Material, SPA-Entwurf (kategorisiert)
- **Notizen** – Käufer-Notizen (sichtbar für beide) + interne Notizen (nur mibeca)

### Wichtige Eigenschaften

- **Mandat-Position** entscheidet, wer Provision zahlt. Standard ist
  „Verkäufer-Mandat" (auch wenn der Investor sucht — siehe Master-Prozess Modell 2).
- **Auto-Anlage**: Klickt der Käufer im Tab „Target-Vorschläge" auf „Interesse",
  wird automatisch eine Akquisition (Phase 2) angelegt.
- **Idempotent**: doppeltes Klicken erzeugt keine Duplikate; manuell angelegte
  Akquisitionen werden nie überschrieben.

---

## 5. Eine einzelne Akte arbeiten

### Akte öffnen

Klick auf eine Zeile im Projekte-Tab oder von der Übersicht aus über die „Wartet
auf mich"-Karten.

### Aufbau der Akte (Tab-Gruppen oben)

| Gruppe | Sub-Tabs |
|---|---|
| **Übersicht** | Übersicht, Master-Prozess |
| **Mandat** | Mandat-Daten, **Ziele & Motivation / Strategie & Ziele**, Fragebogen, Bewertung, Suchprofil |
| **Verträge** | NDA + Mandatsvertrag + Kaufvertrag |
| **Marktansprache** | Exposé, Landing-Page, Interessenten, Long-List |
| **Datenraum** | Dokumente |
| **Abschluss** | Zwischenstand, LOI-Verhandlung, Erfolgsmeldung, Lessons Learned |
| **Verwaltung** | Verlauf, Zeiterfassung |

### Wichtige Aktionen pro Tab

**Übersicht** – Stammdaten auf einen Blick, Phasen-Mini-Visualisierung
**Master-Prozess** – die volle 15- bzw. 10-Phasen-Checkliste mit Auto-Häkchen
**Mandat-Daten** – persönliche + geschäftliche Stammdaten editieren
**Ziele & Motivation** – strukturierte Antworten des Mandanten lesen (Beratungsgrundlage)
**Fragebogen** – Unternehmensbewertung des Mandanten einsehen, ggf. zur Bewertung übertragen
**Bewertung** – mibeca-internes Scoring (Multi-Faktor-Bewertung)
**Suchprofil** – nur bei Käufer-Mandaten: Suchkriterien
**NDA / Verträge** – Verträge erstellen, an Mandanten zur Online-Unterschrift senden, gegenzeichnen
**Exposé** – KI-Generator („Exposé erstellen") + manuell editieren, freigeben
**Landing-Page** – anonyme Ausschreibung erstellen, veröffentlichen
**Interessenten** – Pipeline mit Kanban-Spalten (NDA, Erstgespräch, Gebot, …)
**Long-List** – Kandidaten-Match (Kauf-Mandate)
**Dokumente** – Datenraum mit Ordner-Struktur + Upload + **KI-Analyse-Button**
**Zwischenstand** – Status-Bericht als PDF generieren
**LOI-Verhandlung** – LOI-Punkte mit Verkäufer-/Käufer-Angeboten + Einigung
**Erfolgsmeldung** – Pressetext, Versand-Workflow
**Lessons Learned** – nach Abschluss strukturierte Auswertung
**Verlauf** – komplette Kommunikation chronologisch (Mail, Telefon, Notizen, KI-Einträge)
**Zeiterfassung** – Stunden-Tracking für Abrechnung

---

## 6. CRM-Tab – Kontakte verwalten

### Was hier liegt

Alle Kontakte (Investoren, Käufer, Verkäufer-Pool, Nichtkunden, etc.) in einer
Datenbank. Aktuell ~5.000 Einträge.

### Was du machen kannst

- **Karten-Ansicht:** alle Kontakte auf einer Karte mit PLZ-Radius-Filter
- **Listen-Ansicht:** filterbar nach Typ, Status, Branche
- **Suche:** über Firma, Name, Mail, PLZ, „bietet", „sucht"
- **Bulk-Import** aus Excel/CSV
- **Bulk-Export** als CSV
- **+ Neuer Kontakt** Modal
- **Kontakt-Akte** öffnen (Klick auf Zeile) – mit eigenen Tabs (Übersicht, Produkte,
  Projekte, Verlauf, Dokumente, Notizen)
- **Mehrere E-Mails / Telefone pro Kontakt** (seit 29.05.): Im Edit-Modal kannst du
  beliebig viele zusätzliche Adressen + Telefone mit Label hinterlegen (z.B. „mobil",
  „büro", „privat"). Werden in der KundenAkte alle nebeneinander angezeigt.
- **„Mit Assistent anreichern"-Button** im Akten-Header → KI schlägt Stammdaten-
  Ergänzungen vor, du übernimmst pro Feld.

### Tipp

Für Marktansprache: PLZ-Radius-Filter setzen + Branchen-Filter → alle Kontakte
in der Nähe des Mandates exportieren → in eine Drip-Sequenz einspeisen.

---

## 7. KI-Funktionen nutzen (detailliert)

> Siehe auch eigenes Dokument: **KI-Moeglichkeiten-Detail.md**

### 7.1 KI-Analyse auf Dokumenten

**Wann sinnvoll?**
- BWA oder Jahresabschluss hochgeladen → Kennzahlen schnell extrahieren
- Exposé/PDF einer fremden Firma → Eckdaten ohne manuelles Tippen
- Handelsregister-Auszug → Geschäftsführer-Liste + Gründungsdatum

**Anleitung:**
1. Akte öffnen → **Datenraum**
2. PDF auswählen (oder neu hochladen)
3. **Lila „KI-Analyse"-Button** klicken
4. Warten (5–30 Sek je nach PDF-Größe)
5. Modal öffnet sich mit Vorschlägen pro Feld
6. Pro Feld: Häkchen setzen, ob übernehmen oder nicht
7. **„Übernehmen"** klicken → Werte gespeichert + Verlauf-Eintrag „KI-Analyse"

**Wichtig:**
- Maximal 10 MB PDF
- Bei >5 MB wird der Button **gelb** (Warnung wegen Token-Limit)
- Erstes Mal pro Akte: explizit **„KI-Analyse für diese Akte erlauben"** (Opt-In)
- Token-Verbrauch + Kosten landen im Audit-Log
- Die KI sieht **nur das eine PDF**, nicht den Rest der Akte

### 7.2 KI-Coworker (Jennys externer Assistent)

**Wann sinnvoll?**
- Recherche zu vielen Kontakten gleichzeitig (CRM anreichern)
- Long-List-Aufbau aus externen Quellen
- Verlauf-Notizen verschriften / zusammenfassen
- Match-Analyse zwischen Mandate und Kontakten

**Wie Jenny es benutzt:**
Sie spricht mit ihrem Coworker (außerhalb des Dashboards) und sagt, was zu tun ist.
Der Coworker ruft dann die API mit dem Service-Account auf und schreibt erlaubte
Felder ins Dashboard.

**Was die KI darf:**
- Stammdaten in Kontakten + Mandaten ergänzen (begrenzte Feldliste)
- Verlauf-Einträge anhängen
- Listen lesen

**Was die KI NICHT darf:**
- mb-Nummer, Status, Projekttyp ändern
- Verträge erstellen
- User anlegen
- Dokumente hochladen
- Mails versenden

**Audit:**
Jeder KI-Schreibvorgang wird im Audit-Log als Aktion `ai_update` protokolliert mit
allen geänderten Feldern (alt + neu).

### 7.3 Assistent-Aktionen direkt aus dem Dashboard (seit 29.05.2026)

Statt die KI nur über den Coworker zu nutzen, gibt es **lila Buttons** direkt an den
richtigen Stellen im Dashboard:

#### „Assistent" (Topbar)
- Lila Funken-Button oben rechts in jedem Portal
- Öffnet einen Chat für allgemeine M&A-Fragen
- Konversation bleibt erhalten innerhalb des Modals
- Antworten als Markdown gerendert (Tabellen, Listen, Fett)

#### „Verlauf zusammenfassen" (Target-Akte → Verlauf-Tab)
- Lila Button rechts oben im Verlauf
- Assistent liest den kompletten Kommunikationsverlauf
- Liefert strukturierte Status-Zusammenfassung:
  - 📍 Aktueller Stand
  - ✅ Was wurde erledigt
  - ⏳ Was steht aus
  - ⚠️ Risiken / offene Themen
  - 💡 Empfehlung nächster Schritt
- Praktisch vor Beirats-Meetings oder beim Übergeben an Vertretung

#### „Mit Assistent anreichern" (Kundenakte → Header)
- Lila Button im Akten-Header neben „Bearbeiten"
- Assistent recherchiert aus Allgemein-Wissen Stammdaten-Vorschläge
- Modal mit Konfidenz-Badge + Feldweise-Häkchen
- Per Klick übernimmst du nur die Vorschläge, die du verifizierst
- Spart Recherchezeit beim CRM-Pflege

#### „Mit Assistent schärfen" (Suchprofil-Tab)
- Lila Button in Suchprofil-Akten bei Käufer-Mandanten
- Liefert 3–5 konkrete Rückfragen, die dein Suchprofil präziser machen
- Nicht zur Übernahme – als Beratungs-Input für dein nächstes Gespräch

#### „Match-Bewertung" (LongList → pro Kandidat)
- Sparkles-Icon neben jedem Kandidaten in der Long-List
- Score 0–100 + Pro/Contra-Argumente + Begründung
- Hilft beim schnellen Sortieren der Long-List

### 7.4 KI im Notfall stoppen

**Sofort-Aus (Anna):**
Azure Portal → `itukv-func-v2` → Configuration → `AI_ANALYSE_AKTIV` auf `false` setzen
→ Save → Function App startet automatisch neu → keine KI-Aufrufe mehr möglich.

**API-Key sperren:**
Anthropic Console → API Keys → revoken. Bestehende Aufrufe schlagen sofort fehl.

**Pro Akte:**
In der Akte → „KI-Analyse erlauben" auf `false` setzen → für diese Akte ab sofort gesperrt.

---

## 8. Veröffentlichte Mandate (Landing-Pages)

### Wofür?
Anonyme Ausschreibungen für die Marktansprache. Beispiel: `targets.itukv.de/mb-XXX`
zeigt Eckdaten eines Verkaufs-Mandates an, ohne die Firma zu nennen.

### Anleitung
1. Akte öffnen → **Landing-Page**
2. Inhalte editieren (Branche, Umsatz-Spanne, USP-Stichworte)
3. Vorschau anzeigen
4. **„Veröffentlichen"** → Landing-Page geht online
5. Interessenten können NDA über die Landing-Page anfordern → landet automatisch
   im **Interessenten-Tab** der Akte

### Übersicht aller Landing-Pages
Linker Tab **„Veröffentlichte Mandate"** zeigt alle online geschalteten Ausschreibungen.

---

## 9. E-Mail-Vorlagen + Drip-Sequenzen

### Vorlagen
Vorgefertigte E-Mails für wiederkehrende Anlässe (NDA-Einladung, Exposé-Versand,
Termin-Bestätigung etc.). Editierbar in **„E-Mail-Vorlagen"**.

### Drip-Sequenzen
Automatisierte Mail-Folgen über mehrere Tage. Beispiel: nach NDA-Versand am Tag 1,
3 und 7 erinnern, wenn nicht unterschrieben.

### Anleitung
1. Tab **„E-Mail-Vorlagen"**
2. Sequenz erstellen oder bearbeiten
3. Schritte definieren (Tag X nach Trigger Y → diese Vorlage senden)
4. Sequenz an Mandate oder Kontakt zuweisen
5. System verschickt automatisch

---

## 10. Controlling + Beirats-Bericht

### Controlling-Tab
- Aktuelle KPIs (Mandate gesamt, Abschlüsse, Deal-Dauer, PR-Quote)
- Pipeline-Wert + Provisions-Forecast
- Top-Mandate nach Umsatz
- Pipeline-Funnel (grobe Phasen-Buckets)
- **Phasen-Verteilung pro Verkauf/Kauf** (jede Phase mit Mandate-Liste)
- Deal-Dauer pro Projekttyp
- Monatlicher Verlauf
- Lessons-Learned-Aggregat

### Beirats-Bericht
**„Beirats-Bericht (PDF)"**-Button oben rechts → generiert ein druckfertiges PDF
mit allen wichtigen Kennzahlen + Lessons Learned. Ideal für Quartalsbericht an die GF.

---

## 11. Benutzer-Verwaltung

### Neuer Benutzer

1. Tab **„Benutzer"** → **+ Neuer Benutzer**
2. **Rolle wählen** (Admin, Verkäufer, Investor)
3. Bei Verkäufer/Investor: **Mandate-Picker** mit allen 6 Ansichten:
   - Verkäufer-Ansichten: UVE Target / Projekt Target / MC Target
   - Käufer-Ansichten: Kauf-Mandat / Projekt Investoren / MC Investoren
4. Bei Admin / interner Domain (`@mike-bergmann.de`, `@mibeca.de`): **kein Passwort**
   – User loggt sich via Microsoft an
5. Bei externen Mandanten: System generiert ein **12-stelliges Passwort** + verschickt
   eine Willkommens-Mail mit Login-Daten

### Passwort-Reset
Per Klick „Zugangsdaten neu senden". System generiert ein neues Passwort und mailt
es an den User. Alternativ: User klickt selbst auf „Passwort vergessen?" im Login.

### User löschen
Trash-Icon → Bestätigung → User ist sofort entfernt. **Wichtig:** Mandate bleibt
erhalten (gehört dem Mandate, nicht dem User). Nur der Login-Zugriff geht verloren.

---

## 12. Audit & Backup

### Audit-Log
Jeder Schreibvorgang ist hier protokolliert. Filter nach:
- User
- Mandate
- Zeitfenster
- Aktion (create, update, delete, ai_update, …)

### Backup
- **Wöchentlich automatisch** (Sonntags 03:00 UTC)
- **12-Wochen-Rotation**
- **Manuell:** „Sofort-Backup"-Button → JSON-Datei in Blob `backups/`
- **Recovery:** über Admin-Skript möglich (Anna macht das)

---

## 12a. Verlauf-Suche (seit 29.05.2026)

Im Verlauf-Tab gibt es **ein Such-Feld** über den Filter-Pills.
- Tippe ein Wort ein → durchsucht **Betreff, Beschreibung, Autor, Beteiligte**
- Funktioniert kombiniert mit den Typ-Filtern (Telefon, E-Mail, …)
- Rechts oben siehst du die Anzahl der Treffer
- ✕-Button leert die Suche

**Praktisch für:**
- „Wo war nochmal die Mail vom Steuerberater?" → Name oder Mailadresse eintippen
- Schnell zum richtigen Termin springen
- Bei Mandaten mit vielen hundert Einträgen kein endloses Scrollen mehr

## 12b. Element-Verlauf importieren (seit 29.05.2026)

Wenn ihr noch Element-Räume zu Mandanten habt, kannst du den kompletten Verlauf
einmalig in die Akte importieren, damit alles zentral im Dashboard liegt.

### Schritt 1: Element-Export
1. Element öffnen → den Raum öffnen
2. **Klick auf den Raum-Namen** im Header → Raum-Info erscheint rechts
3. **„Exportieren von Chats"** wählen
4. Format: **JSON**, Nachrichten: **„Von Anfang an"**, Größenlimit: **500 MB**
5. Anhänge: **nicht einbeziehen** (Bilder/Dateien werden ignoriert)
6. **Exportieren** → JSON-Datei wird heruntergeladen

### Schritt 2: Import im Dashboard
1. Im ITUKV-Dashboard die passende Akte öffnen (mb-XXX)
2. Tab **Verlauf**
3. Oben rechts **„Element-Verlauf importieren"** klicken
4. **Datei auswählen** (die JSON aus Schritt 1)
5. **Optional: Matrix-ID von Jenny** eintippen
   - Format: `@jennypy:matrix.mibeca.de` oder ähnlich
   - Findest du in Element → eigenes Profil-Icon → Mein Profil
   - Wenn gesetzt: ihre Nachrichten werden als **Chat gesendet** (mibeca-Seite) markiert,
     alle anderen als **Chat eingegangen** (Mandant-Seite)
6. **„Vorschau"** klicken — System zeigt erste 5 Nachrichten + Gesamt-Anzahl
7. Wenn's passt: **„Importieren"** → Verlauf-Einträge werden chronologisch in die Akte gekippt
8. Modal schließen — Verlauf lädt sich automatisch neu

### Wichtige Hinweise
- **Doppel-Import unproblematisch:** Wenn du den Import nochmal startest, werden bereits
  importierte Nachrichten via Event-ID automatisch übersprungen.
- **Element-Räume sind groß:** Daten werden in einer separaten Tabelle gespeichert
  (nicht in der 32K-begrenzten kommunikationJson), damit auch tausende Nachrichten
  problemlos importierbar sind.
- **Typ „Chat"** statt „E-Mail": Element-Nachrichten erscheinen mit dem türkisen
  Chat-Badge — klar erkennbar als Element-Import, nicht als E-Mail-Konversation.
- **Marker „(Element-Import)"** im Betreff: damit jederzeit klar ist, woher die
  Einträge stammen.
- **Element-Räume können danach geschlossen werden** — Daten liegen vollständig im
  Dashboard.

### Pro Mandate einmalig
Jeden Element-Raum, der zu einem Mandate gehört, einmalig exportieren + importieren.
Danach läuft die Kommunikation nur noch über das Dashboard.

---

## 13. Browser-Push-Benachrichtigungen (seit 29.05.2026)

**Wofür?** Du wirst sofort benachrichtigt, sobald ein Mandant im Verlauf schreibt –
auch wenn das Dashboard-Tab geschlossen ist.

**Aktivieren:**
1. **Einstellungen-Tab** → Sektion **„Browser-Benachrichtigungen"**
2. Toggle umlegen → Browser fragt nach Erlaubnis → **Erlauben** klicken
3. Optional: **„Test"**-Button drücken → du solltest sofort eine Notification sehen

**Funktioniert mit:** Chrome, Edge, Firefox, Safari (alle modernen Browser).
**Funktioniert NICHT mit:** iOS Safari (nur in Standalone-PWA-Modus, nicht im normalen Tab).

**Deaktivieren:** Toggle wieder ausschalten oder in den Browser-Einstellungen
für `dashboard.itukv.de` blockieren.

**Datenschutz:** Subscription wird in Azure (EU) gespeichert. Push-Inhalt ist
verschlüsselt; nur dein Browser kann ihn lesen. Apple/Google/Mozilla sehen nur eine
verschlüsselte Bytefolge, keine Mandanten-Daten.

---

## 14. Tipps & Tricks

- **Glocke oben rechts:** zeigt ungelesene Mandanten-Nachrichten – nicht ignorieren
- **Cmd+Shift+R** wenn was komisch aussieht → Hard-Reload
- **Tab bleibt nach Reload erhalten** – auch im Admin-Bereich
- **Suche im Projekte-Tab** auch über mb-Nr / Region / Branche
- **CRM-Karten-Ansicht** ist gold wert für PLZ-Filter-Recherche
- **„Mandant zuletzt"-Spalte** sortieren → siehst sofort, wer aktiv war
- **Beirats-Bericht** vor jedem Quartals-Meeting frisch generieren
- **Audit-Log monatlich kurz durchscrollen** als Hygiene-Maßnahme

---

## Wer hilft bei Fragen?

| Problem | Wer |
|---|---|
| „Ich komm nicht rein" | Anna |
| „Da ist ein Bug" | Anna |
| „Wie ist der Prozess gemeint" | Jenny |
| „KI macht Quatsch" | Anna (technisch) + Jenny (fachlich) |
| „Wann ist welche Phase fertig" | Master-Prozess-Tab in der Akte |
| „Wer hat Zugriff" | Rollen-Übersicht oder Anna |
