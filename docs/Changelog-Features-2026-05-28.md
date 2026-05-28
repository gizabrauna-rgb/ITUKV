# Was ist neu im ITUKV Dashboard – Stand 2026-05-28

**Zielgruppe:** Jenny, Anna, Geschäftsführung, Datenschutzbeauftragter
**Zweck:** Übersicht aller Verbesserungen, die in den letzten Tagen ins Dashboard
eingebaut wurden – in einfacher Sprache, ohne Tech-Jargon.

---

## Für Mandanten (Verkäufer & Käufer im Portal)

### ✅ Aufgeräumte Startseite
**Was:** Die Begrüßungsseite ist schlanker. Statt 4 doppelter Status-Kacheln gibt es jetzt nur noch eine Begrüßung + Hinweis auf die Ansprechpartnerin Jenny.
**Warum:** Information war doppelt vorhanden, war verwirrend. Jetzt klarer.

### ✅ „Was steht für dich an?" – nur noch eigene Aufgaben
**Was:** In der Aufgabenliste sieht der Mandant jetzt **nur Aufgaben, die wirklich er erledigen muss**. Alles, was Jenny / Anwalt / Notar machen, landet im Bereich „Was im Hintergrund läuft".
**Warum:** Vorher hat der Mandant fälschlich „Exposé erstellen" als seine Aufgabe gesehen, obwohl das mibeca macht.

### ✅ Automatische Häkchen
**Was:** Sobald der Mandant z.B. den Fragebogen abgibt, einen Dokument-Upload macht oder die Kostentabelle bestätigt, setzt das System automatisch den Haken in der Checkliste.
**Warum:** Keine manuelle Doppelung mehr nötig – das System „weiß", was schon erledigt ist.

### ✅ Erledigte Aufgaben jederzeit anpassen
**Was:** Unter „Was steht für dich an?" gibt es einen neuen Block „Bereits erledigt – kannst du jederzeit anpassen". Mandant klickt drauf → Formular öffnet sich mit den gespeicherten Antworten zum Ändern.
**Warum:** Vorher waren erledigte Aufgaben „weg" und man kam nicht mehr ran.

### ✅ Kosten-Tabelle als Modal
**Was:** Beim Klick auf „Kosten-Tabelle ansehen" öffnet sich eine Übersicht mit den typischen M&A-Kosten (mibeca-Honorar, Anwalt, Notar, Steuerberater, DD-Kosten). Inklusive 2 Beispiel-Szenarien und Nach-Steuer-Rechnung je Rechtsform. Mit „Verstanden"-Button.
**Warum:** Mandant weiß sofort, was finanziell auf ihn zukommt – ohne Excel zu öffnen.

### ✅ Ziele & Motivationen (Verkäufer)
**Was:** Neues Formular im Verkäufer-Portal. Mandant trägt strukturiert ein: Warum verkaufe ich? Zeitrahmen? Wunsch-Verkaufspreis? Rolle nach dem Verkauf? Was passiert mit Mitarbeitern/Standort? Earn-Out denkbar? Deal-Breaker?
**Warum:** Jenny bekommt sofort eine strukturierte Beratungs-Grundlage statt mündlicher Aussagen.

### ✅ Akquisitionsstrategie (Käufer)
**Was:** Pendant für Käufer. Strukturiert: Warum kaufen? Hold-Period? Max. Kaufpreis? Finanzierung (Eigenkapital + Bank)? Zielprofil (Branche/Region/Größe)? GF-Verbleib? Synergien? Deal-Breaker?
**Warum:** Genau wie beim Verkäufer – Jenny hat eine klare Beratungs-Grundlage.

### ✅ Tab bleibt nach Reload erhalten
**Was:** Wenn der Mandant die Seite neu lädt, bleibt er auf dem Tab, auf dem er gerade war. Vorher landete er immer wieder bei „Mein Projekt".
**Warum:** Spart Zeit, weniger Frust.

### ✅ Schutz vor versehentlichen Änderungen
**Was:** mb-Nummer, Transaktionsnummer und Kundennummer sind für den Mandanten **read-only**. Nur Anna/Jenny können diese setzen.
**Warum:** Diese Felder sind organisationsseitig vergeben – kein Risiko mehr, dass ein Mandant sie versehentlich überschreibt.

---

## Für Jenny / Anna (Admin-Portal)

### ✅ Projekte-Tab mit Cockpit + Liste in einer Ansicht
**Was:** Der Projekte-Tab zeigt jetzt pro Mandat:
- mb-Nr + Firma + Typ-Badge (Verkäufer / Käufer)
- **„NEU"-Badge** wenn der Mandant in den letzten 3 Tagen aktiv war
- Aktuelle Phase mit Fortschritts-Balken
- **„Was hat der Mandant zuletzt getan?"** (semantische Aktivität wie „Fragebogen abgegeben")
- **„Nächster Schritt für dich"** (was Jenny als Nächstes tun sollte, gelb wenn dringend)
- Status, Wiedervorlage, Aktionen (Löschen)
**Warum:** Statt zweier separater Tabs hast du alles auf einen Blick.

### ✅ Ziele & Strategie-Tab in der Akte
**Was:** In jeder Mandat-Akte gibt es jetzt einen Tab „Ziele & Motivation" (Verkäufer) bzw. „Strategie & Ziele" (Käufer). Hier siehst du strukturiert alle Mandanten-Antworten.
**Warum:** Beratungs-Grundlage auf einen Blick, ohne Klicken durch verschiedene Felder.

### ✅ Auto-Verlauf bei Mandanten-Aktionen
**Was:** Sobald ein Mandant eine Self-Service-Aufgabe abschließt, schreibt das System automatisch einen Verlauf-Eintrag in die Akte (z.B. „Aufgabe erledigt: Ziele & Motivationen ausgefüllt").
**Warum:** Du siehst im Verlauf-Tab sofort, was sich bei jedem Mandanten getan hat – ohne Push-Mails oder ständiges Reinklicken.

### ✅ Phasen-Verteilung im Controlling
**Was:** Im Controlling-Tab gibt es zwei neue Übersichten: „Verkäufer-Mandate pro Phase" und „Käufer-Mandate pro Phase". Pro Phase: Anzahl + mb-Nr-Chips der Mandate.
**Warum:** Du siehst sofort, wo deine Pipeline steht – wieviel ist in Phase 1, wieviel in DD, wieviel kurz vor Closing.

### ✅ User-Anlegen – Mandat-Picker mit allen 6 Ansichten
**Was:** Beim Anlegen neuer User siehst du alle Mandate in einem Dropdown, gruppiert nach „Verkäufer-Ansichten" (UVE / Projekt / MC Target) und „Käufer-Ansichten" (Kauf-Mandat / Projekt Investoren / MC Investoren). Mit Projekttyp pro Eintrag.
**Warum:** Klare Zuordnung – kein versehentliches Verknüpfen mit einem falschen Mandate-Typ mehr.

### ✅ Microsoft-User ohne Passwort
**Was:** Wenn du eine interne mibeca-Kollegin als User anlegst, bekommt sie keine Passwort-Mail mehr. Sie wird informiert, dass sie sich mit ihrem Microsoft-Konto anmeldet.
**Warum:** Keine ungenutzten Passwörter mehr, die theoretisch abhandenkommen könnten.

### ✅ Tab bleibt nach Reload erhalten
**Was:** Auch im Admin-Portal bleibt der gerade offene Tab nach einem Reload aktiv.
**Warum:** Spart Klicks.

### ✅ Phasen-Vorlage als Fallback
**Was:** Wenn ein Mandate noch keine gespeicherten Phasen hat (z.B. neu angelegt), zeigt das Dashboard die aktuelle Vorlage. So sind die Spalten „Aktuelle Phase / Nächster Schritt" nie leer.
**Warum:** Du siehst sofort die richtigen Phasen, ohne erst „initialisieren" zu müssen.

---

## Für die Compliance / Datenschutz

### ✅ Doppelter Mass-Assignment-Schutz
**Was:** Selbst wenn jemand technisch versucht, an der API vorbei mb-Nr, Status oder Projekttyp eines Mandats zu ändern, lehnt das Backend das stillschweigend ab. Gilt auch für die KI-Schnittstelle.
**Warum:** Schutz vor Manipulation – die organisationsseitig vergebenen Felder bleiben unverändert.

### ✅ Auto-Verlauf-Logging vom Server
**Was:** Jede Mandanten-Aktion (Kosten bestätigt, Ziele ausgefüllt, Fragebogen abgegeben) wird **serverseitig** im Verlauf der Akte protokolliert.
**Warum:** Vollständige Nachvollziehbarkeit – ein Mandant kann nicht behaupten „habe ich nie gemacht".

### ✅ sessionStorage statt localStorage
**Was:** Aktive Tabs werden in `sessionStorage` (browser-tab-gebunden) gespeichert, nicht in `localStorage` (cross-session). Auth-Tokens ebenso.
**Warum:** Beim Schließen des Browser-Tabs sind alle Spuren weg – wichtig bei gemeinsam genutzten Rechnern.

### ✅ Aktualisierte Security-Konzepte
**Was:** Beide Security-Dokumente (Dashboard + AI) sind auf Stand 2026-05-28 / Version 1.1.
**Warum:** Compliance-Status und alle technischen Schutzmaßnahmen sind aktuell dokumentiert – bereit für DSB-Prüfung.

---

## Was offen ist (siehe Compliance-Vorlagen 1–7)

- ⏳ API-Key-Rotation (optional, nur als Hygiene)
- ⏳ Budget-Limit + Spending-Alerts bei Anthropic setzen (heute, 5 Min)
- ⏳ AVV mit Anthropic anfragen + unterzeichnen
- ⏳ DSFA mit DSB durchführen
- ⏳ Mandanten-Information-Beilage finalisieren
- ⏳ Eintrag im Verarbeitungsverzeichnis ergänzen

Alle Vorlagen liegen in `docs/`. Die Checkliste für den Chef ist `docs/7-Checkliste-Chef.md`.

---

## Was kommt als Nächstes (Pipeline)

Nicht dringend, aber sinnvoll, sobald die ersten echten Mandate getestet sind:

- DD-Anforderungsliste interaktiv im Datenraum-Tab
- Kundeninfo-Vorlagen mit Platzhaltern für Phase 14 (Post-Closing)
- Käufer-Kosten-Tabelle (analog zur Verkäufer-Version)

Erst in der Praxis testen, dann gezielt nachschärfen.

---

*Diese Liste ist eine Zusammenfassung in einfacher Sprache. Die technischen Details
sind in den Security-Konzept-Dokumenten und im Commit-Verlauf des Git-Repositories
dokumentiert.*
