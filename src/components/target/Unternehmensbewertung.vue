<template>
  <div>
    <div class="mb-5">
      <h2 class="text-xl font-bold text-gray-900">Unternehmensbewertung</h2>
      <p class="text-sm text-gray-500 mt-1">
        Bitte beantworte alle 33 Fragen auf einer Skala von <strong>1 (sehr gut)</strong> bis <strong>5 (sehr schlecht)</strong>.
        Du bekommst sofort eine erste Einschätzung deines Unternehmenswertes.
      </p>
    </div>

    <!-- Live-Score Karte oben -->
    <div class="bg-gradient-to-br from-[#097e92] to-[#0a9aaf] rounded-xl p-5 mb-5 text-white">
      <div class="flex items-start justify-between mb-3">
        <div>
          <div class="text-xs uppercase tracking-wide opacity-80 mb-1">Aktuelle Bewertung</div>
          <div class="text-3xl font-bold">{{ gesamtProzent }}%</div>
          <div class="text-sm opacity-90">{{ einstufung }} · EBIT-Faktor {{ ebitFaktor.toFixed(1) }}×</div>
        </div>
        <div class="text-right">
          <div class="text-xs uppercase tracking-wide opacity-80 mb-1">Beantwortet</div>
          <div class="text-2xl font-bold">{{ beantworteteFragen }} / 33</div>
        </div>
      </div>
      <div class="w-full bg-white/20 rounded-full h-2 mb-3">
        <div class="bg-white h-2 rounded-full transition-all" :style="`width: ${gesamtProzent}%`"></div>
      </div>
      <!-- Block-Scores -->
      <div class="grid grid-cols-5 gap-2 text-xs">
        <div v-for="(blk, idx) in fragen" :key="idx" class="text-center">
          <div class="opacity-80 truncate">TB {{ idx + 1 }}</div>
          <div class="font-bold">{{ blockProzent(idx) }}%</div>
        </div>
      </div>
    </div>

    <!-- EBIT-Eingabe & Unternehmenswert -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-5">
      <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
        <Calculator class="w-4 h-4 text-[#097e92]" />
        Unternehmenswert-Schätzung
      </h3>
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label class="text-xs text-gray-600 mb-1 block">Bereinigtes EBIT (TEUR)</label>
          <input v-model.number="adjustedEbit" type="number" placeholder="z.B. 250" class="input" />
        </div>
        <div>
          <label class="text-xs text-gray-600 mb-1 block">Empfohlener Faktor</label>
          <input :value="ebitFaktor.toFixed(1) + 'x'" readonly class="input bg-gray-50" />
        </div>
      </div>
      <div v-if="adjustedEbit > 0" class="bg-[#097e92]/10 rounded-lg p-4">
        <div class="text-xs text-gray-600">Geschätzter Unternehmenswert</div>
        <div class="text-2xl font-bold text-[#097e92]">{{ formatTeur(unternehmenswert) }} TEUR</div>
        <div class="text-xs text-gray-500 mt-1">= {{ adjustedEbit }} TEUR × {{ ebitFaktor.toFixed(1) }}× ({{ einstufung }})</div>
      </div>
    </div>

    <!-- Themenblöcke mit Fragen -->
    <div v-for="(blk, blkIdx) in fragen" :key="blkIdx" class="bg-white rounded-xl border border-gray-100 mb-4 overflow-hidden">
      <button @click="openBlock = openBlock === blkIdx ? -1 : blkIdx" class="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50">
        <div class="flex items-center gap-3">
          <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold', blockProzent(blkIdx) >= 70 ? 'bg-green-100 text-green-700' : blockProzent(blkIdx) >= 40 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700']">
            {{ blkIdx + 1 }}
          </div>
          <div class="text-left">
            <div class="font-semibold text-gray-900 text-sm">{{ blockNamen[blkIdx] }}</div>
            <div class="text-xs text-gray-500">{{ blockBeantwortet(blkIdx) }} / {{ blk.fragen.length }} beantwortet · Score {{ blockProzent(blkIdx) }}%</div>
          </div>
        </div>
        <ChevronDown :class="['w-5 h-5 text-gray-400 transition-transform', openBlock === blkIdx ? 'rotate-180' : '']" />
      </button>

      <div v-if="openBlock === blkIdx" class="border-t border-gray-100 divide-y divide-gray-50">
        <div v-for="f in blk.fragen" :key="f.nr" class="p-5">
          <div class="flex items-start gap-3 mb-3">
            <span class="font-mono text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-semibold">{{ f.nr }}</span>
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-800">{{ f.frage }}</p>
              <p v-if="f.erklaerung" class="text-xs text-gray-500 mt-1 whitespace-pre-line">{{ f.erklaerung }}</p>
            </div>
          </div>
          <div class="flex gap-2 mt-3">
            <button v-for="n in 5" :key="n" @click="setAntwort(f.nr, n)"
              :class="['flex-1 py-2 rounded-lg text-sm font-semibold border-2 transition-all',
                antworten[f.nr] === n
                  ? (n === 1 || n === 2 ? 'bg-green-500 border-green-500 text-white' : n === 3 ? 'bg-yellow-500 border-yellow-500 text-white' : 'bg-red-500 border-red-500 text-white')
                  : 'border-gray-200 text-gray-500 hover:border-gray-300']">
              {{ n }}
            </button>
          </div>
          <div class="flex justify-between text-xs text-gray-400 mt-1 px-1">
            <span>sehr gut</span><span>sehr schlecht</span>
          </div>
          <input v-model="notizen[f.nr]" placeholder="Notiz (optional)" class="input mt-2 text-sm" />
        </div>
      </div>
    </div>

    <!-- Save -->
    <div class="flex gap-3 mt-6">
      <button @click="save" :disabled="saving" class="flex-1 py-3 bg-[#097e92] text-white rounded-xl font-semibold hover:bg-[#0a9aaf] disabled:opacity-50">
        {{ saving ? 'Speichere…' : 'Bewertung speichern' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ChevronDown, Calculator } from '@lucide/vue'
import fragenData from '../../data/bewertungFragen.json'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String, readOnly: { type: Boolean, default: false } })

const fragen = ref(fragenData)
const blockNamen = fragenData.map(b => b.name.replace(/^Themenblock \d+[:\s"]*/i, '').replace(/"/g,'').trim())

const antworten = ref({}) // { fragenNr: 1-5 }
const notizen = ref({})   // { fragenNr: text }
const adjustedEbit = ref(0)
const openBlock = ref(0)
const saving = ref(false)

// --- Berechnungen ---
const beantworteteFragen = computed(() => Object.keys(antworten.value).filter(k => antworten.value[k] >= 1 && antworten.value[k] <= 5).length)

function blockBeantwortet(idx) {
  return fragen.value[idx].fragen.filter(f => antworten.value[f.nr] >= 1).length
}

function blockScore(idx) {
  // Score = 1 - Σ(Note-1) / (4 * Anzahl beantworteter Fragen)
  const f = fragen.value[idx].fragen
  const noten = f.map(x => antworten.value[x.nr]).filter(n => n >= 1)
  if (!noten.length) return 0
  const sum = noten.reduce((s, n) => s + (n - 1), 0)
  return 1 - (sum / (4 * noten.length))
}

function blockProzent(idx) { return Math.round(blockScore(idx) * 100) }

const gesamtScore = computed(() => {
  const scores = fragen.value.map((_, idx) => ({ score: blockScore(idx), antworten: blockBeantwortet(idx) }))
  const aktive = scores.filter(s => s.antworten > 0)
  if (!aktive.length) return 0
  return aktive.reduce((s, x) => s + x.score, 0) / aktive.length
})
const gesamtProzent = computed(() => Math.round(gesamtScore.value * 100))

const ebitFaktor = computed(() => {
  const p = gesamtProzent.value
  if (p < 40) return 3.0
  if (p < 55) return 4.0
  if (p < 70) return 5.0
  if (p < 85) return 6.0
  return 7.0
})

const einstufung = computed(() => {
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
  antworten.value[nr] = n
}

// --- Persist ---
async function load() {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (t.bewertungJson) {
      const b = JSON.parse(t.bewertungJson)
      antworten.value = b.antworten || {}
      notizen.value = b.notizen || {}
      adjustedEbit.value = b.adjustedEbit || 0
    }
  } catch (e) { console.error(e) }
}
onMounted(load)

async function save() {
  if (!props.targetId) return
  saving.value = true
  try {
    const payload = {
      antworten: antworten.value,
      notizen: notizen.value,
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
  } catch (e) { console.error(e); alert('Speichern fehlgeschlagen') }
  finally { saving.value = false }
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]; }
</style>
