<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Verkaufs-Pipeline</h2>
        <p class="text-sm text-gray-500 mt-1">
          Alle Verkaufs-Mandate nach Phase im Master-Prozess. Klick auf eine Karte öffnet die Akte.
        </p>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <span>{{ verkaufsMandate.length }} Mandate · {{ aktivCount }} aktiv</span>
      </div>
    </div>

    <!-- Filter -->
    <div class="flex flex-wrap gap-2 mb-5">
      <select v-model="filterStatus" class="text-xs px-3 py-1.5 border border-gray-200 rounded-lg bg-white">
        <option value="">Alle Status</option>
        <option v-for="s in statusOptionen" :key="s" :value="s">{{ s }}</option>
      </select>
      <input v-model="filterText" placeholder="Firma / mb-Nr suchen…" class="text-xs px-3 py-1.5 border border-gray-200 rounded-lg flex-1 min-w-[160px] max-w-xs" />
      <div class="flex gap-1 ml-auto">
        <button @click="ansicht = 'kanban'" :class="['text-xs px-3 py-1.5 rounded-lg', ansicht === 'kanban' ? 'bg-orange-600 text-white' : 'border border-gray-200 bg-white']">Kanban</button>
        <button @click="ansicht = 'tabelle'" :class="['text-xs px-3 py-1.5 rounded-lg', ansicht === 'tabelle' ? 'bg-orange-600 text-white' : 'border border-gray-200 bg-white']">Tabelle</button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-sm text-gray-400">Lade Mandate …</div>
    <div v-else-if="!gefiltert.length" class="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-10 text-center">
      <Briefcase class="w-10 h-10 text-gray-300 mx-auto mb-3" />
      <p class="text-sm text-gray-500">Keine Verkaufs-Mandate für diese Filter.</p>
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
        <div v-for="p in PHASEN_TITEL" :key="p.id" class="w-64 flex-shrink-0">
          <div class="bg-gray-100 rounded-t-xl px-3 py-2 border-b-2 border-orange-200">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-700 truncate">{{ p.id }} · {{ p.kurz }}</span>
              <span class="text-[10px] bg-white text-gray-600 px-1.5 py-0.5 rounded-full flex-shrink-0 ml-1">{{ phaseMandate(p.id).length }}</span>
            </div>
          </div>
          <div class="bg-gray-50 rounded-b-xl p-2 min-h-[120px] space-y-2">
            <button v-for="m in phaseMandate(p.id)" :key="m.id"
              @click="$emit('open-akte', { targetId: m.id })"
              class="block w-full text-left bg-white rounded-lg p-2 border border-gray-100 hover:border-orange-200 transition-colors">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] font-mono bg-orange-50 text-orange-700 px-1 rounded">{{ m.mbNr }}</span>
                <span v-if="m.status" class="text-[9px] text-gray-500">{{ m.status }}</span>
              </div>
              <div class="text-xs font-semibold text-gray-900 truncate">{{ m.firma || m.name }}</div>
              <div class="text-[10px] text-gray-500 truncate">{{ m.gfName }}</div>
              <div v-if="m.offen" class="text-[10px] text-amber-700 mt-1 flex items-center gap-1">
                <ListTodo class="w-3 h-3" /> {{ m.offen }} offen
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
            <th class="text-left px-3 py-2">mb-Nr</th>
            <th class="text-left px-3 py-2">Firma / Verkäufer</th>
            <th class="text-left px-3 py-2">Phase</th>
            <th class="text-left px-3 py-2">Status</th>
            <th class="text-left px-3 py-2">Offene Aufgaben</th>
            <th class="text-left px-3 py-2">Wiedervorlage</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="m in gefiltert" :key="m.id"
            @click="$emit('open-akte', { targetId: m.id })"
            class="hover:bg-gray-50 cursor-pointer">
            <td class="px-3 py-2"><span class="text-[10px] font-mono bg-orange-50 text-orange-700 px-1.5 py-0.5 rounded">{{ m.mbNr }}</span></td>
            <td class="px-3 py-2 font-medium text-gray-900">
              {{ m.firma || m.name }}
              <span v-if="m.gfName" class="text-xs text-gray-500 ml-1">· {{ m.gfName }}</span>
            </td>
            <td class="px-3 py-2">
              <span class="text-[10px] bg-orange-50 text-orange-700 px-1.5 py-0.5 rounded">{{ m.phaseId }} · {{ phaseKurz(m.phaseId) }}</span>
            </td>
            <td class="px-3 py-2 text-xs text-gray-600">{{ m.status || '—' }}</td>
            <td class="px-3 py-2 text-xs text-gray-600">{{ m.offen || '—' }}</td>
            <td class="px-3 py-2 text-[10px] text-gray-500">{{ formatDate(m.wiedervorlage) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Briefcase, ListTodo, ChevronLeft, ChevronRight } from '@lucide/vue'
import { getTargets } from '../../api.js'

defineEmits(['open-akte'])

const kanbanRef = ref(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)
function updateScrollState() {
  const el = kanbanRef.value
  if (!el) { canScrollLeft.value = false; canScrollRight.value = false; return }
  canScrollLeft.value = el.scrollLeft > 4
  canScrollRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 4
}
function scrollKanban(dir) {
  const el = kanbanRef.value
  if (!el) return
  el.scrollBy({ left: dir * 280, behavior: 'smooth' })
}

// Master-Prozess Verkauf — 15 Phasen, Kurztitel fuer Kanban-Header
const PHASEN_TITEL = [
  { id: 1,  kurz: 'UVE Start' },
  { id: 2,  kurz: 'UVE Abschluss' },
  { id: 3,  kurz: 'Marktansprache' },
  { id: 4,  kurz: 'NDA' },
  { id: 5,  kurz: 'Erstes Kennenlernen' },
  { id: 6,  kurz: 'Datenraum / Element' },
  { id: 7,  kurz: 'Unterlagen-Austausch' },
  { id: 8,  kurz: 'Indikatives Angebot' },
  { id: 9,  kurz: 'Verhandlungen' },
  { id: 10, kurz: 'LOI' },
  { id: 11, kurz: 'Due Diligence' },
  { id: 12, kurz: 'Vertragsgestaltung' },
  { id: 13, kurz: 'Notartermin & Closing' },
  { id: 14, kurz: 'Post-Closing' },
  { id: 15, kurz: 'Erfolgsmeldung' },
]

function phaseKurz(id) { return (PHASEN_TITEL.find(p => p.id === id) || { kurz: '—' }).kurz }

const targets = ref([])
const loading = ref(true)
const ansicht = ref('kanban')
const filterStatus = ref('')
const filterText = ref('')

onMounted(async () => {
  try {
    const all = await getTargets()
    targets.value = (all || []).filter(t => !/kauf|investor/i.test(t.projekttyp || ''))
  } catch (e) { console.error(e) }
  finally { loading.value = false; await nextTick(); updateScrollState() }
})
watch(() => [ansicht.value, loading.value], async () => { await nextTick(); updateScrollState() })

function isPhaseDone(p) {
  return (p?.aufgaben || []).length > 0 && p.aufgaben.every(a => a.done)
}

const verkaufsMandate = computed(() => targets.value.map(t => {
  let phasen = []
  try { phasen = JSON.parse(t.phasenJson || '[]') } catch {}
  if (!Array.isArray(phasen)) phasen = []
  let phaseId = 1
  for (let i = 0; i < phasen.length; i++) {
    if (!isPhaseDone(phasen[i])) { phaseId = phasen[i].id || i + 1; break }
    if (i === phasen.length - 1) phaseId = phasen[i].id || phasen.length
  }
  const offen = phasen.reduce((sum, ph) => sum + (ph.aufgaben || []).filter(a => !a.done).length, 0)
  return {
    id: t.RowKey || t.id,
    mbNr: t.mbNr || '—',
    firma: t.firma || '',
    name: t.verkaueferName || '',
    gfName: t.gfName || t.verkaueferName || '',
    status: t.status || '',
    phaseId,
    offen,
    wiedervorlage: t.wiedervorlage || '',
  }
}))

const statusOptionen = computed(() => {
  return [...new Set(verkaufsMandate.value.map(m => m.status).filter(Boolean))].sort()
})

const aktivCount = computed(() => verkaufsMandate.value.filter(m => !/verkauft|abgebrochen/i.test(m.status)).length)

const gefiltert = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  return verkaufsMandate.value.filter(m => {
    if (filterStatus.value && m.status !== filterStatus.value) return false
    if (q && !(m.firma + ' ' + m.name + ' ' + m.mbNr).toLowerCase().includes(q)) return false
    return true
  })
})

function phaseMandate(phaseId) {
  return gefiltert.value.filter(m => m.phaseId === phaseId)
}

function formatDate(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleDateString('de-DE') } catch { return '' }
}
</script>

<style scoped>
.kanban-scroll { scrollbar-width: auto; scrollbar-color: #cbd5e1 #f1f5f9; }
.kanban-scroll::-webkit-scrollbar { height: 10px; }
.kanban-scroll::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 8px; }
.kanban-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 8px; }
.kanban-scroll::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
