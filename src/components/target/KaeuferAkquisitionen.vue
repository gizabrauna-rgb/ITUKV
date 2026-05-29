<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Meine Akquisitionen</h2>
        <p class="text-sm text-gray-500 mt-1">
          Hier verwaltest du mehrere Akquisitionen unter einem Mandate. Pro Akquisition eigene Suchkriterien, Notizen + Status.
        </p>
      </div>
      <button @click="openNew" class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700">
        <Plus class="w-4 h-4" /> Neue Akquisition
      </button>
    </div>

    <div v-if="!akquisitionen.length" class="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-10 text-center">
      <Target class="w-10 h-10 text-gray-300 mx-auto mb-3" />
      <h3 class="font-semibold text-gray-700">Noch keine Akquisition angelegt</h3>
      <p class="text-sm text-gray-500 mt-1">Lege deine erste Such-Konfiguration an — z.B. „IT-Systemhäuser DACH" oder „SaaS 2–5 Mio".</p>
      <button @click="openNew" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700">
        Erste Akquisition anlegen
      </button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="(akq, i) in akquisitionen" :key="akq.id"
        class="bg-white rounded-2xl border border-gray-100 p-5 hover:border-blue-200 transition-colors">
        <div class="flex items-start justify-between gap-2 mb-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="font-bold text-gray-900 truncate">{{ akq.name }}</h3>
              <span :class="['text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase',
                statusClass(akq.status)]">{{ akq.status }}</span>
            </div>
            <p class="text-xs text-gray-500">Angelegt {{ formatDate(akq.createdAt) }}</p>
          </div>
          <div class="flex gap-1 flex-shrink-0">
            <button @click="openEdit(akq)" class="p-1.5 hover:bg-gray-50 rounded text-gray-500" title="Bearbeiten">
              <Pencil class="w-4 h-4" />
            </button>
            <button @click="askDelete(i)" class="p-1.5 hover:bg-red-50 rounded text-red-500" title="Löschen">
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs mb-3">
          <div v-if="akq.branche" class="bg-gray-50 rounded-lg px-2 py-1.5">
            <div class="text-[10px] text-gray-400">Branche</div>
            <div class="text-gray-800 font-medium truncate">{{ akq.branche }}</div>
          </div>
          <div v-if="akq.region" class="bg-gray-50 rounded-lg px-2 py-1.5">
            <div class="text-[10px] text-gray-400">Region</div>
            <div class="text-gray-800 font-medium truncate">{{ akq.region }}</div>
          </div>
          <div v-if="akq.mitarbeiter" class="bg-gray-50 rounded-lg px-2 py-1.5">
            <div class="text-[10px] text-gray-400">Mitarbeiter</div>
            <div class="text-gray-800 font-medium truncate">{{ akq.mitarbeiter }}</div>
          </div>
          <div v-if="akq.umsatz" class="bg-gray-50 rounded-lg px-2 py-1.5">
            <div class="text-[10px] text-gray-400">Umsatz</div>
            <div class="text-gray-800 font-medium truncate">{{ akq.umsatz }}</div>
          </div>
          <div v-if="akq.maxKaufpreis" class="bg-gray-50 rounded-lg px-2 py-1.5">
            <div class="text-[10px] text-gray-400">Max. Kaufpreis</div>
            <div class="text-gray-800 font-medium truncate">{{ akq.maxKaufpreis }}</div>
          </div>
          <div v-if="akq.notizen" class="col-span-2 bg-amber-50 border border-amber-100 rounded-lg px-2 py-1.5">
            <div class="text-[10px] text-amber-700">Notizen</div>
            <div class="text-amber-900 truncate">{{ akq.notizen }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal: Neue / Edit -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4 py-8 overflow-y-auto">
      <div class="bg-white rounded-2xl w-full max-w-2xl shadow-2xl">
        <header class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="font-bold text-gray-900">{{ editingIdx !== null ? 'Akquisition bearbeiten' : 'Neue Akquisition' }}</h3>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600"><X class="w-5 h-5" /></button>
        </header>
        <div class="p-5 grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-600 mb-1">Bezeichnung / Name *</label>
            <input v-model="form.name" placeholder="z.B. IT-Systemhäuser DACH" class="input" />
            <p class="text-[11px] text-gray-400 mt-1">Klare Bezeichnung, damit du die Akquisitionen unterscheidest.</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Status</label>
            <select v-model="form.status" class="input">
              <option>aktiv</option>
              <option>pausiert</option>
              <option>geschlossen</option>
              <option>abgebrochen</option>
            </select>
          </div>
          <div></div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Branche(n)</label>
            <input v-model="form.branche" placeholder="z.B. IT-Dienstleister, SaaS" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Region</label>
            <input v-model="form.region" placeholder="z.B. DACH, Bayern, …" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Mitarbeiter-Größe</label>
            <input v-model="form.mitarbeiter" placeholder="z.B. 10–50 MA" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Umsatz-Größe</label>
            <input v-model="form.umsatz" placeholder="z.B. 2–5 Mio. €" class="input" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-600 mb-1">Max. Kaufpreis</label>
            <input v-model="form.maxKaufpreis" placeholder="z.B. bis 3 Mio. €" class="input" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-600 mb-1">Notizen / Besonderheiten</label>
            <textarea v-model="form.notizen" rows="3" class="input resize-none"
              placeholder='z.B. „Bevorzugt Bestand mit Wartungsverträgen", „Standort egal", „Geschäftsführer soll bleiben" …'></textarea>
          </div>
        </div>
        <footer class="px-5 py-3 border-t border-gray-100 flex items-center justify-end gap-2">
          <button @click="closeModal" class="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">Abbrechen</button>
          <button @click="saveAkquisition" :disabled="!form.name.trim() || saving"
            class="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {{ saving ? 'Speichere…' : (editingIdx !== null ? 'Änderungen speichern' : 'Akquisition anlegen') }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Plus, X, Target, Pencil, Trash2 } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: { type: String, required: true } })

const akquisitionen = ref([])
const showModal = ref(false)
const editingIdx = ref(null)
const saving = ref(false)
const form = ref({ name: '', status: 'aktiv', branche: '', region: '', mitarbeiter: '', umsatz: '', maxKaufpreis: '', notizen: '' })

async function load() {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    try { akquisitionen.value = JSON.parse(t.akquisitionenJson || '[]') } catch { akquisitionen.value = [] }
    if (!Array.isArray(akquisitionen.value)) akquisitionen.value = []
  } catch {}
}
onMounted(load)

function openNew() {
  editingIdx.value = null
  form.value = { name: '', status: 'aktiv', branche: '', region: '', mitarbeiter: '', umsatz: '', maxKaufpreis: '', notizen: '' }
  showModal.value = true
}
function openEdit(akq) {
  editingIdx.value = akquisitionen.value.findIndex(a => a.id === akq.id)
  form.value = { ...akq }
  showModal.value = true
}
function closeModal() { showModal.value = false; editingIdx.value = null }

async function saveAkquisition() {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    const list = [...akquisitionen.value]
    if (editingIdx.value !== null) {
      list[editingIdx.value] = { ...list[editingIdx.value], ...form.value }
    } else {
      list.push({
        id: 'akq' + Date.now(),
        createdAt: new Date().toISOString(),
        ...form.value,
      })
    }
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, akquisitionenJson: JSON.stringify(list) }})
    akquisitionen.value = list
    closeModal()
  } finally { saving.value = false }
}

async function askDelete(i) {
  const a = akquisitionen.value[i]
  if (!a) return
  if (!confirm(`Akquisition „${a.name}" wirklich löschen? Das lässt sich nicht rückgängig machen.`)) return
  const list = akquisitionen.value.filter((_, idx) => idx !== i)
  await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, akquisitionenJson: JSON.stringify(list) }})
  akquisitionen.value = list
}

function statusClass(s) {
  if (s === 'aktiv') return 'bg-green-100 text-green-700'
  if (s === 'pausiert') return 'bg-amber-100 text-amber-700'
  if (s === 'geschlossen') return 'bg-blue-100 text-blue-700'
  if (s === 'abgebrochen') return 'bg-gray-200 text-gray-600'
  return 'bg-gray-100 text-gray-500'
}
function formatDate(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleDateString('de-DE') } catch { return '' }
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300; }
</style>
