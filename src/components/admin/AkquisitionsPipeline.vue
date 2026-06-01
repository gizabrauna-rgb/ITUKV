<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Akquisitions-Pipeline</h2>
        <p class="text-sm text-gray-500 mt-1">
          Alle Akquisitionen aller Käufer-Mandate in einer Übersicht. Klick auf eine Karte öffnet die Akte des jeweiligen Käufers.
        </p>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <span>{{ alleAkquisitionen.length }} Akquisitionen · {{ aktivCount }} laufend</span>
      </div>
    </div>

    <!-- Filterleiste -->
    <div class="flex flex-wrap gap-2 mb-5">
      <select v-model="filterStatus" class="text-xs px-3 py-1.5 border border-gray-200 rounded-lg bg-white">
        <option value="">Alle Status</option>
        <option v-for="s in AKQ_STATUS" :key="s.key" :value="s.key">{{ s.label }}</option>
      </select>
      <select v-model="filterInvestor" class="text-xs px-3 py-1.5 border border-gray-200 rounded-lg bg-white">
        <option value="">Alle Investoren</option>
        <option v-for="inv in investoren" :key="inv.id" :value="inv.id">{{ inv.mbNr }} · {{ inv.name }}</option>
      </select>
      <input v-model="filterText" placeholder="Firma suchen…" class="text-xs px-3 py-1.5 border border-gray-200 rounded-lg flex-1 min-w-[160px] max-w-xs" />
      <div class="flex gap-1 ml-auto">
        <button @click="ansicht = 'kanban'" :class="['text-xs px-3 py-1.5 rounded-lg', ansicht === 'kanban' ? 'bg-blue-600 text-white' : 'border border-gray-200 bg-white']">Kanban</button>
        <button @click="ansicht = 'tabelle'" :class="['text-xs px-3 py-1.5 rounded-lg', ansicht === 'tabelle' ? 'bg-blue-600 text-white' : 'border border-gray-200 bg-white']">Tabelle</button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-sm text-gray-400">Lade Akquisitionen …</div>
    <div v-else-if="!gefiltert.length" class="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-10 text-center">
      <Target class="w-10 h-10 text-gray-300 mx-auto mb-3" />
      <p class="text-sm text-gray-500">Keine Akquisitionen für diese Filter.</p>
    </div>

    <!-- Kanban -->
    <div v-else-if="ansicht === 'kanban'" class="relative">
      <button v-show="canScrollLeft" @click="scrollKanban(-1)"
        class="absolute left-1 top-1/2 -translate-y-1/2 z-10 bg-white shadow-lg rounded-full p-2 border border-gray-200 hover:bg-gray-50">
        <ChevronLeft class="w-5 h-5 text-gray-700" />
      </button>
      <button v-show="canScrollRight" @click="scrollKanban(1)"
        class="absolute right-1 top-1/2 -translate-y-1/2 z-10 bg-white shadow-lg rounded-full p-2 border border-gray-200 hover:bg-gray-50">
        <ChevronRight class="w-5 h-5 text-gray-700" />
      </button>
      <div ref="kanbanRef" @scroll="updateScrollState" class="overflow-x-auto kanban-scroll">
      <div class="flex gap-3 min-w-max pb-3">
        <div v-for="p in AKQ_PHASEN" :key="p.id" class="w-64 flex-shrink-0">
          <div class="bg-gray-100 rounded-t-xl px-3 py-2 border-b-2 border-blue-200">
            <div class="flex items-center justify-between gap-1">
              <span class="text-xs font-semibold text-gray-700 truncate flex-1">
                {{ p.id }} · {{ p.label }}
              </span>
              <button @click="phasenInfoModal = p" class="hover:bg-gray-200 rounded p-0.5 flex-shrink-0" title="Was ist in dieser Phase?">
                <Info class="w-3.5 h-3.5 text-gray-500" />
              </button>
              <span class="text-[10px] bg-white text-gray-600 px-1.5 py-0.5 rounded-full flex-shrink-0">{{ phaseAkquisitionen(p.id).length }}</span>
            </div>
          </div>
          <div class="bg-gray-50 rounded-b-xl p-2 min-h-[120px] space-y-2">
            <button v-for="a in phaseAkquisitionen(p.id)" :key="a.akq.id"
              @click="$emit('open-akte', { targetId: a.investor.id })"
              class="block w-full text-left bg-white rounded-lg p-2 border border-gray-100 hover:border-blue-200 transition-colors">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] font-mono bg-green-50 text-green-700 px-1 rounded">{{ a.investor.mbNr }}</span>
                <span :class="['text-[9px] px-1 rounded-full', statusInfo(a.akq.status).cls]">{{ a.akq.status }}</span>
              </div>
              <div class="text-xs font-semibold text-gray-900 truncate">{{ a.akq.name }}</div>
              <div class="text-[10px] text-gray-500 truncate">{{ a.investor.name }}</div>
              <div v-if="offeneAufgaben(a.akq)" class="text-[10px] text-amber-700 mt-1 flex items-center gap-1">
                <ListTodo class="w-3 h-3" /> {{ offeneAufgaben(a.akq) }} offen
              </div>
            </button>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- Tabelle -->
    <div v-else class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-xs text-gray-500 uppercase">
          <tr>
            <th class="text-left px-3 py-2">Käufer</th>
            <th class="text-left px-3 py-2">Firma</th>
            <th class="text-left px-3 py-2">Phase</th>
            <th class="text-left px-3 py-2">Status</th>
            <th class="text-left px-3 py-2">Offene Aufgaben</th>
            <th class="text-left px-3 py-2">Angelegt</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="a in gefiltert" :key="a.akq.id"
            @click="$emit('open-akte', { targetId: a.investor.id })"
            class="hover:bg-gray-50 cursor-pointer">
            <td class="px-3 py-2">
              <span class="text-[10px] font-mono bg-green-50 text-green-700 px-1.5 py-0.5 rounded">{{ a.investor.mbNr }}</span>
              <span class="text-xs text-gray-600 ml-2">{{ a.investor.name }}</span>
            </td>
            <td class="px-3 py-2 font-medium text-gray-900">{{ a.akq.name }}</td>
            <td class="px-3 py-2">
              <span class="text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">{{ a.akq.phase || 1 }} · {{ phaseInfo(a.akq.phase || 1).label }}</span>
            </td>
            <td class="px-3 py-2">
              <span :class="['text-[10px] px-1.5 py-0.5 rounded-full', statusInfo(a.akq.status || 'laufend').cls]">{{ a.akq.status || 'laufend' }}</span>
            </td>
            <td class="px-3 py-2 text-xs text-gray-600">{{ offeneAufgaben(a.akq) || '—' }}</td>
            <td class="px-3 py-2 text-[10px] text-gray-500">{{ formatDate(a.akq.createdAt) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Phasen-Info-Popup -->
    <div v-if="phasenInfoModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center px-4" @click="phasenInfoModal = null">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl" @click.stop>
        <div class="flex items-start justify-between gap-3 mb-3">
          <h3 class="font-bold text-gray-900">Phase {{ phasenInfoModal.id }} · {{ phasenInfoModal.label }}</h3>
          <button @click="phasenInfoModal = null" class="text-gray-400 hover:text-gray-600">
            <X class="w-5 h-5" />
          </button>
        </div>
        <p class="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{{ phasenInfoModal.beschreibung }}</p>
        <div class="mt-4 pt-3 border-t border-gray-100 text-right">
          <button @click="phasenInfoModal = null" class="px-4 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">Schließen</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { Target, ListTodo, ChevronLeft, ChevronRight, Info, X } from '@lucide/vue'
import { getTargets } from '../../api.js'
import { AKQ_PHASEN, AKQ_STATUS, phaseInfo, statusInfo } from '../../data/akquisitionsPhasen.js'

defineEmits(['open-akte'])

// Kanban-Scroll
const kanbanRef = ref(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(true)
let resizeObs = null
function updateScrollState() {
  const el = kanbanRef.value
  if (!el) return
  canScrollLeft.value = el.scrollLeft > 4
  canScrollRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 4
}
function scrollKanban(dir) {
  const el = kanbanRef.value
  if (!el) return
  el.scrollBy({ left: dir * 280, behavior: 'smooth' })
}
onBeforeUnmount(() => {
  if (resizeObs) resizeObs.disconnect()
  window.removeEventListener('resize', updateScrollState)
})

const phasenInfoModal = ref(null)

const targets = ref([])
const loading = ref(true)
const ansicht = ref('kanban')
const filterStatus = ref('')
const filterInvestor = ref('')
const filterText = ref('')

onMounted(async () => {
  try {
    const all = await getTargets()
    targets.value = (all || []).filter(t => /kauf|investor/i.test(t.projekttyp || ''))
  } catch (e) { console.error(e) }
  finally {
    loading.value = false
    await nextTick(); await nextTick()
    updateScrollState()
    if (kanbanRef.value && window.ResizeObserver) {
      resizeObs = new ResizeObserver(updateScrollState)
      resizeObs.observe(kanbanRef.value)
    }
    window.addEventListener('resize', updateScrollState)
  }
})
watch(() => [ansicht.value, filterText.value, filterStatus.value, filterInvestor.value], async () => { await nextTick(); updateScrollState() })

const alleAkquisitionen = computed(() => {
  const out = []
  for (const t of targets.value) {
    let liste = []
    try { liste = JSON.parse(t.akquisitionenJson || '[]') } catch {}
    if (!Array.isArray(liste)) continue
    for (const akq of liste) {
      out.push({
        akq,
        investor: {
          id: t.RowKey || t.id,
          mbNr: t.mbNr || '—',
          name: t.verkaueferName || t.firma || '',
        },
      })
    }
  }
  return out
})

const investoren = computed(() => {
  const m = new Map()
  for (const t of targets.value) m.set(t.RowKey || t.id, { id: t.RowKey || t.id, mbNr: t.mbNr || '—', name: t.verkaueferName || t.firma || '' })
  return [...m.values()].sort((a, b) => (a.mbNr || '').localeCompare(b.mbNr || ''))
})

const gefiltert = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  return alleAkquisitionen.value.filter(a => {
    if (filterStatus.value && (a.akq.status || 'laufend') !== filterStatus.value) return false
    if (filterInvestor.value && a.investor.id !== filterInvestor.value) return false
    if (q && !(a.akq.name || '').toLowerCase().includes(q)) return false
    return true
  })
})

const aktivCount = computed(() => alleAkquisitionen.value.filter(a => (a.akq.status || 'laufend') === 'laufend').length)

function phaseAkquisitionen(phaseId) {
  return gefiltert.value.filter(a => (a.akq.phase || 1) === phaseId)
}
function offeneAufgaben(akq) {
  return (akq.aufgaben || []).filter(x => !x.erledigt).length
}
function formatDate(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleDateString('de-DE') } catch { return '' }
}
</script>

<style scoped>
/* Scrollbar dauerhaft sichtbar */
.kanban-scroll { scrollbar-width: auto; scrollbar-color: #cbd5e1 #f1f5f9; }
.kanban-scroll::-webkit-scrollbar { height: 10px; }
.kanban-scroll::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 8px; }
.kanban-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 8px; }
.kanban-scroll::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
