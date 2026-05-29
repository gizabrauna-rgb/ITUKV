# Rollen im ITUKV-Dashboard

**Stand:** 2026-05-29
**Zielgruppe:** Alle – um zu verstehen, wer was darf und sieht.

---

## Auf einen Blick

| Rolle | Wer ist das? | Sieht | Darf |
|---|---|---|---|
| **Admin** | mibeca-Mitarbeitende (Anna, Jenny) | ALLE Mandate, alle Daten | Alles – inkl. Mandate anlegen, User anlegen, KI-Analyse, Verträge |
| **Verkäufer** | Mandant, der sein Unternehmen verkauft | Nur das eigene Verkaufs-Mandate | Eigene Daten pflegen, Aufgaben abhaken, Verträge unterschreiben |
| **Käufer (Investor)** | Mandant, der ein Unternehmen kaufen möchte | Nur das eigene Kauf-Mandate | Suchprofil, Kandidaten-Feedback, NDA & Kaufvertrag unterschreiben |
| **KI-Service-Account** | technischer Account für Jennys KI-Coworker | Stammdaten + Verlauf | Datenanreicherung in eng begrenzten Feldern |

Plus außerhalb des Dashboards beteiligte Personen (Anwalt, Steuerberater, Notar, DSB) – siehe ganz unten.

---

## Rolle 1: Admin (mibeca-Berater)

### Wer das ist
Alle mibeca-Mitarbeitenden, die operativ mit Mandaten arbeiten. Aktuell:
- **Anna Giza-Braun** (System-Admin, Technik + Compliance)
- **Jennifer „Jenny" Kaplan** (Operativ – M&A-Beratung)

### Was Admin sieht
**Alles.** Sämtliche Mandate (Verkäufer + Käufer), alle Kontakte, das gesamte CRM,
alle Dokumente, Audit-Logs, Controlling, Backups.

### Was Admin darf
- **Mandate anlegen, bearbeiten, löschen** (Verkäufer-Mandate + Käufer-Mandate)
- **Phasen-Prozess** pro Mandate führen + Aufgaben abhaken
- **KI-Analyse** auf hochgeladenen Dokumenten starten
- **Verträge erstellen, gegenzeichnen, an Mandanten zur Unterschrift senden**
- **User anlegen + Rollen vergeben** (Verkäufer, Käufer, weitere Admins)
- **Audit-Log einsehen** (wer hat wann was geändert)
- **Backups manuell triggern + zurückspielen**
- **CRM-Kontakte importieren, bearbeiten, löschen**
- **Veröffentlichte Landing-Pages** für anonyme Ausschreibungen erstellen
- **Beirats-Bericht** als PDF generieren
- **Compliance-Schalter** umlegen (z. B. KI ein/aus)

### Was Admin NICHT darf
- **Passwörter anderer User direkt einsehen** – nur ein neues setzen
- **Audit-Log manipulieren** (es ist unveränderlich)
- **Datenschutzpflichten umgehen** (z. B. unbegrenzt Daten speichern)

### Login
Mit dem **Microsoft-Konto** der mibeca (Single Sign-On über Microsoft Entra ID).
Kein separates Passwort.

---

## Rolle 2: Verkäufer (Mandant)

### Wer das ist
Geschäftsführer / Inhaber eines Unternehmens, das mibeca verkaufen soll. Hat einen
Mandatsvertrag mit mibeca unterzeichnet.

### Was Verkäufer sieht
**Nur das eigene Mandate.** Kein Einblick in andere Mandate, keine anderen Kontakte,
kein Controlling, kein Audit-Log.

Konkret sieht der Verkäufer in seinem persönlichen Portal:
- **Mein Projekt** – aktuelle Phase + persönliche Aufgaben
- **Meine Daten** – persönliche Kontaktdaten + Vorgangsnummern (read-only)
- **Fragebogen** – Unternehmensbewertung beantworten
- **Bewertung** – das Ergebnis seiner Unternehmensbewertung
- **Verträge** – NDA + Mandatsvertrag online unterzeichnen
- **Mein Exposé** – das von mibeca erstellte Exposé prüfen + freigeben
- **Interessenten** – wer hat sich beworben, NDA-Status, VETO setzen
- **Dokumente** – Datenraum mit eigenen Unterlagen
- **Verlauf** – kompletter Kommunikationsverlauf zu seinem Mandate

### Was Verkäufer darf
- **Eigene Daten pflegen** (Name, Mail, Telefon, Branche, MA, Umsatz, …)
- **Fragebogen + Ziele & Motivationen ausfüllen**
- **Eigene Dokumente in den Datenraum hochladen**
- **Exposé freigeben** oder Korrektur anfordern
- **NDA + Mandatsvertrag online unterzeichnen**
- **VETO gegen einzelne Interessenten setzen**
- **Im Verlauf kommunizieren** (Nachrichten, Termin-Bestätigungen)

### Was Verkäufer NICHT darf
- **Mb-Nummer / Transaktionsnummer / Kundennummer ändern** (von mibeca vergeben)
- **Status seines Mandates ändern** (z. B. „verkauft" setzen)
- **Daten anderer Mandanten einsehen**
- **mibeca-interne Dokumente einsehen** (z. B. interne Bewertungen, Audit-Log)
- **Mandatsvertrag löschen** (rechtlich nicht zulässig während Laufzeit)

### Login
**E-Mail + Passwort.** Zugangsdaten kommen einmalig per Mail von Anna oder Jenny.
Passwort sollte beim ersten Login geändert werden.

---

## Rolle 3: Käufer (Investor)

### Wer das ist
Jemand, der ein Unternehmen kaufen möchte und mibeca beauftragt hat, ein passendes
Ziel zu finden. Hat einen Kauf-Mandate-Vertrag mit mibeca.

### Was Käufer sieht
**Nur das eigene Kauf-Mandate.** Die Tabs ähneln der Verkäufer-Ansicht, aber inhaltlich
auf die Käufer-Perspektive zugeschnitten:
- **Mein Projekt** – aktuelle Phase + persönliche Aufgaben
- **Meine Daten** – persönliche + Vorgangsnummern
- **Mein Suchprofil** – Kriterien (Branche, Region, Größe, Preis)
- **Target-Vorschläge** – konkrete Kandidaten mit Feedback-Möglichkeit
- **Verträge** – NDAs mit potenziellen Verkäufern + Mandatsvertrag mit mibeca
- **Dokumente** – Bewertungs-Material, DD-Berichte
- **Verlauf** – Kommunikation

### Was Käufer darf
- **Suchprofil ausfüllen + freigeben**
- **Akquisitionsstrategie & Ziele** dokumentieren
- **Pro Kandidat Feedback geben** („Interesse" / „Rückfrage" / „Kein Interesse")
- **NDAs unterzeichnen**
- **LOI verhandeln** + final unterzeichnen
- **Eigene DD-Unterlagen hochladen**

### Was Käufer NICHT darf
- **Verkäufer-Daten anderer Mandate einsehen** (auch nicht die Kandidaten anderer Käufer)
- **Anonymität von Kandidaten umgehen** (vor NDA werden Namen nicht angezeigt)
- **mibeca-interne Bewertungen einsehen**

### Login
**E-Mail + Passwort.** Wie beim Verkäufer.

---

## Rolle 4: KI-Service-Account (technisch)

### Wer das ist
Ein **technischer User**, kein Mensch. Wird für Jennys KI-Coworker benutzt, der
Kontakte automatisch aus externen Quellen anreichert (z. B. Northdata-Daten,
Web-Recherche).

### Was der Account sieht
- Stammdaten von Kontakten und Mandaten (lesend)
- Verlauf-Einträge (lesend)

### Was der Account darf
- **Eine eng begrenzte Liste von Feldern beschreiben** (Bulk-Update von Stammdaten)
- **Verlauf-Einträge anhängen** (z. B. „KI hat folgendes recherchiert")

### Was der Account NICHT darf
- **Mandate-Stammdaten manipulieren** (mb-Nr, Status, Projekttyp)
- **Verträge erstellen oder ändern**
- **Andere User anlegen oder verändern**
- **Audit-Log einsehen**

### Sicherheits-Hintergrund
Doppelter Schutz: zusätzlich zur Schreib-Allowlist gibt es eine Admin-only-Sperre,
die selbst der KI den Zugriff auf organisationsseitig vergebene Felder verweigert.
Jeder KI-Schreibvorgang landet im Audit-Log.

### Login
**E-Mail + Passwort** (technische Mailadresse). Wird im Backend per JWT mit Rolle
`ai-agent` autorisiert.

---

## Wer vergibt die Rollen?

- **Admin-Rolle:** wird von einem bestehenden Admin (Anna) vergeben
- **Verkäufer-Rolle:** vergibt Anna oder Jenny beim Anlegen eines neuen Mandanten,
  verknüpft mit einem konkreten Mandate (mb-Nummer)
- **Käufer-Rolle:** wie Verkäufer-Rolle, aber mit Kauf-Mandate verknüpft
- **KI-Service-Account:** wird einmal eingerichtet, danach nicht mehr verändert

Im Hintergrund läuft eine **dreistufige Auswahl** beim Anlegen eines neuen Users:
1. Rolle wählen (Admin / Verkäufer / Käufer)
2. Falls Verkäufer oder Käufer: das passende Mandate aus der Liste auswählen
3. Speichern → System verschickt automatisch eine Willkommens-Mail
   (mit Microsoft-Hinweis bei internen, mit Passwort bei externen Usern)

---

## Personen außerhalb des Dashboards

Im M&A-Prozess sind weitere Beteiligte involviert, die **keinen eigenen Account**
im Dashboard haben:

| Person / Rolle | Wofür zuständig | Kommt ins Dashboard rein? |
|---|---|---|
| **Anwalt** | Kaufvertrag, GF-Anstellungsvertrag, rechtliche DD | Nein – arbeitet im Hintergrund, kriegt Dokumente per Mail |
| **Steuerberater** | Steuerliche + Financial Due Diligence | Nein – kriegt Datenraum-Zugang per separatem Link |
| **Notar** | Beurkundung des Kaufvertrags | Nein – externer Termin |
| **Datenschutzbeauftragter (DSB)** | Prüfung der Datenverarbeitung | Optional Lese-Zugriff als Admin, sonst per Bericht |
| **Bürgschaftsbank** | Finanzierung beim Käufer | Nein |
| **Marketing-Dienstleister** | Landing-Pages, Pressetexte | Nein – Vorlagen werden von mibeca übernommen |
| **Käufer-Interessent (vor NDA)** | sieht nur das öffentliche Exposé | Nur über Token-Link, kein Login |
| **Käufer-Interessent (nach NDA)** | bekommt detailliertes Exposé + Datenraum-Einblick | Über persönlichen Token-Link, kein Login-Konto |

Diese Personen werden über **Verlauf-Einträge + Mail-Vorlagen** im Dashboard mitgepflegt,
aber sie loggen sich nicht selbst ein.

---

## Wichtig zum Schluss

- **Jede Rolle sieht nur, was sie sehen soll.** Die Daten-Trennung ist serverseitig
  technisch erzwungen (IDOR-Schutz). Kein „aus Versehen anderer Daten sehen".
- **Jede Aktion wird protokolliert.** Wer hat wann was geändert? Steht im Audit-Log.
- **Rollen können nachträglich geändert werden.** Anna kann z. B. einen Verkäufer
  zum Admin machen (in Ausnahmefällen) oder umgekehrt.
- **Bei Personalwechsel:** alten User löschen, neuen anlegen. Alle Mandate bleiben
  erhalten – nur der Zugriff wechselt.

---

## Wer hilft bei Fragen?

| Frage | An wen |
|---|---|
| „Ich kann mich nicht einloggen." | Anna |
| „Ich sehe nicht, was ich sehen sollte." | Anna |
| „Mein Mandat zeigt falsche Phase / Daten." | Jenny |
| „Wer hat Zugriff auf welche Daten?" | siehe dieses Dokument |
| „Wie kommt jemand neues ins Dashboard?" | Anna legt neuen User an |
| „Wie wird ein User entfernt?" | Anna löscht den User |
