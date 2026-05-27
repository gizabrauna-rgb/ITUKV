<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-bold text-gray-900">Projekte</h2>
      <button @click="showModal = true" class="flex items-center gap-2 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8] transition-colors">
        <Plus class="w-4 h-4" /> Neues Projekt
      </button>
    </div>

    <!-- Such- und Filter-Leiste -->
    <div class="flex flex-wrap items-center gap-3 mb-3">
      <div class="relative flex-1 min-w-[260px] max-w-md">
        <Search class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
        <input v-model="search" placeholder="Suche nach mb-Nr, Verkäufer, Firma, Region…"
          class="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
      </div>
      <select v-model="filterStatus" class="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
        <option value="">Alle Status</option>
        <option value="verfuegbar">Verfügbar</option>
        <option value="in_verhandlung">In Verhandlung</option>
        <option value="verkauft">Verkauft</option>
      </select>
      <select v-model="filterRichtung" class="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
        <option value="">Alle Mandate</option>
        <option value="verkauf">Verkauf-Mandate</option>
        <option value="kauf">Kauf-Mandate</option>
      </select>
      <select v-model="filterTyp" class="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
        <option value="">Alle Projekttypen</option>
        <option>UVE Target</option>
        <option>Projekt Target</option>
        <option>MC Target</option>
        <option>Projekt Investoren</option>
        <option>MC Investoren</option>
        <option>Kauf-Mandat</option>
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
            <th class="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-8"></th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">mb-Nr</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Name / Firma</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Region</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Typ</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Fortschritt</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Letzte Aktivität</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Wiedervorlage</th>
            <th class="text-left px-2 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-8"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="t in sortedFiltered" :key="t.RowKey" class="hover:bg-gray-50 cursor-pointer" @click="$emit('open-detail', t)">
            <td class="px-3 py-3">
              <span :class="['inline-block w-2.5 h-2.5 rounded-full', wvDotClass(t.wiedervorlage)]" :title="wvTooltip(t.wiedervorlage)"></span>
            </td>
            <td class="px-4 py-3">
              <span class="font-mono text-xs bg-blue-50 text-blue-800 px-2 py-0.5 rounded">{{ t.mbNr }}</span>
            </td>
            <td class="px-4 py-3 text-sm">
              <div class="font-medium text-gray-800">{{ t.verkaueferName }}</div>
              <div class="text-xs text-gray-400">{{ t.firma }}</div>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ t.region }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ t.projekttyp }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <div class="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden w-24">
                  <div class="bg-[#0088ba] h-full" :style="`width: ${phaseProgress(t).percent}%`"></div>
                </div>
                <span class="text-xs text-gray-500 whitespace-nowrap">{{ phaseProgress(t).aktuell }}/{{ phaseProgress(t).gesamt }}</span>
              </div>
            </td>
            <td class="px-4 py-3 text-xs">
              <span :class="lastActivityClass(t)">{{ lastActivityLabel(t) }}</span>
            </td>
            <td class="px-4 py-3" @click.stop>
              <select v-model="t.status" @change="updateStatus(t)" :class="['text-xs border rounded-lg px-2 py-1 focus:outline-none', statusSelectClass(t.status)]">
                <template v-if="istKaufMandat(t)">
                  <option value="verfuegbar">Aktive Suche</option>
                  <option value="in_verhandlung">In Verhandlung</option>
                  <option value="verkauft">Erfolgreich abgeschlossen</option>
                  <option value="abgebrochen">Mandat beendet</option>
                </template>
                <template v-else>
                  <option value="verfuegbar">Verfügbar</option>
                  <option value="in_verhandlung">In Verhandlung</option>
                  <option value="verkauft">Verkauft</option>
                </template>
              </select>
            </td>
            <td class="px-4 py-3" @click.stop>
              <input v-model="t.wiedervorlage" type="date" @change="updateWiedervorlage(t)"
                :class="['text-xs border rounded-lg px-2 py-1 focus:outline-none', wvInputClass(t.wiedervorlage)]" />
              <button v-if="t.wiedervorlage" @click="t.wiedervorlage = ''; updateWiedervorlage(t)" class="ml-1 text-xs text-gray-400 hover:text-red-500">✕</button>
            </td>
            <td class="px-2 py-3" @click.stop>
              <button @click="askDelete(t)" class="text-gray-400 hover:text-red-500 p-1" title="Mandat löschen">
                <Trash2 class="w-4 h-4" />
              </button>
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
              <optgroup label="Verkauf-Mandate (Target sucht Käufer)">
                <option>UVE Target</option>
                <option>Projekt Target</option>
                <option>MC Target</option>
              </optgroup>
              <optgroup label="Kauf-Mandate (Käufer sucht Targets)">
                <option>Kauf-Mandat</option>
                <option>Projekt Investoren</option>
                <option>MC Investoren</option>
              </optgroup>
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
          <button @click="createTarget" :disabled="saving" class="px-5 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8] disabled:opacity-50">
            {{ saving ? 'Speichern…' : 'Mandat anlegen' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, X, Search, Trash2 } from '@lucide/vue'
import { getTargets, createTarget as apiCreateTarget, updateTarget, deleteTarget } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const emit = defineEmits(['open-detail'])
const targets = ref([])
const search = ref('')
const filterStatus = ref('')
const filterTyp = ref('')
const filterRichtung = ref('')
const loading = ref(true)

const filtered = computed(() => {
  let r = targets.value
  if (filterStatus.value) r = r.filter(t => t.status === filterStatus.value)
  if (filterTyp.value) r = r.filter(t => t.projekttyp === filterTyp.value)
  if (filterRichtung.value === 'kauf') r = r.filter(t => /kauf|investor/i.test(t.projekttyp || ''))
  if (filterRichtung.value === 'verkauf') r = r.filter(t => !/kauf|investor/i.test(t.projekttyp || ''))
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

async function askDelete(t) {
  const label = `${t.mbNr || ''} – ${t.verkaueferName || t.firma || ''}`
  if (!confirm(`Mandat „${label}" wirklich löschen? Inkl. zugeordneter Interessenten und Dokumente. Lässt sich nicht rückgängig machen.`)) return
  try {
    await deleteTarget(t.RowKey)
    targets.value = targets.value.filter(x => x.RowKey !== t.RowKey)
    toast.success('Mandat gelöscht')
  } catch (e) {
    toast.error('Löschen fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  }
}

async function updateWiedervorlage(t) {
  await updateTarget(t.RowKey, { wiedervorlage: t.wiedervorlage || '' })
}

// Sortierung: Überfällige zuerst, dann nach Wiedervorlage-Datum, dann ohne Datum nach mb-Nr
const sortedFiltered = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return [...filtered.value].sort((a, b) => {
    const av = a.wiedervorlage || ''
    const bv = b.wiedervorlage || ''
    // Beide ohne Datum → nach mbNr
    if (!av && !bv) {
      const na = parseInt((a.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
      const nb = parseInt((b.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
      return na - nb
    }
    // Mit Datum kommt zuerst
    if (av && !bv) return -1
    if (!av && bv) return 1
    // Beide mit Datum: aufsteigend (älteste = überfällig oben)
    return av < bv ? -1 : av > bv ? 1 : 0
  })
})

function daysUntil(dateStr) {
  if (!dateStr) return null
  const today = new Date(); today.setHours(0,0,0,0)
  const d = new Date(dateStr); d.setHours(0,0,0,0)
  return Math.round((d - today) / 86400000)
}

function wvDotClass(dateStr) {
  const d = daysUntil(dateStr)
  if (d === null) return 'bg-gray-200'
  if (d < 0) return 'bg-red-500'      // überfällig
  if (d === 0) return 'bg-yellow-400'  // heute
  if (d <= 7) return 'bg-blue-400'     // demnächst
  return 'bg-gray-300'
}

function wvTooltip(dateStr) {
  const d = daysUntil(dateStr)
  if (d === null) return 'Keine Wiedervorlage'
  if (d < 0) return `Überfällig (vor ${Math.abs(d)} Tagen)`
  if (d === 0) return 'Heute fällig'
  if (d === 1) return 'Morgen fällig'
  return `In ${d} Tagen fällig`
}

function wvInputClass(dateStr) {
  const d = daysUntil(dateStr)
  if (d === null) return 'border-gray-200 text-gray-500'
  if (d < 0) return 'border-red-300 bg-red-50 text-red-700 font-medium'
  if (d === 0) return 'border-yellow-300 bg-yellow-50 text-yellow-700 font-medium'
  if (d <= 7) return 'border-blue-200 bg-blue-50 text-blue-700'
  return 'border-gray-200 text-gray-600'
}

function istKaufMandat(t) {
  return /kauf|investor/i.test(t.projekttyp || '')
}

function statusSelectClass(s) {
  if (s === 'verfuegbar') return 'border-green-200 bg-green-50 text-green-700'
  if (s === 'in_verhandlung') return 'border-yellow-200 bg-yellow-50 text-yellow-700'
  return 'border-gray-200'
}

function phaseProgress(t) {
  try {
    const phasen = t.phasenJson ? JSON.parse(t.phasenJson) : []
    const gesamt = phasen.length || 15
    let aktuell = 0
    for (const p of phasen) {
      const aufg = p.aufgaben || []
      if (aufg.length && aufg.every(a => a.done)) aktuell++
    }
    const percent = gesamt > 0 ? Math.round((aktuell / gesamt) * 100) : 0
    return { aktuell, gesamt, percent }
  } catch {
    return { aktuell: 0, gesamt: 15, percent: 0 }
  }
}

function lastActivityDate(t) {
  try {
    const komm = t.kommunikationJson ? JSON.parse(t.kommunikationJson) : []
    if (!komm.length) return null
    const sorted = [...komm].sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
    return sorted[0].datum || null
  } catch {
    return null
  }
}

function lastActivityLabel(t) {
  const iso = lastActivityDate(t)
  if (!iso) return '—'
  const then = new Date(iso).getTime()
  const now = Date.now()
  const diffMs = now - then
  const min = Math.floor(diffMs / 60000)
  if (min < 60) return min <= 1 ? 'gerade' : `vor ${min} Min`
  const std = Math.floor(min / 60)
  if (std < 24) return `vor ${std} Std`
  const tg = Math.floor(std / 24)
  if (tg < 30) return `vor ${tg} Tg`
  const mon = Math.floor(tg / 30)
  return `vor ${mon} Mon`
}

function lastActivityClass(t) {
  const iso = lastActivityDate(t)
  if (!iso) return 'text-gray-400'
  const tg = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
  if (tg > 30) return 'text-red-600 font-medium'
  if (tg > 14) return 'text-amber-600'
  return 'text-gray-500'
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
