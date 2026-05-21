<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-bold text-gray-900">Targets (Verkaufsmandate)</h2>
      <button @click="showModal = true" class="flex items-center gap-2 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf] transition-colors">
        <Plus class="w-4 h-4" /> Neues Mandat
      </button>
    </div>

    <!-- Such- und Filter-Leiste -->
    <div class="flex flex-wrap items-center gap-3 mb-3">
      <div class="relative flex-1 min-w-[260px] max-w-md">
        <Search class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
        <input v-model="search" placeholder="Suche nach mb-Nr, Verkäufer, Firma, Region…"
          class="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30" />
      </div>
      <select v-model="filterStatus" class="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
        <option value="">Alle Status</option>
        <option value="verfuegbar">Verfügbar</option>
        <option value="in_verhandlung">In Verhandlung</option>
        <option value="verkauft">Verkauft</option>
      </select>
      <select v-model="filterTyp" class="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
        <option value="">Alle Typen</option>
        <option>UVE Target</option>
        <option>Projekt Target</option>
        <option>MC Target</option>
        <option>Projekt Investoren</option>
        <option>MC Investoren</option>
      </select>
      <span class="text-sm text-gray-400 self-center">{{ filtered.length }} / {{ targets.length }}</span>
    </div>

    <!-- Tabelle -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-400 text-sm">Lade Targets…</div>
      <div v-else-if="!targets.length" class="p-8 text-center text-gray-400 text-sm">Noch keine Targets angelegt.</div>
      <div v-else-if="!filtered.length" class="p-8 text-center text-gray-400 text-sm">
        Keine Treffer. <button @click="clearFilters" class="underline hover:text-gray-700">Filter zurücksetzen</button>
      </div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">mb-Nr</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Verkäufer</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Region</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Typ</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Aktionen</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="t in filtered" :key="t.RowKey" class="hover:bg-gray-50 cursor-pointer" @click="$emit('open-detail', t)">
            <td class="px-4 py-3">
              <span class="font-mono text-xs bg-blue-50 text-blue-800 px-2 py-0.5 rounded">{{ t.mbNr }}</span>
            </td>
            <td class="px-4 py-3 text-sm font-medium text-gray-800">{{ t.verkaueferName }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ t.region }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ t.projekttyp }}</td>
            <td class="px-4 py-3">
              <span :class="statusClass(t.status)" class="text-xs font-medium px-2 py-0.5 rounded-full">
                {{ statusLabel(t.status) }}
              </span>
            </td>
            <td class="px-4 py-3" @click.stop>
              <select v-model="t.status" @change="updateStatus(t)" class="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#097e92]">
                <option value="verfuegbar">Verfügbar</option>
                <option value="in_verhandlung">In Verhandlung</option>
                <option value="verkauft">Verkauft</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal: Neues Mandat -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-bold text-gray-900">Neues Mandat anlegen</h3>
          <button @click="showModal = false" class="text-gray-400 hover:text-gray-600"><X class="w-5 h-5" /></button>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">mb-Nummer *</label>
            <input v-model="form.mbNr" placeholder="mb-XXX" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Projekttyp *</label>
            <select v-model="form.projekttyp" class="input">
              <option>UVE Target</option>
              <option>Projekt Target</option>
              <option>MC Target</option>
              <option>Projekt Investoren</option>
              <option>MC Investoren</option>
            </select>
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-600 mb-1">Name Verkäufer *</label>
            <input v-model="form.verkaueferName" placeholder="Vorname Nachname" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Region</label>
            <input v-model="form.region" placeholder="Raum München" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">PLZ</label>
            <input v-model="form.plz" placeholder="80000" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Branche</label>
            <input v-model="form.branche" placeholder="IT-Systemhaus" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Mitarbeiter</label>
            <input v-model="form.mitarbeiter" placeholder="12" class="input" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-600 mb-1">Umsatz (ca.)</label>
            <input v-model="form.umsatz" placeholder="ca. 2,1 Mio. €" class="input" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-600 mb-1">Kurzbeschreibung</label>
            <textarea v-model="form.beschreibung" rows="3" class="input resize-none" placeholder="Kurze Beschreibung des Unternehmens…"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal = false" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Abbrechen</button>
          <button @click="createTarget" :disabled="saving" class="px-5 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf] disabled:opacity-50">
            {{ saving ? 'Speichern…' : 'Mandat anlegen' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, X, Search } from '@lucide/vue'
import { getTargets, createTarget as apiCreateTarget, updateTarget } from '../../api.js'

const emit = defineEmits(['open-detail'])
const targets = ref([])
const search = ref('')
const filterStatus = ref('')
const filterTyp = ref('')
const loading = ref(true)

const filtered = computed(() => {
  let r = targets.value
  if (filterStatus.value) r = r.filter(t => t.status === filterStatus.value)
  if (filterTyp.value) r = r.filter(t => t.projekttyp === filterTyp.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    r = r.filter(t =>
      (t.mbNr || '').toLowerCase().includes(q) ||
      (t.verkaueferName || '').toLowerCase().includes(q) ||
      (t.firma || '').toLowerCase().includes(q) ||
      (t.region || '').toLowerCase().includes(q) ||
      (t.branche || '').toLowerCase().includes(q)
    )
  }
  return r
})

function clearFilters() {
  search.value = ''
  filterStatus.value = ''
  filterTyp.value = ''
}
const showModal = ref(false)
const saving = ref(false)
const form = ref({ mbNr: '', verkaueferName: '', region: '', plz: '', branche: '', mitarbeiter: '', umsatz: '', beschreibung: '', projekttyp: 'Projekt Target' })

function sortByMbNr(list) {
  return [...list].sort((a, b) => {
    const na = parseInt((a.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
    const nb = parseInt((b.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
    return na - nb
  })
}

onMounted(async () => {
  try { targets.value = sortByMbNr(await getTargets()) } finally { loading.value = false }
})

function statusClass(s) {
  if (s === 'verfuegbar') return 'bg-green-100 text-green-700'
  if (s === 'in_verhandlung') return 'bg-yellow-100 text-yellow-700'
  return 'bg-gray-100 text-gray-500'
}
function statusLabel(s) {
  if (s === 'verfuegbar') return 'Verfügbar'
  if (s === 'in_verhandlung') return 'In Verhandlung'
  return 'Verkauft'
}

async function createTarget() {
  if (!form.value.mbNr || !form.value.verkaueferName) return
  saving.value = true
  try {
    const t = await apiCreateTarget(form.value)
    targets.value = sortByMbNr([...targets.value, t])
    showModal.value = false
    form.value = { mbNr: '', verkaueferName: '', region: '', plz: '', branche: '', mitarbeiter: '', umsatz: '', beschreibung: '', projekttyp: 'Projekt Target' }
  } finally { saving.value = false }
}

async function updateStatus(t) {
  await updateTarget(t.RowKey, { status: t.status })
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]; }
</style>
