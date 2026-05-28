# Datenschutz-Folgenabschätzung (DSFA)

**Verarbeitungstätigkeit:** KI-gestützte Dokumenten-Analyse im ITUKV-Dashboard
**Verantwortlich:** mibeca GmbH
**Erstellt am:** 2026-05-28
**Status:** Entwurf – durch DSB zu prüfen und abzuzeichnen
**Rechtsgrundlage DSFA:** Art. 35 DSGVO

---

## 1. Beschreibung der Verarbeitung

### 1.1 Zweck
Auswertung hochgeladener Mandanten-Dokumente (BWA, Jahresabschluss, Exposé,
Handelsregister-Auszug) zur automatischen Extraktion strukturierter Kennzahlen
(Mitarbeiterzahl, Umsatz, EBIT, Rechtsform, Gründungsjahr, Geschäftsführer u. a.).
Die KI dient als Entscheidungsunterstützung für mibeca-Beraterinnen.

### 1.2 Art der verarbeiteten Daten

| Datenkategorie | Beispiele | Sensibilität |
|---|---|---|
| Unternehmens-Stammdaten | Firmenname, Rechtsform, Gründungsjahr | gering |
| Geschäftskennzahlen | Umsatz, EBIT, Mitarbeiterzahl | mittel |
| Personenbezogene Daten | Name + Funktion von Geschäftsführern | mittel |
| Adressen / Kontakt | Sitz, Telefon, E-Mail | mittel |
| Besondere Kategorien Art. 9 | keine | – |

### 1.3 Betroffenenkreise

- Geschäftsführer und Ansprechpartner der Mandanten-Unternehmen
- Geschäftsführer und Ansprechpartner potenzieller Käufer

### 1.4 Empfänger

- intern: mibeca-Beraterinnen
- extern: Anthropic PBC (USA, Auftragsverarbeiter)

### 1.5 Übermittlung in Drittländer
USA. Absicherung über EU-US Data Privacy Framework + ergänzende SCCs.

### 1.6 Speicherdauer

| Ort | Dauer |
|---|---|
| ITUKV Dashboard (Azure, EU) | Lebenszeit des Mandats + 10 Jahre HGB-Frist |
| Anthropic | max. 30 Tage Trust-&-Safety, dann gelöscht |

---

## 2. Notwendigkeit und Verhältnismäßigkeit

### 2.1 Erforderlichkeit

Manuelle Auswertung von Bilanzen, BWAs und Exposés bindet zwischen 30 und 90 Minuten
pro Dokument. Eine KI-gestützte Erst-Extraktion reduziert diese Zeit auf wenige Minuten
und ermöglicht eine zügigere Mandatsbearbeitung. Da bei M&A-Mandaten unter zeitlich
befristeten Bedingungen gearbeitet wird (Letter of Intent, Due-Diligence-Fenster),
ist die Effizienzsteigerung sachgerecht.

### 2.2 Alternativ-Prüfung

| Alternative | Bewertung |
|---|---|
| Manuelle Auswertung | weiterhin als Fallback verfügbar (Opt-Out pro Akte) |
| Lokale Open-Source-KI | aktuell nicht praxistauglich für strukturierte Extraktion |
| Andere Cloud-KI-Anbieter | vergleichbares Risiko, Anthropic gewählt wegen Schutzkonzept |

### 2.3 Mindestdaten-Prinzip

- Es wird ausschließlich das **konkret ausgewählte Dokument** übermittelt, nicht
  die gesamte Akte.
- Keine zusätzlichen personenbezogenen Felder werden über das Dokument hinaus gesendet.
- PDFs > 10 MB werden serverseitig abgewiesen.

---

## 3. Risiko-Bewertung

| Risiko | Eintritts-Wahrscheinlichkeit | Schwere | Restrisiko | Maßnahmen |
|---|---|---|---|---|
| Daten-Leak bei Anthropic | sehr gering | hoch | gering | AVV/SCCs, kurze Aufbewahrung, kein Modell-Training |
| Falsche KI-Ausgabe → falscher Wert in Akte | mittel | mittel | gering | manuelle Übernahme zwingend, pro Feld bestätigbar |
| Unautorisierte interne Nutzung | sehr gering | mittel | sehr gering | nur Admin-Rolle, Audit-Log, Pro-Akte-Opt-In |
| Mandant widerspricht nach Verarbeitung | mittel | gering | gering | Opt-Out + Löschung der KI-Verlauf-Einträge möglich |
| API-Key kompromittiert | gering | mittel | gering | Key nur in Azure App-Settings, sofortige Rotation möglich |
| Übermäßige Kosten | gering | gering | gering | Budget-Limit + Spending-Alert bei Anthropic |
| Drittland-Risiko (USA) | mittel | mittel | gering | DPF + SCCs |

**Gesamt-Risiko: gering bei vollständiger Umsetzung der Maßnahmen.**

---

## 4. Abhilfemaßnahmen

### 4.1 Technische Maßnahmen (umgesetzt)
- Globaler Kill-Switch (`AI_ANALYSE_AKTIV`)
- Pro-Akte-Opt-In durch Admin
- Manuelle Übernahme jedes einzelnen Feldes
- API-Key getrennt von Code (Azure App Settings)
- 2-stufige Mass-Assignment-Allowlist (KI darf keine Stammdaten überschreiben)
- TLS 1.2+ überall, keine ungesicherte Übertragung
- Audit-Log pro KI-Aufruf mit User, Zeit, Dokument, Token-Verbrauch
- Sichtbarer „KI-Analyse"-Marker im Verlauf der Akte
- 10-MB-Limit pro Datei

### 4.2 Organisatorische Maßnahmen (zu erfüllen)
- AVV mit Anthropic unterzeichnen
- Anthropic im Verarbeitungsverzeichnis Art. 30 DSGVO ergänzen
- Mandanten-Information schriftlich an alle Mandanten geben
- Budget-Limit + Spending-Alert in Anthropic Console einrichten
- Schulung „KI-Kompetenz" nach AI-Act Art. 4 dokumentieren

---

## 5. Konsultation der Betroffenen

mibeca informiert betroffene Mandanten schriftlich (Mandatsvertrag oder separate
Beilage; siehe Vorlage „Mandanten-Information") und räumt ein **Widerspruchsrecht
pro Akte** ein.

---

## 6. Konsultation Aufsichtsbehörde

Eine vorherige Konsultation der zuständigen Aufsichtsbehörde nach Art. 36 DSGVO
ist nicht erforderlich, da das Restrisiko nach Umsetzung der Maßnahmen als
**gering** bewertet wird.

---

## 7. Bewertung des Datenschutzbeauftragten

**Bewertung durch DSB:** ______________________________________________________

**Empfehlungen / Auflagen:** __________________________________________________

**Bewertungs-Datum:** ___________________

**Unterschrift DSB:** ___________________

---

## 8. Bewertung durch die Geschäftsführung

**Bewertung:** ________________________________________________________________

**Datum:** ___________________

**Unterschrift Geschäftsführung:** ___________________

---

## 9. Überprüfung

- Erste Überprüfung: 12 Monate nach Inbetriebnahme
- Anlassbezogen: bei Änderungen am Verfahren oder am AVV mit Anthropic
- Mindestens alle 24 Monate

---

*Hinweis: Diese DSFA-Vorlage ist eine Arbeitsgrundlage. Die finale Bewertung obliegt
dem Datenschutzbeauftragten der mibeca GmbH.*
