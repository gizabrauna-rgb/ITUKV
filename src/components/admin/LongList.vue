<template>
  <div>
    <div class="mb-5 flex items-start justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Long-List / Short-List</h2>
        <p class="text-sm text-gray-500 mt-1">Targets, die für diesen Käufer in Frage kommen. Match-Score zeigt, wie gut sie zum Suchprofil passen.</p>
      </div>
      <button @click="refreshList" :disabled="loading"
        class="flex items-center gap-2 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf] disabled:opacity-50">
        <RefreshCw :class="['w-4 h-4', loading ? 'animate-spin' : '']" />
        {{ loading ? 'Lade…' : 'Long-List neu berechnen' }}
      </button>
    </div>

    <!-- Filter -->
    <div class="flex gap-2 mb-3">
      <button @click="filter = 'long'" :class="['px-3 py-1.5 rounded-lg text-xs font-medium', filter === 'long' ? 'bg-[#097e92] text-white' : 'bg-white border border-gray-200']">
        Long-List ({{ items.length }})
      </button>
      <button @click="filter = 'short'" :class="['px-3 py-1.5 rounded-lg text-xs font-medium', filter === 'short' ? 'bg-[#097e92] text-white' : 'bg-white border border-gray-200']">
        Short-List ({{ shortListCount }})
      </button>
      <button @click="filter = 'abgesagt'" :class="['px-3 py-1.5 rounded-lg text-xs font-medium', filter === 'abgesagt' ? 'bg-[#097e92] text-white' : 'bg-white border border-gray-200']">
        Abgesagt ({{ abgesagtCount }})
      </button>
    </div>

    <div v-if="loading" class="text-center text-sm text-gray-400 py-10">Lade Kandidaten…</div>
    <div v-else-if="!visibleItems.length" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">
      <Users class="w-10 h-10 mx-auto mb-3 text-gray-200" />
      Keine Kandidaten gefunden.
      <p class="text-xs mt-2">Vergiss nicht: erst Suchprofil ausfüllen, dann Long-List neu berechnen.</p>
    </div>

    <div v-else class="space-y-2">
      <div v-for="k in visibleItems" :key="k.id || k.RowKey" class="bg-white rounded-xl border border-gray-100 p-4 flex items-start gap-3">
        <!-- Score-Kreis -->
        <div :class="['w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0',
                       k.score >= 70 ? 'bg-green-100 text-green-700' : k.score >= 40 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-500']">
          {{ k.score }}%
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-medium text-gray-900">{{ k.firma }}</span>
            <span v-if="k.istKunde" class="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full font-semibold">Kunde</span>
            <span v-if="k.istExKunde" class="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded-full font-semibold">Ex-Kunde</span>
          </div>
          <div class="text-xs text-gray-500 mt-0.5">
            {{ k.plz }} {{ k.ort }} · {{ k.mitarbeiter || '?' }} MA · {{ k.umsatz || '?' }} Umsatz
          </div>
          <div v-if="k.matchGruende?.length" class="flex flex-wrap gap-1 mt-2">
            <span v-for="g in k.matchGruende" :key="g" class="text-[10px] bg-[#097e92]/10 text-[#097e92] px-2 py-0.5 rounded-full">✓ {{ g }}</span>
          </div>
          <div v-if="k.ablehnGruende?.length" class="flex flex-wrap gap-1 mt-1">
            <span v-for="g in k.ablehnGruende" :key="g" class="text-[10px] bg-red-50 text-red-600 px-2 py-0.5 rounded-full">✗ {{ g }}</span>
          </div>
        </div>
        <div class="flex gap-1 flex-shrink-0">
          <button v-if="k.status !== 'short'" @click="setStatus(k, 'short')" title="Auf Short-List"
            class="p-1.5 hover:bg-green-50 rounded text-green-600"><Check class="w-4 h-4" /></button>
          <button v-if="k.status !== 'abgesagt'" @click="setStatus(k, 'abgesagt')" title="Absagen"
            class="p-1.5 hover:bg-red-50 rounded text-red-600"><X class="w-4 h-4" /></button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Users, RefreshCw, Check, X } from '@lucide/vue'
import { authFetch, getKontakte } from '../../api.js'

const props = defineProps({ targetId: String })

const items = ref([])
const loading = ref(true)
const filter = ref('long')
const decisions = ref({})  // { kontaktId: 'short' | 'abgesagt' }

const shortListCount = computed(() => Object.values(decisions.value).filter(v => v === 'short').length)
const abgesagtCount = computed(() => Object.values(decisions.value).filter(v => v === 'abgesagt').length)
const visibleItems = computed(() => {
  if (filter.value === 'long') return items.value.filter(k => !decisions.value[k.id])
  if (filter.value === 'short') return items.value.filter(k => decisions.value[k.id] === 'short')
  if (filter.value === 'abgesagt') return items.value.filter(k => decisions.value[k.id] === 'abgesagt')
  return items.value
})

function scoreFor(kontakt, suchprofil) {
  let score = 50  // Basis
  const reasons = []
  const dislikes = []
  const ist = (n, min, max) => (!min || n >= min) && (!max || n <= max)

  // Mitarbeiter
  const ma = parseInt(kontakt.mitarbeiter) || 0
  if (suchprofil.maMin || suchprofil.maMax) {
    if (ma > 0 && ist(ma, suchprofil.maMin, suchprofil.maMax)) {
      score += 15; reasons.push(`${ma} MA passt`)
    } else if (ma > 0) {
      score -= 20; dislikes.push(`${ma} MA außerhalb ${suchprofil.maMin}-${suchprofil.maMax}`)
    }
  }

  // Region (einfaches PLZ-Match)
  if (suchprofil.zentralPlz && kontakt.plz) {
    if (kontakt.plz.startsWith(suchprofil.zentralPlz.slice(0, 2))) {
      score += 10; reasons.push('PLZ-Region passt')
    }
  }
  if (suchprofil.regionen && kontakt.ort) {
    const regs = suchprofil.regionen.toLowerCase().split(/[,;]/).map(s => s.trim()).filter(Boolean)
    if (regs.some(r => kontakt.ort.toLowerCase().includes(r) || (kontakt.plz || '').startsWith(r.slice(0, 2)))) {
      score += 10; reasons.push('Region erlaubt')
    }
  }

  // Kunde-Bonus (vertraute Targets bevorzugt)
  if (kontakt.istKunde) { score += 5; reasons.push('Bestandskunde') }

  // IT-Fokus (gegen kontakt-flags wie hatUC etc.)
  if (suchprofil.itFokus?.includes('MSP / Managed Services') && (kontakt.hatMC || kontakt.bietet?.toLowerCase().includes('msp'))) {
    score += 8; reasons.push('MSP-Fokus')
  }

  // Cap
  score = Math.max(0, Math.min(100, score))
  return { score, reasons, dislikes }
}

async function refreshList() {
  loading.value = true
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    const suchprofil = t.suchprofilJson ? JSON.parse(t.suchprofilJson) : {}
    const kontakte = await getKontakte()
    const ranked = (kontakte || [])
      .map(k => {
        const { score, reasons, dislikes } = scoreFor(k, suchprofil)
        return {
          ...k, id: k.RowKey || k.id, score,
          matchGruende: reasons, ablehnGruende: dislikes,
        }
      })
      .filter(k => k.score >= 30)
      .sort((a, b) => b.score - a.score)
    items.value = ranked
    // Decisions aus target laden
    try { decisions.value = JSON.parse(t.longListDecisionsJson || '{}') } catch { decisions.value = {} }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function setStatus(k, status) {
  const newDecisions = { ...decisions.value, [k.id]: status }
  decisions.value = newDecisions
  try {
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, longListDecisionsJson: JSON.stringify(newDecisions) } })
  } catch (e) { console.error(e) }
}

onMounted(refreshList)
</script>
