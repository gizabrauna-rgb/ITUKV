// Master-Prozess-Phasen-Vorlagen (Jennys 13-Schritte-Prozess)
// Shared zwischen PhasenProzess.vue (Admin) und TargetDashboard.vue (Mandant)

export const PHASEN_VORLAGE = () => ([
  { id: 1, titel: '1. UVE Start — Vorbereitungs-Checkliste', notiz: '', aufgaben: [
    { id: 'uve1', label: 'MB050: Videolektionen ansehen ("Wie läuft Verkauf von A bis Z ab?")', done: false, verantwortlich: 'Kunde', datum: '', notiz: '' },
    { id: 'uve2', label: 'MB050: Fragebogen Unternehmensbewertung ausgefüllt', done: false, verantwortlich: 'Kunde', datum: '', notiz: '', auto: 'fragebogenAbgegeben' },
    { id: 'uve3a', label: 'MB050: Datenraum-Vorlage einrichten (Ordnerstruktur nach Muster)', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 'uve3b', label: 'MB050: Unterlagen in den Datenraum hochladen (Bilanzen, Verträge, Personal …)', done: false, verantwortlich: 'Kunde', datum: '', notiz: '', auto: 'datenraumHatDokumente' },
    { id: 'uve4', label: 'Ziele & Motivationen erfassen (Wunsch-Exit, Rolle nach Verkauf, Deal-Struktur)', done: false, verantwortlich: 'Kunde', datum: '', notiz: '', auto: 'zieleErfasst' },
    { id: 'uve5', label: 'Unternehmensexposé freigeben (von mibeca erstellt)', done: false, verantwortlich: 'Kunde', datum: '', notiz: '', auto: 'exposeApproved' },
    { id: 'uve6', label: 'Verkaufsmandat erteilen → Marktansprache durch mibeca', done: false, verantwortlich: 'Kunde', datum: '', notiz: '' },
    { id: 'uve7', label: 'Kosten-Tabelle ansehen ("Welche Kosten kommen auf Dich zu")', done: false, verantwortlich: 'Kunde', datum: '', notiz: '', auto: 'kostenZurKenntnis' },
    { id: 't1', label: 'Zahlen, Daten, Fakten zusammentragen', done: false, verantwortlich: 'Kunde', datum: '', notiz: '', auto: 'stammdatenZdfVorhanden' },
    { id: 't2', label: 'Unternehmensbewertung erstellen', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'bewertungVorhanden' },
    { id: 't3', label: 'Exposé-Entwurf erstellen', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'exposeEntwurfVorhanden' },
  ]},
  { id: 2, titel: '2. UVE Abschluss — Verkaufsmandat-Eröffnung', notiz: '', aufgaben: [
    { id: 't1', label: 'Verkaufsmandat unterzeichnen (12 Monate)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '', auto: 'mandatGegengezeichnet' },
    { id: 't2', label: 'Standard-Ordner anlegen: ITUKV/UVE/mb-XX', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 't3', label: 'Onboarding-Termin mit Jenny wahrnehmen', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 't4', label: 'Kundenakte angelegt', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'kundenakteAngelegt' },
  ]},
  { id: 3, titel: '3. Marktansprache — Interessenten anschreiben', notiz: '', aufgaben: [
    { id: 't1', label: 'Landing-Page online (targets.itukv.de/mb-XX)', done: false, verantwortlich: 'Marketing', datum: '', notiz: '', auto: 'landingPublished' },
    { id: 't2', label: 'Erstinteressenten aus Kundenstamm filtern (PLZ-Radius)', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'interessentenAngelegt' },
    { id: 't3', label: 'Anschreiben über zahlreiche Kanäle (Mail/Brief/Telefon)', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'anschreibenVerschickt' },
    { id: 't4', label: 'KEINE Exklusivität zugesagt!', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
  { id: 4, titel: '4. NDA von Interessenten abholen', notiz: '', aufgaben: [
    { id: 't1', label: 'Mindestens 1 NDA erhalten', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'ndaErhalten' },
    { id: 't2', label: 'VETO-Check: Interessenten freigeben oder ablehnen', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 't3', label: 'Signierte NDAs in Akte ablegen', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'ndaInDatenraum' },
  ]},
  { id: 5, titel: '5. Erstes Kennenlernen — Interessent ↔ Verkäufer', notiz: '', aufgaben: [
    { id: 't1', label: 'Termin koordinieren (3er-Gespräch)', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'kennenlernenGeplant' },
    { id: 't2', label: 'Am Kennenlerngespräch teilnehmen', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '', auto: 'kennenlernenErfolgt' },
    { id: 't3', label: 'Eindruck dokumentieren', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
  { id: 6, titel: '6. Datenraum / Kommunikationsraum in Element', notiz: '', aufgaben: [
    { id: 't1', label: 'Element-Raum eröffnet', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 't2', label: 'Beteiligte eingeladen', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 't3', label: 'Zugang verifiziert', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
  { id: 7, titel: '7. Austausch von Unterlagen', notiz: '', aufgaben: [
    { id: 't1', label: 'Erweiterte Unterlagen für Interessenten freigeben', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 't2', label: 'Rückfragen der Interessenten beantworten', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
  ]},
  { id: 8, titel: '8. Indikatives Angebot', notiz: '', aufgaben: [
    { id: 't1', label: 'Erstes Gebot eingegangen', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 't2', label: 'Angebot bewerten (mit Jenny)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 't3', label: 'Rückmeldung an Käufer', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
  { id: 9, titel: '9. Verhandlungen', notiz: '', aufgaben: [
    { id: 't1', label: 'Preis verhandeln', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 't2', label: 'Struktur (Share Deal / Asset Deal) festlegen', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 't3', label: 'Bedingungen klären (Earn-Out, GF-Verbleib)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
  ]},
  { id: 10, titel: '10. Letter of Intent (LOI)', notiz: '', aufgaben: [
    { id: 't1', label: 'LOI-Entwurf erstellen', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'loiGestartet' },
    { id: 't2', label: 'LOI verhandeln + final unterzeichnen', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '', auto: 'loiFinal' },
  ]},
  { id: 11, titel: '11. Due Diligence', notiz: '', aufgaben: [
    { id: 'ddprep', label: 'Datenraum vollständig befüllen', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '', auto: 'datenraumGefuellt' },
    { id: 'dda', label: 'A. Allgemeines: Ansprechpartner geklärt (Veräußerer + Erwerber)', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 'ddb', label: 'B. Rechtliche DD: Gesellschaftsunterlagen, Verträge, Arbeitsrecht (~58 Items)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
    { id: 'ddc', label: 'C. Steuerliche DD: Veranlagung, Betriebsprüfungen, Verlustvorträge (~35 Items)', done: false, verantwortlich: 'Steuerberater', datum: '', notiz: '' },
    { id: 'ddd', label: 'D. Financial DD: Jahresabschlüsse, BWAs, Budgets (~95 Items)', done: false, verantwortlich: 'Steuerberater', datum: '', notiz: '' },
    { id: 'dde', label: 'E. Business DD: Markt, Wettbewerber, Vertrieb, Personal (~14 Items)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 'ddf', label: 'F. Technologische DD: IT-Architektur, Security, F&E (~16 Items)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 'ddend', label: 'DD-Bericht / Fragen-Antworten dokumentiert', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
  { id: 12, titel: '12. Vertragsgestaltung', notiz: '', aufgaben: [
    { id: 't1', label: 'Deal-Struktur entscheiden: Share Deal (SPA) vs. Asset Deal', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 't2', label: 'Kaufvertrag Entwurf (Vorlage: SPA-Master oder Asset-Deal-Vertrag)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
    { id: 't3', label: 'GF-Anstellungsvertrag (falls GF im Unternehmen verbleibt)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
    { id: 't4', label: 'Gesellschaftsvertrag anpassen (falls neue Gesellschafter)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
    { id: 't5', label: 'Vertragsverhandlungen — Garantien, Earn-Out, Klauseln', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 't6', label: 'Finale Version abstimmen', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
  ]},
  { id: 13, titel: '13. Notartermin & Closing', notiz: '', aufgaben: [
    { id: 't1', label: 'Notartermin koordiniert', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'notarGeplant' },
    { id: 't2', label: 'Unterzeichnung beim Notar', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '', auto: 'notarErfolgt' },
    { id: 't3', label: 'Kaufpreis erhalten', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 't4', label: 'Anteilsübertragung vollzogen', done: false, verantwortlich: 'Notar', datum: '', notiz: '' },
  ]},
  { id: 14, titel: '14. Post-Closing — Übergabe & Kommunikation', notiz: '', aufgaben: [
    { id: 'pc1', label: 'Übergabe-Plan erstellen (Begleitung 3-12 Monate)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 'pc2', label: 'Mitarbeiter informieren', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 'pc3', label: 'Kunden-Information: "Unternehmen wurde verkauft" (Vorlage nutzen)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 'pc4', label: 'Vertragsübergabe-Information an Kunden (Vorlage nutzen)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 'pc5', label: 'Earn-Out-Phase tracken (falls vereinbart)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 'pc6', label: 'Aufhebungsvertrag GF (falls GF ausscheidet)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
  ]},
  { id: 15, titel: '15. Erfolgsmeldung & Abrechnung', notiz: '', aufgaben: [
    { id: 'pr1', label: 'Pressemitteilung erstellt (Vorlage: DATAreform x Knoblauch)', done: false, verantwortlich: 'Marketing', datum: '', notiz: '', auto: 'pressetextErstellt' },
    { id: 'pr2', label: 'Pressetext freigeben', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '', auto: 'pressetextFreigegeben' },
    { id: 'pr3', label: 'Erfolgsmeldung an Branche/Newsletter', done: false, verantwortlich: 'Marketing', datum: '', notiz: '', auto: 'presseVersand' },
    { id: 'pr4', label: 'LinkedIn-Post (anonymisiert oder mit Zustimmung)', done: false, verantwortlich: 'Marketing', datum: '', notiz: '' },
    { id: 'pr5', label: 'Erfolgshonorar berechnet & in Rechnung gestellt', done: false, verantwortlich: 'Claudia', datum: '', notiz: '' },
    { id: 'pr6', label: 'Zeiterfassung final abgerechnet', done: false, verantwortlich: 'Claudia', datum: '', notiz: '' },
    { id: 'pr7', label: 'Mandat in Ordnerstruktur archiviert', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
])

export const PHASEN_KAUF = () => ([
  { id: 1, titel: '1. Suchprofil definieren', notiz: '', aufgaben: [
    { id: 'k1', label: 'Suchkriterien erarbeiten (Region, Branche, Größe)', done: false, verantwortlich: 'Käufer', datum: '', notiz: '' },
    { id: 'k2', label: 'Suchprofil im Dashboard freigeben', done: false, verantwortlich: 'Käufer', datum: '', notiz: '', auto: 'suchprofilFreigegeben' },
    { id: 'k3', label: 'Budget-Rahmen + Strategische Ziele dokumentieren', done: false, verantwortlich: 'Käufer', datum: '', notiz: '', auto: 'akquisitionsstrategieErfasst' },
  ]},
  { id: 2, titel: '2. Markt-Screening (mibeca)', notiz: '', aufgaben: [
    { id: 'k1', label: 'Kandidaten-Suche im eigenen CRM', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 'k2', label: 'Externe Quellen ausgewertet (LinkedIn, Branchenverbände)', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 'k3', label: 'In-House-Matching mit unseren Verkaufs-Targets', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
  { id: 3, titel: '3. Long-List erstellt', notiz: '', aufgaben: [
    { id: 'k1', label: 'Mindestens 1 Kandidat in der Long-List', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'longListHatEintraege' },
    { id: 'k2', label: 'Long-List dem Käufer präsentiert', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
  { id: 4, titel: '4. Short-List / Käufer-Auswahl', notiz: '', aufgaben: [
    { id: 'k1', label: 'Feedback zu Kandidaten geben (Interesse / Rückfrage / Kein Interesse)', done: false, verantwortlich: 'Käufer', datum: '', notiz: '', auto: 'kaeuferFeedbackVorhanden' },
    { id: 'k2', label: 'Top-Kandidaten festlegen', done: false, verantwortlich: 'Käufer', datum: '', notiz: '' },
  ]},
  { id: 5, titel: '5. Anonyme Ansprache', notiz: '', aufgaben: [
    { id: 'k1', label: 'Erstkontakt zu Top-Kandidaten (anonym)', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 'k2', label: 'Interesse abfragen + erste Gespräche', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
  { id: 6, titel: '6. NDA-Austausch', notiz: '', aufgaben: [
    { id: 'k1', label: 'NDA mit interessiertem Kandidat unterzeichnen', done: false, verantwortlich: 'Käufer', datum: '', notiz: '' },
    { id: 'k2', label: 'Anonymität aufgelöst', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
  ]},
  { id: 7, titel: '7. Erstes Kennenlernen', notiz: '', aufgaben: [
    { id: 'k1', label: 'Termin zwischen Käufer und Verkäufer-Kandidat', done: false, verantwortlich: 'Jenny', datum: '', notiz: '', auto: 'kennenlernenGeplant' },
    { id: 'k2', label: 'Am Kennenlerngespräch teilnehmen + Bewertung', done: false, verantwortlich: 'Käufer', datum: '', notiz: '', auto: 'kennenlernenErfolgt' },
  ]},
  { id: 8, titel: '8. LOI / Indikatives Angebot', notiz: '', aufgaben: [
    { id: 'k1', label: 'LOI mit Verkäufer-Kandidat verhandeln', done: false, verantwortlich: 'Käufer', datum: '', notiz: '', auto: 'loiGestartet' },
    { id: 'k2', label: 'LOI final unterzeichnen', done: false, verantwortlich: 'Käufer', datum: '', notiz: '', auto: 'loiFinal' },
  ]},
  { id: 9, titel: '9. Due Diligence', notiz: '', aufgaben: [
    { id: 'k1', label: 'DD-Datenraum-Zugang vom Verkäufer erhalten', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 'k2', label: 'Rechtliche DD durchführen', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
    { id: 'k3', label: 'Financial DD durchführen', done: false, verantwortlich: 'Steuerberater', datum: '', notiz: '' },
    { id: 'k4', label: 'Business/Technologische DD durchführen', done: false, verantwortlich: 'Käufer', datum: '', notiz: '' },
    { id: 'k5', label: 'DD-Bericht erstellen + Risiken identifizieren', done: false, verantwortlich: 'Käufer', datum: '', notiz: '' },
  ]},
  { id: 10, titel: '10. Vertrag & Closing', notiz: '', aufgaben: [
    { id: 'k1', label: 'Kaufvertrag (SPA/Asset Deal) verhandeln', done: false, verantwortlich: 'Käufer', datum: '', notiz: '' },
    { id: 'k2', label: 'Mandatsvertrag mit mibeca unterzeichnen', done: false, verantwortlich: 'Käufer', datum: '', notiz: '', auto: 'mandatGegengezeichnet' },
    { id: 'k3', label: 'Notartermin und Closing', done: false, verantwortlich: 'Notar', datum: '', notiz: '', auto: 'notarErfolgt' },
    { id: 'k4', label: 'Erfolgshonorar abgerechnet', done: false, verantwortlich: 'Claudia', datum: '', notiz: '' },
  ]},
])

export function getPhasenVorlage(projekttyp) {
  return /kauf|investor/i.test(projekttyp || '') ? PHASEN_KAUF() : PHASEN_VORLAGE()
}
