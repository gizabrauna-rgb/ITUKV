<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Exposé</h3>
        <p class="text-xs text-gray-500">Anonymisiertes Kurzexposé für die Marktansprache</p>
      </div>
      <div class="flex gap-2">
        <button @click="generieren" :disabled="!hasFragebogen" class="flex items-center gap-2 px-3 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf] disabled:opacity-50" :title="!hasFragebogen ? 'Erst Fragebogen ausfüllen' : ''">
          <Wand2 class="w-4 h-4" /> Aus Fragebogen generieren
        </button>
        <button @click="downloadText" :disabled="!exposeText" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50 disabled:opacity-50">
          <Download class="w-4 h-4" /> Text-Datei
        </button>
        <button @click="printPdf" :disabled="!exposeText" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50 disabled:opacity-50">
          <Printer class="w-4 h-4" /> PDF drucken
        </button>
      </div>
    </div>

    <!-- Status / Freigabe-Workflow -->
    <div class="bg-white rounded-xl border border-gray-100 p-4 mb-4">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-3">
          <div :class="['w-3 h-3 rounded-full', statusColor]"></div>
          <span class="font-medium text-sm">Status: {{ statusLabel }}</span>
        </div>
        <div class="flex gap-2">
          <button v-if="exposeStatus !== 'in_review'" @click="setStatus('in_review')" class="text-xs px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50">Zur Review (Jenny)</button>
          <button v-if="exposeStatus !== 'awaiting_approval'" @click="setStatus('awaiting_approval')" class="text-xs px-3 py-1.5 border border-amber-200 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100">An Kunde zur Freigabe</button>
          <button v-if="exposeStatus !== 'approved'" @click="setStatus('approved')" class="text-xs px-3 py-1.5 border border-green-200 bg-green-50 text-green-700 rounded-lg hover:bg-green-100">Freigegeben</button>
        </div>
      </div>
      <p class="text-xs text-gray-500">{{ statusHinweis }}</p>
    </div>

    <!-- Empty State -->
    <div v-if="!exposeText && !generating" class="bg-white rounded-xl border border-gray-100 p-10 text-center">
      <FileText class="w-12 h-12 mx-auto mb-3 text-gray-200" />
      <h4 class="font-semibold text-gray-700 mb-1">Noch kein Exposé erstellt</h4>
      <p class="text-sm text-gray-500 mb-4">
        {{ hasFragebogen ? 'Klicke auf "Aus Fragebogen generieren" um ein Kurzexposé aus den Fragebogen-Daten zu erstellen.'
                       : 'Der Kunde muss erst den Fragebogen ausfüllen, damit das Exposé automatisch generiert werden kann.' }}
      </p>
    </div>

    <div v-else-if="generating" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400">
      <Loader2 class="w-8 h-8 mx-auto mb-2 animate-spin text-[#097e92]" />
      Generiere Exposé aus Fragebogen-Daten…
    </div>

    <!-- Editor -->
    <div v-else>
      <textarea
        v-model="exposeText"
        @blur="save"
        rows="35"
        class="w-full px-5 py-4 bg-white border border-gray-200 rounded-xl text-sm leading-relaxed font-mono focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92] whitespace-pre-wrap"
      ></textarea>
      <p class="text-xs text-gray-400 mt-2">Auto-Speichern beim Verlassen des Feldes. Bearbeitungen von Jenny werden gespeichert und gehen dann zum Kunden zur Freigabe.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Wand2, Download, Printer, FileText, Loader2 } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String })

const target = ref(null)
const fragebogen = ref({})
const exposeText = ref('')
const exposeStatus = ref('draft')
const generating = ref(false)

const hasFragebogen = computed(() => target.value?.fragebogenJson)

const statusLabel = computed(() => ({
  draft: 'Entwurf', in_review: 'In Review (Jenny)',
  awaiting_approval: 'Beim Kunden zur Freigabe', approved: 'Freigegeben'
})[exposeStatus.value] || 'Entwurf')

const statusColor = computed(() => ({
  draft: 'bg-gray-400', in_review: 'bg-blue-500',
  awaiting_approval: 'bg-amber-500', approved: 'bg-green-500'
})[exposeStatus.value] || 'bg-gray-400')

const statusHinweis = computed(() => ({
  draft: 'Exposé wird gerade erstellt oder bearbeitet.',
  in_review: 'Jenny prüft das Exposé und macht ggf. Anpassungen.',
  awaiting_approval: 'Der Kunde sieht das Exposé in seinem Portal und kann es freigeben oder Korrekturwünsche äußern.',
  approved: 'Exposé ist freigegeben — die Ausschreibung kann starten!'
})[exposeStatus.value] || '')

onMounted(async () => {
  if (!props.targetId) return
  try {
    target.value = await authFetch(`/targets/${props.targetId}`)
    exposeText.value = target.value.exposeText || ''
    exposeStatus.value = target.value.exposeStatus || 'draft'
    if (target.value.fragebogenJson) {
      try { fragebogen.value = JSON.parse(target.value.fragebogenJson) } catch { fragebogen.value = {} }
    }
  } catch (e) { console.error(e) }
})

function anonPlz(plz) {
  if (!plz) return 'PLZ XX...'
  const s = String(plz).trim()
  if (s.length >= 2) return 'PLZ ' + s.substring(0, 2) + '...'
  return 'PLZ XX...'
}

function generieren() {
  generating.value = true
  setTimeout(() => {
    exposeText.value = generateExpose()
    save()
    generating.value = false
  }, 600)
}

function generateExpose() {
  const t = target.value || {}
  const f = fragebogen.value || {}
  const mbNr = t.mbNr || 'mb-XXX'
  const branche = t.branche || 'IT-Systemhaus'
  const region = anonPlz(t.plz || f.plzOrt?.match(/\d{5}/)?.[0])
  const gj = f.gruendungsjahr || '19XX'
  const heute = new Date().toLocaleDateString('de-DE')

  // Mitarbeiter zusammenfassen
  const personal = f.personal || {}
  const techMA = +(personal.technikVollzeit || 0)
  const vertriebMA = +(personal.vertriebVollzeit || 0)
  const innenMA = +(personal.innendienstVollzeit || 0)
  const totalMA = techMA + vertriebMA + innenMA + (+f.anzahlGf || 0)

  // Zeitaufteilung GF1
  const z = f.zeitGf?.[1] || {}
  const zeitText = ['technik','vertrieb','innendienst','geschaeftsfuehrung']
    .map(k => z[k] ? `${k.charAt(0).toUpperCase()+k.slice(1)} ${z[k]} %` : null)
    .filter(Boolean).join(', ')

  // Lösungs-Schwerpunkte (Top 3 nach Skala 1-10)
  const loesungen = f.loesungen || {}
  const topLoesungen = Object.entries(loesungen)
    .filter(([k,v]) => v >= 7)
    .sort((a,b) => b[1] - a[1])
    .slice(0, 4)
    .map(([k]) => k)

  // Verkaufsgründe (Top 3)
  const gruende = f.verkaufsgruende || {}
  const topGruende = Object.entries(gruende)
    .filter(([k,v]) => v >= 7)
    .sort((a,b) => b[1] - a[1])
    .slice(0, 3)
    .map(([k]) => k)

  // Wartungsumsatz letztes Jahr
  const wartung = f.wartungUmsatz || {}
  const letztesJahr = Math.max(...Object.keys(wartung).map(Number).filter(n => !isNaN(n)), 0)
  const wartungLetzt = letztesJahr && wartung[letztesJahr] ? `ca. ${wartung[letztesJahr]} €` : '—'

  return `UNTERNEHMENSEXPOSÉ
Projektnummer: ${mbNr}
Stand: ${heute}

────────────────────────────────────────────

${branche.toUpperCase()} BIETET ÜBERNAHME GEGEN GEBOT

Das hier vorgestellte Unternehmen ist ein etablierter ${branche} mit Sitz im ${region}.
Auf den folgenden Seiten finden Sie eine anonymisierte Kurzbeschreibung. Bei Interesse
unterzeichnen Sie bitte zunächst eine Vertraulichkeitsvereinbarung (NDA, siehe letzte Seite).

────────────────────────────────────────────

1. UNTERNEHMEN UND HISTORIE

Das Unternehmen wurde im Jahr ${gj} als ${f.gesellschaftsform || '[Gesellschaftsform]'} gegründet.
${f.gesellschaftsform === 'GmbH' ? `Das Stammkapital beträgt ${f.stammkapital || '[XX.XXX]'} €.` : ''}
${f.eigeneImmobilie ? 'Das Unternehmen verfügt über eine eigene, selbst genutzte Immobilie.' : ''}
${f.besitzgesellschaft ? 'Im Hintergrund existiert eine Besitz-/Verwaltungsgesellschaft.' : ''}

2. GESCHÄFTSFELDER UND GESCHÄFTSMODELL

${topLoesungen.length ? 'Die Leistungsschwerpunkte (gewichtet nach Bedeutung) sind:\n' + topLoesungen.map((l,i) => `  ${i+1}. ${l}`).join('\n') : 'Die genauen Leistungsschwerpunkte werden im Detail-Gespräch erläutert.'}

3. KUNDEN UND KUNDENSTRUKTUR

Aktive Geschäftskunden: ${f.aktiveGeschaeftskunden || '[Anzahl]'}
${f.privatkundenAnteil ? 'Anteil Privatkunden: ' + f.privatkundenAnteil + ' %' : ''}
${f.branchenschwerpunkte ? 'Branchenschwerpunkte: ' + f.branchenschwerpunkte : ''}
${f.typischeArbeitsplaetze ? 'Typische Unternehmensgröße der Kunden: ' + f.typischeArbeitsplaetze : ''}
${f.kundenRegionen ? 'Hauptregion: ' + f.kundenRegionen : ''}

4. UMSÄTZE, ERTRÄGE, FINANZIELLE SITUATION

Wiederkehrende Umsätze durch Service- und Wartungsverträge im Jahr ${letztesJahr || '[Jahr]'}: ${wartungLetzt}

(Detaillierte Finanzzahlen — Umsatz, EBIT, bereinigtes EBIT — werden nach NDA-Unterzeichnung zur Verfügung gestellt.)

5. MITARBEITER

Gesamt: ${totalMA || '[Anzahl]'} Mitarbeitende
${techMA ? `· Technik: ${techMA} Vollzeit` : ''}
${vertriebMA ? `· Vertrieb: ${vertriebMA} Vollzeit` : ''}
${innenMA ? `· Innendienst/Verwaltung: ${innenMA} Vollzeit` : ''}
${f.anzahlGf ? `· Geschäftsführung: ${f.anzahlGf}` : ''}

6. MANAGEMENT

${zeitText ? 'Zeitaufteilung des Hauptgeschäftsführers: ' + zeitText : 'Aktive Geschäftsführung mit klar geregelten Verantwortlichkeiten.'}

7. WACHSTUMSPOTENZIAL

${f.wachstumspotenzial || '[Wachstumspotenzial wird in Detailgespräch erläutert]'}

8. WETTBEWERBSSITUATION

${f.wettbewerbssituation || '[Wettbewerbssituation wird in Detailgespräch erläutert]'}

9. FIRMENSITZ

Der Firmensitz liegt im Bereich ${region}.

10. TRANSAKTIONSVORHABEN UND VERKAUFSMOTIV

${topGruende.length ? 'Hauptgründe für den geplanten Verkauf:\n' + topGruende.map((g,i) => `  ${i+1}. ${g}`).join('\n') : 'Die Motivation für den Verkauf wird im persönlichen Gespräch erläutert.'}

${f.verbleibImUnternehmen ? `Der Inhaber ist bereit, im Unternehmen zu verbleiben (Details: ${f.verbleibDetails || 'nach Absprache'}).` : ''}
${f.uebergabeVerfuegbarkeit ? 'Verfügbarkeit zur Übergabe: ' + f.uebergabeVerfuegbarkeit : ''}

11. CHANCEN UND PERSPEKTIVEN FÜR DEN INVESTOR

Solide Bestandskundenbasis mit wiederkehrenden Umsätzen, etabliertes Geschäftsmodell, geeignet für Buy-and-Build-Strategie oder strategische Erweiterung.

12. VERTRAULICHKEIT

Strenge Vertraulichkeit wird erwartet. Bitte unterzeichnen Sie die NDA, bevor weitere Informationen weitergegeben werden.

────────────────────────────────────────────

KONTAKT FÜR INTERESSENTEN

mibeca GmbH · M&A-Beratung für IT-Unternehmen
Mike Bergmann · Geschäftsführer
Hambrocker Str. 47 · 29525 Uelzen
www.itukv.de · info@mail.itukv.de

────────────────────────────────────────────`
}

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch(`/targets/${props.targetId}`, {
        method: 'PATCH',
        data: { exposeText: exposeText.value, exposeStatus: exposeStatus.value }
      })
    } catch (e) { console.error(e) }
  }, 500)
}

function setStatus(s) {
  exposeStatus.value = s
  save()
}

function downloadText() {
  const blob = new Blob([exposeText.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url
  a.download = `Expose_${target.value?.mbNr || 'mandat'}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

function printPdf() {
  const win = window.open('', '_blank')
  if (!win) return
  win.document.write(`<html><head><title>Exposé ${target.value?.mbNr}</title><style>
    body{font-family:Georgia,serif;max-width:720px;margin:40px auto;padding:0 20px;line-height:1.6;color:#161e2a;font-size:14px}
    pre{white-space:pre-wrap;font-family:inherit}
  </style></head><body><pre>${exposeText.value.replaceAll('<','&lt;')}</pre><script>window.print()</scr` + `ipt></body></html>`)
  win.document.close()
}
</script>
