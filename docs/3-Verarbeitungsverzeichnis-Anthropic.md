# Eintrag im Verarbeitungsverzeichnis (Art. 30 DSGVO)

**Verfahren:** KI-gestützte Dokumenten-Analyse (ITUKV Dashboard)
**Status:** Vorlage zum Übernehmen ins zentrale Art-30-Verzeichnis der mibeca GmbH
**Stand:** 2026-05-28

---

## Stammdaten

| Feld | Angabe |
|---|---|
| Bezeichnung der Verarbeitung | KI-gestützte Auswertung hochgeladener Mandanten-Dokumente |
| Erfasst seit | 2026-05-28 |
| Verantwortlicher | mibeca GmbH, [Anschrift einfügen] |
| Vertreter falls extern | – |
| Datenschutzbeauftragter | [Name + Kontakt einfügen] |
| Auftragsverarbeiter | Anthropic PBC, 548 Market St #94234, San Francisco, CA 94104, USA |

## Zweck der Verarbeitung

Auswertung hochgeladener Mandanten-Dokumente (BWA, Jahresabschluss, Exposé, Handels-
register-Auszug) zur Extraktion strukturierter Geschäftskennzahlen (Mitarbeiter,
Umsatz, EBIT, Gründungsjahr, Rechtsform, Geschäftsführer u. a.) als Entscheidungs-
unterstützung für mibeca-Beraterinnen.

## Rechtsgrundlage

- Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung – Mandatsbearbeitung)
- Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an effizienter Bearbeitung)

## Datenkategorien

- Unternehmens-Stammdaten (Firma, Sitz, Rechtsform, Gründungsjahr)
- Geschäftskennzahlen (Umsatz, EBIT, Mitarbeiter, Recurring-Anteil)
- Personenbezogene Daten von Geschäftsführern und Ansprechpartnern
  (Name, Funktion, ggf. E-Mail/Telefon, soweit im Dokument enthalten)
- **Keine besonderen Kategorien nach Art. 9 DSGVO**

## Kategorien von Betroffenen

- Geschäftsführer und gesetzliche Vertreter der mandantierenden Verkäufer-Unternehmen
- Geschäftsführer und gesetzliche Vertreter potenzieller Käufer
- in den Dokumenten ggf. genannte Ansprechpartner

## Kategorien von Empfängern

- intern: mibeca-Beraterinnen (Admin-Rolle im ITUKV Dashboard)
- extern: Anthropic PBC (USA, Auftragsverarbeiter)

## Übermittlung in Drittländer

| Drittland | Empfänger | Absicherung |
|---|---|---|
| USA | Anthropic PBC | EU-US Data Privacy Framework + EU-Standardvertragsklauseln (SCCs) als AVV-Anlage |

## Löschfristen

| Speicherort | Dauer |
|---|---|
| ITUKV Dashboard (Azure Westeurope) | Mandatslebenszeit + 10 Jahre (HGB / AO) |
| Anthropic-Server (USA) | max. 30 Tage Trust-&-Safety, dann automatische Löschung |
| Audit-Log | 24 Monate |

## Technische und organisatorische Maßnahmen (TOM)

Siehe „AI-Security-Konzept" der mibeca GmbH. Zusammenfassung:

- Globaler Kill-Switch im Backend
- Pro-Akte-Opt-In durch Admin
- Manuelle Übernahme der KI-Vorschläge zwingend
- TLS 1.2+ auf allen Übertragungswegen
- API-Key in Azure App-Settings (nicht im Code)
- 2-stufige Mass-Assignment-Allowlist
- Audit-Log mit User, Zeit, Dokument, Token-Verbrauch
- 10-MB-Limit pro Dokument

## Verfahrensbeschreibung (Kurz)

1. Admin lädt Mandanten-Dokument in Datenraum
2. Admin klickt „KI-Analyse" auf dem Dokument
3. Backend prüft Berechtigung + Pro-Akte-Opt-In
4. Dokument wird verschlüsselt (TLS) an Anthropic übertragen
5. Anthropic liefert strukturiertes JSON zurück
6. Admin prüft Vorschläge im Modal und übernimmt manuell pro Feld
7. Backend schreibt nur freigegebene Felder + erzeugt Audit-Log + Verlauf-Eintrag

## Sicherheits-Bewertung

- DSFA durchgeführt: [Datum einfügen]
- Risiko-Bewertung: gering (siehe DSFA-Dokument)
- Notwendigkeits-Bewertung: erforderlich für effiziente Mandatsbearbeitung

---

*Letzte Aktualisierung dieses Eintrags: 2026-05-28*
