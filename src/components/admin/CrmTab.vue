<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-bold text-gray-900">CRM / Investoren-Datenbank</h2>
      <div class="flex gap-2">
        <button @click="toggleView" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
          <Map v-if="view === 'list'" class="w-4 h-4" /> <List v-else class="w-4 h-4" />
          {{ view === 'list' ? 'Kartenansicht' : 'Listenansicht' }}
        </button>
        <button @click="exportCsv" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
          <Download class="w-4 h-4" /> Exportieren
        </button>
        <button @click="showImport = true" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
          <Upload class="w-4 h-4" /> Importieren
        </button>
        <button @click="showNewModal = true" class="flex items-center gap-2 px-3 py-2 bg-[#097e92] text-white rounded-xl text-sm hover:bg-[#0a9aaf]">
          <UserPlus class="w-4 h-4" /> Neuer Kontakt
        </button>
      </div>
    </div>

    <!-- Filter-Zeile -->
    <div class="flex gap-3 mb-4">
      <div class="relative flex-1 max-w-xs">
        <Search class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
        <input v-model="search" @input="applyFilters" placeholder="Firma, Name, E-Mail…" class="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30" />
      </div>
      <select v-model="filterTyp" @change="applyFilters" class="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
        <option value="">Alle Typen</option>
        <option>PE</option>
        <option>Systemhausgruppe</option>
        <option>Strategisch</option>
        <option>Sonstige</option>
      </select>
      <input v-model="filterPlz" @input="applyFilters" placeholder="PLZ-Prefix" class="w-28 border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none" />
      <span class="text-sm text-gray-400 self-center">{{ filtered.length }} Kontakte</span>
    </div>

    <!-- Listenansicht -->
    <div v-if="view === 'list'" class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-400 text-sm">Lade Kontakte…</div>
      <div v-else-if="!filtered.length" class="p-8 text-center text-gray-400 text-sm">Keine Kontakte gefunden.</div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Firma</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Name</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Typ</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">PLZ / Ort</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Sucht / Bietet</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Aktionen</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="k in filtered" :key="k.RowKey" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm font-medium text-gray-800">{{ k.firma }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ k.name }}</td>
            <td class="px-4 py-3">
              <span :class="typClass(k.typ)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ k.typ }}</span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-500">{{ k.plz }} {{ k.ort }}</td>
            <td class="px-4 py-3 text-xs text-gray-500 max-w-xs">
              <div v-if="k.sucht" class="truncate">Sucht: {{ k.sucht }}</div>
              <div v-if="k.bietet" class="truncate">Bietet: {{ k.bietet }}</div>
            </td>
            <td class="px-4 py-3">
              <a v-if="k.email" :href="`mailto:${k.email}`" class="inline-flex items-center gap-1 text-xs text-[#097e92] hover:text-[#0a9aaf] mr-2">
                <Mail class="w-3.5 h-3.5" /> Anschreiben
              </a>
              <button @click="openEdit(k)" class="text-xs text-gray-400 hover:text-gray-600">
                <Pencil class="w-3.5 h-3.5" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Kartenansicht (DACH) -->
    <div v-else>
      <div class="bg-white rounded-xl border border-gray-100 p-4 mb-3 flex items-center justify-between text-sm">
        <div class="flex items-center gap-4">
          <span class="text-gray-600"><strong>{{ mapData.kontakte?.length || 0 }}</strong> mit Standort</span>
          <span class="text-gray-400">·</span>
          <span class="text-gray-500">{{ mapData.withoutCoords || 0 }} ohne PLZ</span>
        </div>
        <!-- Legende -->
        <div class="flex items-center gap-3 text-xs">
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" style="background:#097e92"></span>Strategisch</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" style="background:#3498db"></span>Systemhausgruppe</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" style="background:#a855f7"></span>PE</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" style="background:#c8b274"></span>Verkäufer-Interesse</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" style="background:#64748b"></span>Sonstige</span>
        </div>
      </div>
      <KundenMap :kontakte="mapData.kontakte || []" />
    </div>

    <!-- Import Modal -->
    <div v-if="showImport" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-900">Kontakte importieren</h3>
          <button @click="showImport = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <p class="text-sm text-gray-500 mb-4">JSON-Array mit Kontakten einfügen oder CSV-Datei hochladen:</p>
        <textarea v-model="importJson" rows="6" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 resize-none" placeholder='[{"firma":"Musterfirma","name":"Max Muster","email":"m@example.de","typ":"PE","plz":"80000","ort":"München"}]'></textarea>
        <div class="flex gap-3 mt-4">
          <button @click="showImport = false" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl hover:bg-gray-50">Abbrechen</button>
          <button @click="doImport" :disabled="importing" class="flex-1 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium disabled:opacity-50">
            {{ importing ? 'Importiere…' : 'Importieren' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Neuer Kontakt / Bearbeiten Modal -->
    <div v-if="showNewModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-lg">
        <div class="flex items-center justify-between mb-5">
          <h3 class="font-bold text-gray-900">{{ editKontakt ? 'Kontakt bearbeiten' : 'Neuer Kontakt' }}</h3>
          <button @click="closeModal"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2"><label class="field-label">Firma</label><input v-model="form.firma" class="input" /></div>
          <div><label class="field-label">Name</label><input v-model="form.name" class="input" /></div>
          <div><label class="field-label">Typ</label>
            <select v-model="form.typ" class="input">
              <option>PE</option><option>Systemhausgruppe</option><option>Strategisch</option><option>Sonstige</option>
            </select>
          </div>
          <div><label class="field-label">E-Mail</label><input v-model="form.email" type="email" class="input" /></div>
          <div><label class="field-label">Telefon</label><input v-model="form.telefon" class="input" /></div>
          <div><label class="field-label">PLZ</label><input v-model="form.plz" class="input" /></div>
          <div><label class="field-label">Ort</label><input v-model="form.ort" class="input" /></div>
          <div class="col-span-2"><label class="field-label">Sucht</label><input v-model="form.sucht" class="input" /></div>
          <div class="col-span-2"><label class="field-label">Bietet</label><input v-model="form.bietet" class="input" /></div>
          <div class="col-span-2"><label class="field-label">Kommentar</label><textarea v-model="form.kommentar" rows="2" class="input resize-none"></textarea></div>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="closeModal" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl hover:bg-gray-50">Abbrechen</button>
          <button @click="saveKontakt" :disabled="saving" class="flex-1 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium disabled:opacity-50">
            {{ saving ? 'Speichern…' : 'Speichern' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { Map, List, Download, Upload, UserPlus, Search, Mail, Pencil, X } from '@lucide/vue'
import { getKontakte, createKontakt, updateKontakt, importKontakte, exportKontakte } from '../../api.js'
import { authFetch } from '../../api.js'
import KundenMap from '../KundenMap.vue'

const allKontakte = ref([])
const filtered = ref([])
const mapData = ref({ kontakte: [], withoutCoords: 0 })
const loading = ref(true)
const view = ref('list')
const search = ref('')
const filterTyp = ref('')
const filterPlz = ref('')
const showImport = ref(false)
const showNewModal = ref(false)
const editKontakt = ref(null)
const importJson = ref('')
const importing = ref(false)
const saving = ref(false)
const form = ref({ firma: '', name: '', email: '', telefon: '', plz: '', ort: '', typ: 'Sonstige', sucht: '', bietet: '', kommentar: '' })

onMounted(async () => {
  try { allKontakte.value = await getKontakte(); filtered.value = [...allKontakte.value] }
  finally { loading.value = false }
})

function applyFilters() {
  let r = [...allKontakte.value]
  if (search.value) {
    const q = search.value.toLowerCase()
    r = r.filter(k => (k.firma+k.name+k.email).toLowerCase().includes(q))
  }
  if (filterTyp.value) r = r.filter(k => k.typ === filterTyp.value)
  if (filterPlz.value) r = r.filter(k => String(k.plz||'').startsWith(filterPlz.value))
  filtered.value = r
}

function typClass(t) {
  if (t === 'PE') return 'bg-purple-100 text-purple-700'
  if (t === 'Systemhausgruppe') return 'bg-blue-100 text-blue-700'
  if (t === 'Strategisch') return 'bg-[#097e92]/10 text-[#097e92]'
  return 'bg-gray-100 text-gray-600'
}

async function toggleView() {
  view.value = view.value === 'list' ? 'map' : 'list'
  if (view.value === 'map' && !mapData.value.kontakte.length) {
    try {
      mapData.value = await authFetch('/kontakte/locations')
    } catch { mapData.value = { kontakte: [], withoutCoords: 0 } }
  }
}

async function exportCsv() {
  try {
    const csv = await exportKontakte()
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'kontakte.csv'; a.click()
    URL.revokeObjectURL(url)
  } catch {
    alert('Export fehlgeschlagen')
  }
}

async function doImport() {
  importing.value = true
  try {
    const items = JSON.parse(importJson.value)
    const result = await importKontakte({ items })
    allKontakte.value = await getKontakte()
    applyFilters()
    showImport.value = false
    importJson.value = ''
    alert(`${result.imported} Kontakte importiert.`)
  } catch { alert('Import fehlgeschlagen – bitte JSON prüfen.') }
  finally { importing.value = false }
}

function openEdit(k) { editKontakt.value = k; form.value = { ...k }; showNewModal.value = true }
function closeModal() { showNewModal.value = false; editKontakt.value = null; form.value = { firma:'',name:'',email:'',telefon:'',plz:'',ort:'',typ:'Sonstige',sucht:'',bietet:'',kommentar:'' } }

async function saveKontakt() {
  saving.value = true
  try {
    if (editKontakt.value) {
      await updateKontakt(editKontakt.value.RowKey, form.value)
    } else {
      await createKontakt(form.value)
    }
    allKontakte.value = await getKontakte()
    applyFilters()
    closeModal()
  } finally { saving.value = false }
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]; }
.field-label { @apply block text-xs font-medium text-gray-600 mb-1; }
</style>
