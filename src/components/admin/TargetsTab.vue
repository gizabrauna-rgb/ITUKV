<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-bold text-gray-900">Projekte</h2>
      <button @click="openNew" class="flex items-center gap-2 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8] transition-colors">
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
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Aktuelle Phase</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Mandant zuletzt</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Nächster Schritt für dich</th>
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
              <div class="flex items-center gap-1.5">
                <span class="font-mono text-xs bg-blue-50 text-blue-800 px-2 py-0.5 rounded">{{ t.mbNr }}</span>
                <span v-if="isNeu(t)" class="bg-green-100 text-green-700 text-[10px] font-bold px-1.5 py-0.5 rounded-full">NEU</span>
              </div>
            </td>
            <td class="px-4 py-3 text-sm">
              <div class="font-medium text-gray-800">{{ t.verkaueferName }}</div>
              <div class="text-xs text-gray-400">{{ t.firma }}</div>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ t.region }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ t.projekttyp }}</td>
            <td class="px-4 py-3">
              <div class="text-xs text-gray-700 truncate max-w-[180px]">{{ currentPhaseTitle(t) }}</div>
              <div class="flex items-center gap-2 mt-1">
                <div class="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden w-20">
                  <div class="bg-[#0088ba] h-full" :style="`width: ${phaseProgress(t).percent}%`"></div>
                </div>
                <span class="text-[10px] text-gray-400 whitespace-nowrap">{{ phaseProgress(t).aktuell }}/{{ phaseProgress(t).gesamt }}</span>
              </div>
            </td>
            <td class="px-4 py-3 text-xs max-w-[200px]">
              <div v-if="mandantLastAction(t).label" class="text-gray-700 truncate">{{ mandantLastAction(t).label }}</div>
              <div v-else class="text-gray-400 italic">noch nichts</div>
              <div v-if="mandantLastAction(t).datum" class="text-[10px] text-gray-400 mt-0.5">{{ formatRel(mandantLastAction(t).datum) }}</div>
            </td>
            <td class="px-4 py-3 text-xs max-w-[240px]">
              <div v-if="nextStep(t).label" :class="['p-2 rounded-lg border text-[11px]', nextStep(t).dringend ? 'bg-amber-50 border-amber-200' : 'bg-gray-50 border-gray-100']">
                <div class="text-gray-800 truncate">{{ nextStep(t).label }}</div>
                <div v-if="nextStep(t).verantwortlich" class="text-[10px] text-gray-500 mt-0.5">
                  Verantwortlich: <strong>{{ nextStep(t).verantwortlich }}</strong>
                </div>
              </div>
              <div v-else class="text-gray-400 italic">—</div>
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
                  <option value="pausiert">Pausiert</option>
                  <option value="verkaufsstopp">Verkaufsstopp</option>
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
              <div class="flex items-center gap-1 justify-end">
                <button @click="openEdit(t)" class="text-gray-400 hover:text-[#0088ba] p-1" title="Bearbeiten">
                  <Pencil class="w-4 h-4" />
                </button>
                <button @click="askDelete(t)" class="text-gray-400 hover:text-red-500 p-1" title="Mandat löschen">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal: Neues Mandat / Bearbeiten -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-bold text-gray-900">{{ editingId ? 'Mandat bearbeiten' : 'Neues Mandat anlegen' }}</h3>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600"><X class="w-5 h-5" /></button>
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
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Name Verkäufer *</label>
            <input v-model="form.verkaueferName" placeholder="Vorname Nachname" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Firma</label>
            <input v-model="form.firma" placeholder="z.B. ronet GmbH" class="input" />
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
          <button @click="closeModal" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Abbrechen</button>
          <button @click="saveTarget" :disabled="saving" class="px-5 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8] disabled:opacity-50">
            {{ saving ? 'Speichern…' : (editingId ? 'Änderungen speichern' : 'Mandat anlegen') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, X, Search, Trash2, Pencil } from '@lucide/vue'
import { getTargets, createTarget as apiCreateTarget, updateTarget, deleteTarget } from '../../api.js'
import { getPhasenVorlage } from '../../lib/phasenTemplates.js'
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
const form = ref({ mbNr: '', verkaueferName: '', firma: '', region: '', plz: '', branche: '', mitarbeiter: '', umsatz: '', beschreibung: '', projekttyp: 'Projekt Target' })

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
  if (s === 'pausiert') return 'bg-blue-100 text-blue-700'
  if (s === 'verkaufsstopp') return 'bg-red-100 text-red-700'
  if (s === 'verkauft') return 'bg-gray-100 text-gray-500'
  if (s === 'abgebrochen') return 'bg-gray-100 text-gray-500'
  return 'bg-gray-100 text-gray-500'
}
function statusLabel(s) {
  if (s === 'verfuegbar') return 'Verfügbar'
  if (s === 'in_verhandlung') return 'In Verhandlung'
  if (s === 'pausiert') return 'Pausiert'
  if (s === 'verkaufsstopp') return 'Verkaufsstopp'
  if (s === 'verkauft') return 'Verkauft'
  if (s === 'abgebrochen') return 'Abgebrochen'
  return s || 'Verkauft'
}

const editingId = ref(null)

function emptyForm() {
  return { mbNr: '', verkaueferName: '', firma: '', region: '', plz: '', branche: '', mitarbeiter: '', umsatz: '', beschreibung: '', projekttyp: 'Projekt Target' }
}

function openNew() {
  editingId.value = null
  form.value = emptyForm()
  showModal.value = true
}

function openEdit(t) {
  editingId.value = t.RowKey
  form.value = {
    mbNr: t.mbNr || '', verkaueferName: t.verkaueferName || '', firma: t.firma || '',
    region: t.region || '', plz: t.plz || '', branche: t.branche || '',
    mitarbeiter: t.mitarbeiter || '', umsatz: t.umsatz || '',
    beschreibung: t.beschreibung || '', projekttyp: t.projekttyp || 'Projekt Target',
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingId.value = null
  form.value = emptyForm()
}

async function saveTarget() {
  if (editingId.value) {
    saving.value = true
    try {
      await updateTarget(editingId.value, form.value)
      // lokal patchen
      const idx = targets.value.findIndex(t => t.RowKey === editingId.value)
      if (idx >= 0) targets.value[idx] = { ...targets.value[idx], ...form.value }
      closeModal()
    } finally { saving.value = false }
    return
  }
  // Anlegen
  if (!form.value.mbNr || !form.value.verkaueferName) return
  saving.value = true
  try {
    const t = await apiCreateTarget(form.value)
    targets.value = sortByMbNr([...targets.value, t])
    closeModal()
  } finally { saving.value = false }
}

// Backwards compat
const createTarget = saveTarget

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
  if (s === 'pausiert') return 'border-blue-200 bg-blue-50 text-blue-700'
  if (s === 'verkaufsstopp') return 'border-red-200 bg-red-50 text-red-700'
  return 'border-gray-200'
}

function phaseProgress(t) {
  const phasen = getPhasen(t)
  const gesamt = phasen.length || 15
  let aktuell = 0
  for (const p of phasen) {
    const aufg = p.aufgaben || []
    if (aufg.length && aufg.every(a => a.done)) aktuell++
  }
  const percent = gesamt > 0 ? Math.round((aktuell / gesamt) * 100) : 0
  return { aktuell, gesamt, percent }
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

// =============== Cockpit-Helfer (Mandanten-Aktivitaet + Naechster Schritt) ===============
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

function getPhasen(t) {
  // Wenn phasenJson leer/ungueltig -> aktuelle Vorlage fuer den Projekttyp laden
  try {
    const ph = JSON.parse(t.phasenJson || '[]')
    if (Array.isArray(ph) && ph.length) return ph
  } catch {}
  return getPhasenVorlage(t.projekttyp || '')
}

function currentPhase(t) {
  const ph = getPhasen(t)
  for (let i = 0; i < ph.length; i++) {
    if ((ph[i].aufgaben || []).some(a => !a.done)) return { idx: i + 1, obj: ph[i], total: ph.length }
  }
  return { idx: ph.length || 1, obj: ph[ph.length - 1] || null, total: ph.length }
}
function currentPhaseTitle(t) {
  const o = currentPhase(t).obj
  return o ? (o.titel || '').replace(/^\d+\.\s*/, '') : '—'
}

function mandantLastAction(t) {
  let label = '', datum = null
  function maybe(l, d) {
    if (!d) return
    const dd = new Date(d)
    if (isNaN(dd.getTime())) return
    if (!datum || dd > datum) { label = l; datum = dd }
  }
  if (t.kostenInfoBestaetigtAm) maybe('Kosten zur Kenntnis genommen', t.kostenInfoBestaetigtAm)
  if (t.fragebogenAbgegebenAm) maybe('Fragebogen abgegeben', t.fragebogenAbgegebenAm)
  if (t.zieleMotivationenJson && t.zieleMotivationenJson !== '{}' && !label) label = 'Ziele & Motivationen ausgefüllt'
  if (t.akquisitionsstrategieJson && t.akquisitionsstrategieJson !== '{}' && !label) label = 'Akquisitionsstrategie ausgefüllt'
  try {
    const verlauf = JSON.parse(t.kommunikationJson || '[]')
    const mandant = verlauf.filter(e => !e.createdByMibeca && !e.createdByKI).sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
    if (mandant.length) maybe(mandant[0].betreff || (mandant[0].beschreibung || '').slice(0, 50) || 'Nachricht', mandant[0].datum)
  } catch {}
  return { label, datum }
}

function isNeu(t) {
  const d = mandantLastAction(t).datum
  if (!d) return false
  return (Date.now() - d.getTime()) < 3 * 86400000
}

function nextStep(t) {
  const ph = currentPhase(t).obj
  if (!ph) return { label: '', verantwortlich: '', dringend: false }
  const offen = (ph.aufgaben || []).filter(a => !a.done)
  const mibecaTask = offen.find(a => istMibecaAufgabe(a.verantwortlich))
  if (mibecaTask) {
    return {
      label: (mibecaTask.label || '').replace(/^MB\d+:\s*/, ''),
      verantwortlich: mibecaTask.verantwortlich,
      dringend: true,
    }
  }
  const wartetAufMandant = offen.find(a => istMandantAufgabe(a.verantwortlich))
  if (wartetAufMandant) {
    return {
      label: 'Warte auf Mandant: ' + (wartetAufMandant.label || '').replace(/^MB\d+:\s*/, ''),
      verantwortlich: wartetAufMandant.verantwortlich,
      dringend: false,
    }
  }
  if (offen.length) {
    return { label: (offen[0].label || '').replace(/^MB\d+:\s*/, ''), verantwortlich: offen[0].verantwortlich || '—', dringend: false }
  }
  return { label: '', verantwortlich: '', dringend: false }
}

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

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
