<template>
  <div>
    <!-- Header -->
    <div class="mb-4">
      <h2 class="text-xl font-bold text-gray-900">Unternehmensbewertung</h2>
      <p class="text-sm text-gray-500 mt-1">Beantworte 33 kurze Fragen – wir berechnen automatisch deinen Unternehmenswert.</p>
    </div>

    <!-- Hinweis-Banner: Fragebogen zuerst ausfüllen -->
    <div v-if="autoSuggestionsCount > 0" class="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4 flex items-start gap-3">
      <Lightbulb class="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
      <div class="text-sm text-blue-900">
        <strong>{{ autoSuggestionsCount }} Fragen wurden automatisch ausgefüllt</strong> aus deinen Angaben im Fragebogen.
        Du kannst diese jederzeit anpassen. Bei weiteren Fragen siehst du das <Lightbulb class="w-3.5 h-3.5 inline -mt-0.5" />-Symbol – klick darauf, um den Vorschlag zu übernehmen.
      </div>
    </div>
    <div v-else-if="!fragebogenLoaded" class="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4 flex items-start gap-3">
      <Lightbulb class="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
      <div class="text-sm text-blue-900">
        <strong>Tipp:</strong> Wenn du zuerst den <strong>Fragebogen</strong> ausfüllst, schlagen wir dir hier automatisch viele Antworten vor.
      </div>
    </div>

    <!-- Sticky Live-Score -->
    <div class="bg-gradient-to-br from-[#0088ba] to-[#00a0d8] rounded-xl p-5 mb-4 text-white sticky top-4 z-10 shadow-lg">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div class="text-xs uppercase tracking-wide opacity-80">Deine Bewertung</div>
          <div class="text-3xl font-bold">{{ gesamtProzent }}% <span class="text-base font-normal opacity-90">· {{ einstufung }}</span></div>
        </div>
        <div class="text-right">
          <div class="text-xs uppercase tracking-wide opacity-80">EBIT-Faktor</div>
          <div class="text-3xl font-bold">{{ ebitFaktor.toFixed(1) }}×</div>
        </div>
      </div>
      <div class="w-full bg-white/20 rounded-full h-2 mt-3">
        <div class="bg-white h-2 rounded-full transition-all" :style="`width: ${gesamtProzent}%`"></div>
      </div>
      <div class="flex items-center justify-between text-xs mt-2 opacity-90">
        <span>{{ beantworteteFragen }} von 33 Fragen beantwortet</span>
        <span v-if="adjustedEbit > 0">Geschätzter Wert: <strong>{{ formatTeur(unternehmenswert) }} TEUR</strong></span>
      </div>
    </div>

    <!-- EBIT-Eingabe Karte -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <div class="flex items-center gap-2 mb-3">
        <Calculator class="w-4 h-4 text-[#0088ba]" />
        <h3 class="font-semibold text-gray-800 text-sm">Unternehmenswert-Schätzung</h3>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 items-end">
        <div>
          <label class="text-xs text-gray-600 mb-1 block">Dein bereinigtes EBIT (TEUR)</label>
          <input v-model.number="adjustedEbit" type="number" placeholder="z.B. 250" class="input" />
          <p class="text-xs text-gray-400 mt-1">EBIT nach Bereinigung um Sondereffekte und marktübliches GF-Gehalt</p>
        </div>
        <div v-if="adjustedEbit > 0" class="bg-[#0088ba]/10 rounded-lg p-4">
          <div class="text-xs text-gray-600">Geschätzter Unternehmenswert</div>
          <div class="text-2xl font-bold text-[#0088ba]">{{ formatTeur(unternehmenswert) }} TEUR</div>
          <div class="text-xs text-gray-500 mt-1">{{ adjustedEbit }} × {{ ebitFaktor.toFixed(1) }}× ({{ einstufung }})</div>
        </div>
      </div>
    </div>

    <!-- Filter -->
    <div class="flex items-center gap-2 mb-3">
      <button @click="onlyUnanswered = !onlyUnanswered"
        :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors',
          onlyUnanswered ? 'bg-[#0088ba] text-white border-[#0088ba]' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50']">
        <Filter class="w-3.5 h-3.5" /> Nur unbeantwortete zeigen
      </button>
      <button @click="expandAll" class="text-xs text-gray-500 hover:text-[#0088ba] underline">Alle aufklappen</button>
      <button @click="collapseAll" class="text-xs text-gray-500 hover:text-[#0088ba] underline">Alle zuklappen</button>
    </div>

    <!-- Themenblöcke -->
    <div v-for="(blk, blkIdx) in fragen" :key="blkIdx" class="bg-white rounded-xl border border-gray-100 mb-3 overflow-hidden">
      <button @click="toggleBlock(blkIdx)" class="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
        <div class="flex items-center gap-3 flex-1 min-w-0">
          <div :class="['w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0',
            blockBeantwortet(blkIdx) === 0 ? 'bg-gray-100 text-gray-400' :
            blockProzent(blkIdx) >= 70 ? 'bg-green-100 text-green-700' :
            blockProzent(blkIdx) >= 40 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700']">
            {{ blkIdx + 1 }}
          </div>
          <div class="text-left flex-1 min-w-0">
            <div class="font-semibold text-gray-900 text-sm truncate">{{ blockNamen[blkIdx] }}</div>
            <div class="text-xs text-gray-500 flex items-center gap-2 flex-wrap">
              <span>{{ blockBeantwortet(blkIdx) }} / {{ blk.fragen.length }} beantwortet</span>
              <span v-if="blockBeantwortet(blkIdx) > 0">· Score {{ blockProzent(blkIdx) }}%</span>
              <span v-if="blockOffeneVorschlaege(blkIdx) > 0" class="text-blue-600 flex items-center gap-1">
                <Lightbulb class="w-3 h-3" /> {{ blockOffeneVorschlaege(blkIdx) }} Vorschläge
              </span>
            </div>
          </div>
        </div>
        <ChevronDown :class="['w-5 h-5 text-gray-400 transition-transform flex-shrink-0', openBlocks[blkIdx] ? 'rotate-180' : '']" />
      </button>

      <div v-if="openBlocks[blkIdx]" class="border-t border-gray-100 divide-y divide-gray-50">
        <div v-for="f in visibleFragen(blk)" :key="f.nr" class="p-5">
          <!-- Frage -->
          <div class="flex items-start gap-3 mb-3">
            <span class="font-mono text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-semibold flex-shrink-0">{{ f.nr }}</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-800">{{ f.frage }}</p>
              <p v-if="f.erklaerung" class="text-xs text-gray-500 mt-1 whitespace-pre-line">{{ f.erklaerung }}</p>
            </div>
          </div>

          <!-- Auto-Vorschlag (wenn vorhanden + noch nicht beantwortet oder anders beantwortet) -->
          <div v-if="vorschlag(f.nr) && antworten[f.nr] !== vorschlag(f.nr).note"
            class="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 mb-3">
            <Lightbulb class="w-4 h-4 text-blue-600 flex-shrink-0" />
            <div class="text-xs text-blue-900 flex-1">
              <strong>Vorschlag: Note {{ vorschlag(f.nr).note }}</strong> — {{ vorschlag(f.nr).begruendung }}
            </div>
            <button @click="setAntwort(f.nr, vorschlag(f.nr).note)"
              class="text-xs px-3 py-1 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">
              Übernehmen
            </button>
          </div>

          <!-- 1-5 Buttons -->
          <div class="flex gap-2">
            <button v-for="n in 5" :key="n" @click="setAntwort(f.nr, n)" :disabled="readOnly"
              :class="['flex-1 py-2.5 rounded-lg text-sm font-semibold border-2 transition-all',
                antworten[f.nr] === n
                  ? (n <= 2 ? 'bg-green-500 border-green-500 text-white' : n === 3 ? 'bg-yellow-500 border-yellow-500 text-white' : 'bg-red-500 border-red-500 text-white')
                  : 'border-gray-200 text-gray-500 hover:border-gray-300 bg-white']">
              {{ n }}
            </button>
          </div>
          <div class="flex justify-between text-xs text-gray-400 mt-1.5 px-1">
            <span>sehr gut</span><span>sehr schlecht</span>
          </div>
          <input v-model="notizen[f.nr]" :disabled="readOnly" placeholder="Notiz (optional)" class="input mt-3 text-sm" />
        </div>
        <div v-if="!visibleFragen(blk).length" class="p-5 text-center text-sm text-gray-400">
          Alle Fragen in diesem Block beantwortet.
        </div>
      </div>
    </div>

    <!-- Save Button -->
    <div class="sticky bottom-4 bg-white border border-gray-100 rounded-xl p-3 shadow-lg mt-6 flex items-center gap-3">
      <div class="flex-1 text-sm">
        <div v-if="lastSaved" class="text-xs text-gray-500">Zuletzt gespeichert: {{ lastSavedHuman }}</div>
        <div v-else class="text-xs text-gray-500">Vergiss nicht zu speichern</div>
      </div>
      <button @click="save" :disabled="saving || readOnly" class="px-6 py-2.5 bg-[#0088ba] text-white rounded-xl font-semibold hover:bg-[#00a0d8] disabled:opacity-50 flex items-center gap-2">
        <Save class="w-4 h-4" />
        {{ saving ? 'Speichere…' : 'Bewertung speichern' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ChevronDown, Calculator, Lightbulb, Filter, Save } from '@lucide/vue'
import fragenData from '../../data/bewertungFragen.json'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String, readOnly: { type: Boolean, default: false } })

const fragen = ref(fragenData)
const blockNamen = fragenData.map(b => b.name.replace(/^Themenblock \d+[:\s"]*/i, '').replace(/"/g,'').trim())

const antworten = reactive({})  // { fragenNr: 1-5 }
const notizen = reactive({})
const adjustedEbit = ref(0)
const openBlocks = reactive(fragenData.map(() => false))
const onlyUnanswered = ref(false)
const saving = ref(false)
const lastSaved = ref(null)
const fragebogenData = ref(null)
const fragebogenLoaded = ref(false)

function toggleBlock(idx) { openBlocks[idx] = !openBlocks[idx] }
function expandAll() { fragenData.forEach((_, i) => openBlocks[i] = true) }
function collapseAll() { fragenData.forEach((_, i) => openBlocks[i] = false) }

// --- Auto-Vorschläge aus Fragebogen ---
const vorschlaege = computed(() => {
  const d = fragebogenData.value
  if (!d) return {}
  const out = {}

  // Frage 8: Anzahl Mitarbeiter
  const p = d.personal || {}
  const ma = ['technikVollzeit','technikAzubis','technikAushilfen','vertriebVollzeit','vertriebAzubis','vertriebAushilfen','innendienstVollzeit','innendienstAzubis','innendienstAushilfen']
    .reduce((s, k) => s + (parseInt(p[k]) || 0), 0)
  if (ma > 0) {
    let note = 5, label = `${ma} Mitarbeiter`
    if (ma >= 30) note = 1
    else if (ma >= 16) note = 2
    else if (ma >= 5) note = 3
    else if (ma >= 2) note = 4
    out[8] = { note, begruendung: label }
  }

  // Frage 29: Rechtsform
  const gf = (d.gesellschaftsform || '').toLowerCase()
  if (gf) {
    let note = 3, label = d.gesellschaftsform
    if (gf.includes('holding')) note = 1
    else if (gf.includes('gmbh & co. kg') || gf.includes('gmbh & co.kg') || gf.includes('gmbh&co')) note = 4
    else if (gf.includes('gmbh') || gf.includes('ag')) note = 2
    else if (gf.includes('einzel') || gf.includes('gbr') || gf.includes('kg') || gf.includes('ohg')) note = 5
    out[29] = { note, begruendung: label }
  }

  // Frage 30: Gesellschafter-Anzahl
  const gesellschafter = [d.gesellschafter1, d.gesellschafter2, d.gesellschafter3].filter(g => g && g.trim()).length
  if (gesellschafter > 0) {
    let note = 5, label = `${gesellschafter} Gesellschafter angegeben`
    if (gesellschafter === 1) note = 1
    else if (gesellschafter === 2) note = 2
    else if (gesellschafter === 3) note = 3
    out[30] = { note, begruendung: label }
  }

  // Frage 31: Eigene Immobilie
  if (d.eigeneImmobilie === true) out[31] = { note: 5, begruendung: 'Eigenes Gebäude in der Gesellschaft' }
  else if (d.eigeneImmobilie === false) out[31] = { note: 1, begruendung: 'Normaler Mietvertrag' }

  return out
})

function vorschlag(nr) { return vorschlaege.value[nr] || null }
const autoSuggestionsCount = computed(() => Object.keys(vorschlaege.value).length)

function visibleFragen(blk) {
  if (!onlyUnanswered.value) return blk.fragen
  return blk.fragen.filter(f => !(antworten[f.nr] >= 1 && antworten[f.nr] <= 5))
}

function blockOffeneVorschlaege(idx) {
  return fragen.value[idx].fragen.filter(f => vorschlag(f.nr) && antworten[f.nr] !== vorschlag(f.nr).note).length
}

// --- Berechnungen ---
const beantworteteFragen = computed(() => Object.values(antworten).filter(v => v >= 1 && v <= 5).length)

function blockBeantwortet(idx) {
  return fragen.value[idx].fragen.filter(f => antworten[f.nr] >= 1).length
}

function blockScore(idx) {
  const f = fragen.value[idx].fragen
  const noten = f.map(x => antworten[x.nr]).filter(n => n >= 1)
  if (!noten.length) return 0
  const sum = noten.reduce((s, n) => s + (n - 1), 0)
  return 1 - (sum / (4 * noten.length))
}
function blockProzent(idx) { return Math.round(blockScore(idx) * 100) }

const gesamtScore = computed(() => {
  const scores = fragen.value.map((_, idx) => ({ score: blockScore(idx), n: blockBeantwortet(idx) }))
  const aktive = scores.filter(s => s.n > 0)
  if (!aktive.length) return 0
  return aktive.reduce((s, x) => s + x.score, 0) / aktive.length
})
const gesamtProzent = computed(() => Math.round(gesamtScore.value * 100))

const ebitFaktor = computed(() => {
  if (beantworteteFragen.value === 0) return 5.0
  const p = gesamtProzent.value
  if (p < 40) return 3.0
  if (p < 55) return 4.0
  if (p < 70) return 5.0
  if (p < 85) return 6.0
  return 7.0
})

const einstufung = computed(() => {
  if (beantworteteFragen.value === 0) return 'Noch keine Bewertung'
  const p = gesamtProzent.value
  if (p < 40) return 'Sehr schwach'
  if (p < 55) return 'Schwach'
  if (p < 70) return 'Durchschnitt'
  if (p < 85) return 'Stark'
  return 'Exzellent'
})

const unternehmenswert = computed(() => adjustedEbit.value * ebitFaktor.value)
function formatTeur(v) { return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 }).format(v || 0) }

function setAntwort(nr, n) {
  if (props.readOnly) return
  antworten[nr] = n
}

const lastSavedHuman = computed(() => {
  if (!lastSaved.value) return ''
  const d = new Date(lastSaved.value)
  return d.toLocaleString('de-DE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
})

// --- Persist ---
async function load() {
  if (!props.targetId) { fragebogenLoaded.value = true; return }
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (t.bewertungJson) {
      const b = JSON.parse(t.bewertungJson)
      Object.assign(antworten, b.antworten || {})
      Object.assign(notizen, b.notizen || {})
      adjustedEbit.value = b.adjustedEbit || 0
      lastSaved.value = b.stand
    }
    if (t.fragebogenJson) {
      try {
        fragebogenData.value = JSON.parse(t.fragebogenJson)
        fragebogenLoaded.value = true
      } catch {}
    }
  } catch (e) { console.error(e) }
}
onMounted(load)

async function save() {
  if (!props.targetId) return
  saving.value = true
  try {
    const payload = {
      antworten: { ...antworten },
      notizen: { ...notizen },
      adjustedEbit: adjustedEbit.value,
      gesamtScore: gesamtScore.value,
      gesamtProzent: gesamtProzent.value,
      ebitFaktor: ebitFaktor.value,
      einstufung: einstufung.value,
      unternehmenswert: unternehmenswert.value,
      blockScores: fragen.value.map((_, idx) => ({ name: blockNamen[idx], score: blockScore(idx), prozent: blockProzent(idx) })),
      stand: new Date().toISOString(),
    }
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, bewertungJson: JSON.stringify(payload) } })
    lastSaved.value = payload.stand
  } catch (e) { console.error(e); toast.error('Speichern fehlgeschlagen') }
  finally { saving.value = false }
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
