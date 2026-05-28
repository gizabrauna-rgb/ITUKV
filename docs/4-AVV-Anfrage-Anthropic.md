# AVV-Anfrage an Anthropic

**Zweck:** Den Auftragsverarbeitungs-Vertrag (Data Processing Addendum, DPA) mit Anthropic
abschließen, bevor produktiv personenbezogene Daten verarbeitet werden.
**Stand:** 2026-05-28

---

## Option 1: Online-Self-Service (empfohlen, schnellster Weg)

Anthropic bietet sein DPA inzwischen über ein Self-Service-Formular an. Schritte:

1. **Login** unter https://console.anthropic.com mit dem mibeca-Konto.
2. Im linken Menü auf **„Organization"** klicken (oder direkt
   https://console.anthropic.com/settings/organization).
3. Im Tab **„Legal"** oder **„Compliance"** den Punkt „Data Processing Addendum"
   suchen.
4. Auf **„Sign DPA"** klicken. Es öffnet sich ein DocuSign- oder Online-Vertrags-Editor.
5. Die für mibeca relevanten Felder ausfüllen:
   - **Customer Legal Entity Name:** `mibeca GmbH`
   - **Customer Address:** vollständige Anschrift
   - **Authorized Signatory:** Name + Position der Geschäftsführung
   - **E-Mail of Signatory:** mibeca-Mailadresse für Vertragskopie
6. Unterzeichnen und signierte Kopie als PDF ablegen.
7. Im Verarbeitungsverzeichnis Art. 30 DSGVO ergänzen (siehe Vorlage 3).

Falls das Self-Service-Formular nicht erscheint, weiter mit Option 2.

---

## Option 2: Anfrage per E-Mail

**Empfänger:** legal@anthropic.com (mit Kopie an support@anthropic.com)
**Betreff:** Request for Data Processing Addendum (DPA) – mibeca GmbH

### E-Mail-Text (Englisch, kann 1:1 verwendet werden)

```
Hello Anthropic Legal Team,

We are mibeca GmbH, a German consulting company using the Anthropic API
(Claude) within our internal SaaS platform "ITUKV Dashboard". The platform
analyzes business documents (financial statements, BWAs, exposes) uploaded
by our clients in order to extract structured key figures.

To comply with the European General Data Protection Regulation (GDPR),
we require:

1. A signed Data Processing Addendum (DPA) according to Article 28 GDPR
2. The current Standard Contractual Clauses (SCCs) as an annex to the DPA
   for the transfer of personal data to the United States
3. A copy of your current Trust Center information / TOM documentation
4. Confirmation that our API data is not used for model training
5. Information on your current data retention period (default 30 days) and
   the option to opt into a Zero Retention Mode

Please send the documents to the following contact:

Name:       [Name einfügen]
Position:   [Position]
Company:    mibeca GmbH
Address:    [Anschrift]
Email:      [E-Mail]

Our Anthropic account email is: [mibeca-Account-Mail einfügen]
Our Workspace / Organization ID is: [aus Anthropic Console kopieren]

Thank you very much. We look forward to your reply.

Kind regards
[Name]
mibeca GmbH
```

### Was du nach dem Senden erwartest

- Antwortzeit: meist 3–5 Werktage
- Du erhältst entweder einen direkten DPA-Link zum Online-Signing oder
  eine PDF-Vorlage zum Ausfüllen + Rücksenden
- Anthropic verlangt keine Anwaltskosten oder Setup-Fees für das DPA
- SCCs sind standardmäßig als Annex enthalten (Modul 2: Verantwortlicher → Auftragsverarbeiter)

---

## Option 3: Zero-Retention-Mode mitbestellen

Wenn ihr besonders sensible Mandate habt (z. B. mit personenbezogenen Daten im Exposé)
und nicht möchtet, dass Anthropic die Anfrage 30 Tage speichert, könnt ihr den
**Zero-Retention-Mode** mit Anthropic vereinbaren. Voraussetzungen:

- Enterprise-Plan oder Enterprise-Add-on
- Begründung der Notwendigkeit (z. B. „M&A advisory data with personally identifiable
  information of company executives")
- Anfrage an enterprise@anthropic.com

Bei aktueller Nutzungsmenge eher nicht notwendig, aber gut zu wissen für später.

---

## Checkliste

- [ ] DPA über Console oder per Mail angefragt
- [ ] DPA unterzeichnet und PDF-Kopie abgelegt unter `docs/legal/`
- [ ] SCCs-Anlage liegt vor
- [ ] Verarbeitungsverzeichnis aktualisiert (Vorlage 3)
- [ ] AI-Security-Konzept §1a auf „erfolgt" gesetzt
