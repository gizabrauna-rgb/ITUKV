# Checkliste für die Geschäftsführung

**Adressat:** Mike Bergmann (mibeca-GF)
**Zweck:** Alle Aktionen, die explizit der Chef persönlich erledigen muss, damit das
ITUKV-Dashboard mit aktiver KI-Funktion vollständig DSGVO- und AI-Act-konform läuft.
**Vorbereitung durch:** Anna Giza-Braun (technisch) + DSB (rechtlich)
**Stand:** 2026-05-28

---

## Gesamt-Aufwand: ca. 30 Minuten

| Aktion | Aufwand | Frist |
|---|---|---|
| 2× digital signieren (AVV + DSFA) | 10 Min | innerhalb 2 Wochen |
| 1× DSB instruieren | 5 Min | diese Woche |
| 1× Mandanten-Info-Beilage freigeben | 5 Min | innerhalb 2 Wochen |
| 1× Budget freigeben | 1 Min | heute |
| Unternehmensdaten an Anna geben | 5 Min | sobald gefragt |

---

## 1. AVV mit Anthropic unterzeichnen ✍️

**Hintergrund:** Anthropic verarbeitet im Auftrag der mibeca personenbezogene Daten
(Inhalte von Mandanten-Dokumenten). Die DSGVO Art. 28 schreibt einen
Auftragsverarbeitungsvertrag (AVV) vor.

**Was zu tun ist:**
- [ ] Mail von Anthropic Legal abwarten (Anna fragt das DPA an)
- [ ] DocuSign-Link öffnen, Vertrag prüfen
- [ ] Digital signieren
- [ ] PDF-Kopie an Anna zur Ablage in `docs/legal/`

**Aufwand:** 5 Min

---

## 2. DSFA freigeben 📋

**Hintergrund:** Die Datenschutz-Folgenabschätzung dokumentiert die Risiko-Bewertung
der KI-Verarbeitung. Pflicht nach Art. 35 DSGVO.

**Was zu tun ist:**
- [ ] DSFA-Dokument vom DSB erhalten (Anna + DSB bereiten vor)
- [ ] Abschnitt 8 (Bewertung Geschäftsführung) lesen
- [ ] Unterschrift unter Abschnitt 8 setzen
- [ ] Dokument an Anna zur Ablage in `docs/legal/`

**Aufwand:** 15 Min Lesen + Unterschrift

---

## 3. Mandanten-Information als Beilage zum Mandatsvertrag 📝

**Hintergrund:** Mandanten müssen nach Art. 13 DSGVO darüber informiert werden, dass
KI-Tools (Anthropic) zur Dokumenten-Auswertung eingesetzt werden. Hierfür reicht
eine **separate Info-Beilage** (kein Anwalt nötig, kein Vertragsbestandteil).

**Was zu tun ist:**
- [ ] Beilage-Vorlage von Anna durchlesen (1 Seite)
- [ ] OK geben oder kleinere Anpassungen rückmelden
- [ ] Beilage wird ab dann jedem neuen Mandanten beim Onboarding mitgegeben
- [ ] Bestehende Mandanten erhalten die Info per Mail als Nachtrag

**Aufwand:** 5 Min

---

## 4. Datenschutzbeauftragter (DSB) 🛡️

**Status prüfen:**
- [ ] Ist ein DSB bestellt? Wenn ja: Name + Mail an Anna
- [ ] Wenn nein: DSB benennen (intern oder extern, z. B. Datenschutz-Kanzlei)

**Wenn DSB bestellt ist:**
- [ ] DSB instruieren: „Bitte DSFA + Verarbeitungsverzeichnis-Eintrag von Anna prüfen
      und abzeichnen."
- [ ] Kontakt zwischen Anna und DSB herstellen

**Aufwand:** 5 Min Mail oder Telefonat

---

## 5. Budget für Anthropic freigeben 💳

**Hintergrund:** Damit ein Bug oder Missbrauch nicht zu unkontrollierten Kosten führt,
setzen wir ein Hard-Limit in der Anthropic Console.

**Was zu tun ist:**
- [ ] Anna's Empfehlung bestätigen: **50 USD/Monat** (ca. 45 EUR)
- [ ] Anna setzt das Limit + Alerts in der Anthropic Console
- [ ] Bei Bedarf später anpassen

**Aufwand:** 1 Min

---

## 6. Unternehmensdaten für Verträge bereitstellen 🏢

Anna braucht für die Verträge folgende Angaben (1× zentral hinterlegen):

- [ ] Vollständige Geschäftsanschrift (Straße, PLZ, Ort)
- [ ] Handelsregister-Nummer + Amtsgericht
- [ ] Name + Position des Unterzeichners (vermutlich der Geschäftsführer)
- [ ] mibeca-Mailadresse für Vertragskopien
- [ ] Anthropic-Account-Mailadresse + Organization-ID
  (oben rechts in https://console.anthropic.com auf den Workspace-Namen klicken)

**Aufwand:** 5 Min Sammeln + an Anna mailen

---

## Was der Chef NICHT tun muss

- Technische Einrichtung (Anna übernimmt)
- Anthropic-Console-Aktionen (Anna)
- Verarbeitungsverzeichnis-Pflege (DSB / Anna)
- Schulung der Mitarbeiter (Anna + Jenny intern)
- Audit-Log-Review (Anna)

---

## Termin-Vorschlag

**Variante 1: alles in einem 30-Minuten-Slot**
Anna setzt einen Termin auf, hat alle Dokumente vorbereitet, Chef arbeitet alle
6 Punkte in einem Rutsch ab.

**Variante 2: über die Woche verteilt**
Anna schickt jeden Punkt einzeln per Mail mit klarer Handlungsaufforderung.

---

## Erfolgsmessung

Wenn alle 6 Punkte erledigt sind:

- ✅ AI-Security-Konzept §1a (Compliance-Tabelle) komplett auf grün
- ✅ KI-Funktion läuft formal vollständig abgesichert
- ✅ Bereit für externe Audits (Datenschutzbehörde, Kunden-Due-Diligence)
