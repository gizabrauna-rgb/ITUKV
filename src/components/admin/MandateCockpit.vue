<template>
  <div>
    <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Mandate-Cockpit – wo steht jeder Kunde?</h2>
        <p class="text-sm text-gray-500 mt-0.5">Alle aktiven Mandate, aktueller Schritt und nächste Aktion für dich auf einen Blick.</p>
      </div>
      <div class="flex gap-2 items-center text-xs">
        <label class="flex items-center gap-1.5 cursor-pointer">
          <input type="checkbox" v-model="nurMitNeuigkeit" />
          <span>nur mit Neuigkeit (letzte 7 Tage)</span>
        </label>
        <select v-model="filterTyp" class="border border-gray-200 rounded-lg px-2 py-1">
          <option value="">Alle Typen</option>
          <option value="verkauf">Verkäufer</option>
          <option value="kauf">Käufer</option>
        </select>
        <select v-model="sortBy" class="border border-gray-200 rounded-lg px-2 py-1">
          <option value="neu">Sortiert: Neueste Aktivität zuerst</option>
          <option value="alt">Sortiert: Lange nichts passiert</option>
          <option value="phase">Sortiert: Phasen-Fortschritt</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400">Lade Mandate…</div>
    <div v-else-if="!visibleRows.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400">Keine Mandate gefunden.</div>
    <div v-else class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Mandat</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Typ</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Aktuelle Phase</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Was hat der Mandant zuletzt getan?</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Nächster Schritt für dich</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="r in visibleRows" :key="r.targetId" @click="$emit('open-akte', r.targetId)"
            class="hover:bg-gray-50 cursor-pointer">
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <span class="font-mono text-xs bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded">{{ r.mbNr || '—' }}</span>
                <span class="font-medium text-sm text-gray-800 truncate max-w-[180px]">{{ r.firma || '—' }}</span>
                <span v-if="r.neuSeitTage !== null && r.neuSeitTage <= 3" class="bg-green-100 text-green-700 text-[10px] font-bold px-1.5 py-0.5 rounded-full">NEU</span>
              </div>
            </td>
            <td class="px-4 py-3">
              <span :class="['text-xs px-2 py-0.5 rounded-full font-medium',
                             r.istKauf ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700']">
                {{ r.istKauf ? 'Käufer' : 'Verkäufer' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <div class="text-sm text-gray-800 truncate max-w-[220px]">{{ r.phaseLabel }}</div>
              <div class="text-[11px] text-gray-400">Phase {{ r.phaseIdx }} von {{ r.phasenTotal }}</div>
              <div class="w-32 bg-gray-100 rounded-full h-1 mt-1.5">
                <div class="bg-[#0088ba] h-1 rounded-full" :style="`width: ${r.phasenTotal ? (r.phaseIdx/r.phasenTotal)*100 : 0}%`"></div>
              </div>
            </td>
            <td class="px-4 py-3 text-xs max-w-[260px]">
              <div v-if="r.letzteAktivitaet" class="text-gray-700 truncate">{{ r.letzteAktivitaet }}</div>
              <div v-else class="text-gray-400 italic">noch nichts</div>
              <div v-if="r.letzteAktivitaetDatum" class="text-[10px] text-gray-400 mt-0.5">{{ formatRel(r.letzteAktivitaetDatum) }}</div>
            </td>
            <td class="px-4 py-3 text-xs max-w-[300px]">
              <div v-if="r.naechsterSchritt" :class="['p-2 rounded-lg border', r.naechsterSchrittDringend ? 'bg-amber-50 border-amber-200' : 'bg-gray-50 border-gray-100']">
                <div class="text-gray-800">{{ r.naechsterSchritt }}</div>
                <div v-if="r.naechsterSchrittVerantwortlich" class="text-[10px] text-gray-500 mt-0.5">
                  Verantwortlich: <strong>{{ r.naechsterSchrittVerantwortlich }}</strong>
                </div>
              </div>
              <div v-else class="text-gray-400 italic">—</div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { authFetch } from '../../api.js'

const emit = defineEmits(['open-akte'])

const targets = ref([])
const loading = ref(true)
const filterTyp = ref('')
const sortBy = ref('neu')
const nurMitNeuigkeit = ref(false)

const MIBECA_VERANTWORTLICH = ['jenny', 'mibeca', 'marketing', 'claudia', 'admin', 'anwalt', 'steuerberater', 'notar']
function istMibecaAufgabe(v) {
  if (!v) return false
  return MIBECA_VERANTWORTLICH.includes(v.toLowerCase())
}
function istMandantAufgabe(v) {
  if (!v) return false
  const x = v.toLowerCase()
  return x === 'kunde' || x === 'käufer' || x === 'kaeufer' || x === 'verkäufer' || x === 'verkaeufer'
}

async function load() {
  loading.value = true
  try {
    const all = await authFetch('/targets', { method: 'GET' })
    targets.value = (all || []).filter(t => {
      const s = (t.status || '').toLowerCase()
      return s !== 'abgebrochen' && s !== 'verkauft'
    })
  } finally { loading.value = false }
}
onMounted(load)

const rows = computed(() => {
  return targets.value.map(t => {
    const istKauf = /kauf|investor/i.test(t.projekttyp || '')
    let phasen = []
    try { phasen = JSON.parse(t.phasenJson || '[]') } catch {}

    let phaseIdx = 1
    for (let i = 0; i < phasen.length; i++) {
      const offen = (phasen[i].aufgaben || []).some(a => !a.done)
      if (offen) { phaseIdx = i + 1; break }
      phaseIdx = i + 1
    }
    const phaseObj = phasen[phaseIdx - 1] || null
    const phaseLabel = phaseObj ? (phaseObj.titel || '').replace(/^\d+\.\s*/, '') : '—'

    let verlauf = []
    try { verlauf = JSON.parse(t.kommunikationJson || '[]') } catch {}
    let letzteAktivitaet = ''
    let letzteAktivitaetDatum = null

    function maybeUpdate(label, datum) {
      if (!datum) return
      const d = new Date(datum)
      if (isNaN(d.getTime())) return
      if (!letzteAktivitaetDatum || d > letzteAktivitaetDatum) {
        letzteAktivitaet = label
        letzteAktivitaetDatum = d
      }
    }
    if (t.kostenInfoBestaetigtAm) maybeUpdate('Kosten zur Kenntnis genommen', t.kostenInfoBestaetigtAm)
    if (t.fragebogenAbgegebenAm) maybeUpdate('Fragebogen abgegeben', t.fragebogenAbgegebenAm)
    if (t.zieleMotivationenJson && t.zieleMotivationenJson !== '{}' && !letzteAktivitaet) {
      letzteAktivitaet = 'Ziele & Motivationen ausgefüllt'
    }
    if (t.akquisitionsstrategieJson && t.akquisitionsstrategieJson !== '{}' && !letzteAktivitaet) {
      letzteAktivitaet = 'Akquisitionsstrategie ausgefüllt'
    }
    const mandantEntries = verlauf.filter(e => !e.createdByMibeca && !e.createdByKI).sort((a,b) => (b.datum||'').localeCompare(a.datum||''))
    if (mandantEntries.length) {
      const e = mandantEntries[0]
      maybeUpdate(e.betreff || (e.beschreibung || '').slice(0, 60) || 'Nachricht', e.datum)
    }
    const neuSeitTage = letzteAktivitaetDatum
      ? Math.floor((Date.now() - letzteAktivitaetDatum.getTime()) / 86400000)
      : null

    let naechsterSchritt = ''
    let naechsterSchrittVerantwortlich = ''
    let naechsterSchrittDringend = false
    if (phaseObj) {
      const offen = (phaseObj.aufgaben || []).filter(a => !a.done)
      const mibecaTask = offen.find(a => istMibecaAufgabe(a.verantwortlich))
      const wartetAufMandant = offen.find(a => istMandantAufgabe(a.verantwortlich))
      if (mibecaTask) {
        naechsterSchritt = (mibecaTask.label || '').replace(/^MB\d+:\s*/, '')
        naechsterSchrittVerantwortlich = mibecaTask.verantwortlich
        naechsterSchrittDringend = true
      } else if (wartetAufMandant) {
        naechsterSchritt = 'Warte auf Mandant: ' + (wartetAufMandant.label || '').replace(/^MB\d+:\s*/, '')
        naechsterSchrittVerantwortlich = wartetAufMandant.verantwortlich
      } else if (offen.length) {
        naechsterSchritt = (offen[0].label || '').replace(/^MB\d+:\s*/, '')
        naechsterSchrittVerantwortlich = offen[0].verantwortlich || '—'
      }
    }

    return {
      targetId: t.RowKey,
      mbNr: t.mbNr,
      firma: t.firma || t.verkaueferName,
      istKauf,
      phaseLabel, phaseIdx, phasenTotal: phasen.length,
      letzteAktivitaet, letzteAktivitaetDatum,
      neuSeitTage,
      naechsterSchritt, naechsterSchrittVerantwortlich, naechsterSchrittDringend,
    }
  })
})

const visibleRows = computed(() => {
  let r = rows.value
  if (filterTyp.value === 'verkauf') r = r.filter(x => !x.istKauf)
  if (filterTyp.value === 'kauf') r = r.filter(x => x.istKauf)
  if (nurMitNeuigkeit.value) r = r.filter(x => x.neuSeitTage !== null && x.neuSeitTage <= 7)
  if (sortBy.value === 'neu') {
    r = [...r].sort((a, b) => (b.letzteAktivitaetDatum?.getTime() || 0) - (a.letzteAktivitaetDatum?.getTime() || 0))
  } else if (sortBy.value === 'alt') {
    r = [...r].sort((a, b) => (a.letzteAktivitaetDatum?.getTime() || Infinity) - (b.letzteAktivitaetDatum?.getTime() || Infinity))
  } else if (sortBy.value === 'phase') {
    r = [...r].sort((a, b) => b.phaseIdx - a.phaseIdx)
  }
  return r
})

function formatRel(d) {
  if (!d) return ''
  const ms = Date.now() - d.getTime()
  const min = Math.floor(ms / 60000)
  if (min < 1) return 'gerade eben'
  if (min < 60) return `vor ${min} Min`
  const h = Math.floor(min / 60)
  if (h < 24) return `vor ${h} Std`
  const tage = Math.floor(h / 24)
  if (tage === 1) return 'gestern'
  if (tage < 7) return `vor ${tage} Tagen`
  return d.toLocaleDateString('de-DE')
}
</script>
