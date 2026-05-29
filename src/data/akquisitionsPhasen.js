// Akquisitions-Phasen für Käufer-Mandate.
// Jede Akquisition (= konkretes Target, das ein Investor verfolgt) durchläuft diese 11 Phasen.
// Status ist orthogonal (laufend/pausiert/abgesagt/abgeschlossen).

export const AKQ_PHASEN = [
  { id: 1,  key: 'vorgeschlagen',      label: 'Vorgeschlagen',          beschreibung: 'mibeca hat den Kandidaten freigegeben.' },
  { id: 2,  key: 'interesse',          label: 'Interesse bekundet',     beschreibung: 'Käufer signalisiert grundsätzliches Interesse.' },
  { id: 3,  key: 'nda',                label: 'NDA',                    beschreibung: 'Beidseitige Vertraulichkeitsvereinbarung läuft.' },
  { id: 4,  key: 'expose',             label: 'Exposé',                 beschreibung: 'Exposé geteilt; Käufer prüft Details.' },
  { id: 5,  key: 'erstgespraech',      label: 'Erstgespräch',           beschreibung: 'Persönliches Kennenlernen Käufer + Verkäufer.' },
  { id: 6,  key: 'loi',                label: 'Indikatives Angebot / LOI', beschreibung: 'Schriftliche Absichtserklärung.' },
  { id: 7,  key: 'dd',                 label: 'Due Diligence',          beschreibung: 'DD-Anforderungsliste + Datenraum.' },
  { id: 8,  key: 'spa',                label: 'SPA-Verhandlung',        beschreibung: 'Kaufvertragsentwurf wird verhandelt.' },
  { id: 9,  key: 'closing',            label: 'Closing',                beschreibung: 'Notartermin, Unterschriften.' },
  { id: 10, key: 'uebergabe',          label: 'Übergabe',               beschreibung: 'Mitarbeiter-/Kunden-Information, Übergangsphase.' },
  { id: 11, key: 'provision',          label: 'Provision',              beschreibung: 'Abrechnung mibeca.' },
]

export const AKQ_STATUS = [
  { key: 'laufend',      label: 'laufend',      cls: 'bg-green-100 text-green-700' },
  { key: 'pausiert',     label: 'pausiert',     cls: 'bg-amber-100 text-amber-700' },
  { key: 'abgesagt',     label: 'abgesagt',     cls: 'bg-gray-200 text-gray-600' },
  { key: 'abgeschlossen',label: 'abgeschlossen',cls: 'bg-blue-100 text-blue-700' },
]

export const MANDAT_POSITION = [
  { key: 'verkaeufer',  label: 'Verkäufer-Mandat',  hinweis: 'Provision fließt vom Verkäufer (Standardfall).' },
  { key: 'kaeufer',     label: 'Käufer-Mandat',     hinweis: 'Finders-Fee-Vereinbarung mit dem Käufer.' },
  { key: 'beidseitig',  label: 'Beidseitig',        hinweis: 'Selten — beide Seiten zahlen anteilig.' },
]

// Default-Aufgaben, die beim Wechsel in eine Phase automatisch angelegt werden
// (idempotent — Templates haben feste Schlüssel, doppeltes Anlegen wird vermieden).
export const PHASE_DEFAULT_AUFGABEN = {
  1: [
    { key: 'mibeca-pruefen',    titel: 'mibeca prüft Match', verantwortlich: 'mibeca' },
  ],
  2: [
    { key: 'naechste-schritte', titel: 'Nächste Schritte mit Käufer abstimmen', verantwortlich: 'mibeca' },
  ],
  3: [
    { key: 'nda-versenden',     titel: 'NDA versenden',                   verantwortlich: 'mibeca' },
    { key: 'nda-zeichnen',      titel: 'NDA gegenzeichnen',               verantwortlich: 'käufer' },
  ],
  4: [
    { key: 'expose-teilen',     titel: 'Exposé teilen',                   verantwortlich: 'mibeca' },
    { key: 'expose-pruefen',    titel: 'Exposé prüfen + Rückfragen',      verantwortlich: 'käufer' },
  ],
  5: [
    { key: 'termin-finden',     titel: 'Erstgesprächs-Termin finden',     verantwortlich: 'mibeca' },
    { key: 'termin-vorbereiten',titel: 'Erstgespräch vorbereiten',        verantwortlich: 'käufer' },
  ],
  6: [
    { key: 'loi-entwurf',       titel: 'LOI-Entwurf erstellen',           verantwortlich: 'käufer' },
    { key: 'loi-pruefen',       titel: 'LOI prüfen + abstimmen',          verantwortlich: 'mibeca' },
  ],
  7: [
    { key: 'dd-liste',          titel: 'DD-Anforderungsliste senden',     verantwortlich: 'käufer' },
    { key: 'dr-bereitstellen',  titel: 'Datenraum bereitstellen',         verantwortlich: 'mibeca' },
    { key: 'dd-pruefen',        titel: 'DD durchführen',                  verantwortlich: 'käufer' },
  ],
  8: [
    { key: 'spa-entwurf',       titel: 'SPA-Entwurf erstellen',           verantwortlich: 'käufer' },
    { key: 'spa-verhandeln',    titel: 'SPA verhandeln',                  verantwortlich: 'mibeca' },
  ],
  9: [
    { key: 'notartermin',       titel: 'Notartermin vereinbaren',         verantwortlich: 'mibeca' },
    { key: 'unterschrift',      titel: 'Beim Notar unterschreiben',       verantwortlich: 'käufer' },
  ],
  10: [
    { key: 'mitarbeiterinfo',   titel: 'Mitarbeiter informieren',         verantwortlich: 'käufer' },
    { key: 'kundeninfo',        titel: 'Kunden informieren',              verantwortlich: 'käufer' },
    { key: 'aufhebungsvertrag', titel: 'Aufhebungsvertrag GF (falls nötig)', verantwortlich: 'mibeca' },
  ],
  11: [
    { key: 'rechnung',          titel: 'Provisionsrechnung stellen',      verantwortlich: 'mibeca' },
    { key: 'zahlung-pruefen',   titel: 'Zahlungseingang prüfen',          verantwortlich: 'mibeca' },
  ],
}

export function phaseInfo(id) {
  return AKQ_PHASEN.find(p => p.id === id) || AKQ_PHASEN[0]
}

export function statusInfo(key) {
  return AKQ_STATUS.find(s => s.key === key) || AKQ_STATUS[0]
}

// Default-Aufgaben für die angegebene Phase erzeugen. Nur Templates, die noch nicht
// in `vorhandene` (Liste mit `templateKey`) enthalten sind, werden hinzugefügt.
export function defaultAufgabenFuerPhase(phaseId, vorhandene = []) {
  const tpl = PHASE_DEFAULT_AUFGABEN[phaseId] || []
  const existSet = new Set((vorhandene || []).map(a => a.templateKey).filter(Boolean))
  const out = []
  for (const t of tpl) {
    if (existSet.has(`p${phaseId}-${t.key}`)) continue
    out.push({
      id: 'auf' + Date.now() + Math.random().toString(36).slice(2, 6),
      titel: t.titel,
      verantwortlich: t.verantwortlich,
      erledigt: false,
      faellig: '',
      createdAt: new Date().toISOString(),
      templateKey: `p${phaseId}-${t.key}`,
      phaseAngelegtIn: phaseId,
    })
  }
  return out
}
