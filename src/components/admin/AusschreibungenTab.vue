<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Ausschreibungen</h2>
      <button @click="showModal = true" class="flex items-center gap-2 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8]">
        <Plus class="w-4 h-4" /> Neue Ausschreibung
      </button>
    </div>

    <div v-if="loading" class="text-center text-gray-400 text-sm py-10">Lade Ausschreibungen…</div>
    <div v-else-if="!items.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400 text-sm">Noch keine Ausschreibungen vorhanden.</div>

    <div v-else class="space-y-4">
      <div v-for="a in items" :key="a.RowKey" class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="font-mono text-xs bg-blue-50 text-blue-800 px-2 py-0.5 rounded">{{ a.mbNr }}</span>
              <span :class="a.status === 'aktiv' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'" class="text-xs font-medium px-2 py-0.5 rounded-full">{{ a.status }}</span>
            </div>
            <h3 class="font-semibold text-gray-900">{{ a.titel }}</h3>
            <p class="text-sm text-gray-500 mt-0.5">{{ a.region }} · {{ a.mitarbeiter }} Mitarbeiter · {{ a.umsatz }}</p>
            <p class="text-sm text-gray-500 mt-1 max-w-xl">{{ a.kurzprofil }}</p>
          </div>
          <div class="flex gap-2">
            <button @click="openDetail(a)" class="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 rounded-lg text-xs hover:bg-gray-50">
              <Users class="w-3.5 h-3.5" /> Interessenten
            </button>
            <select v-model="a.status" @change="updateStatus(a)" class="text-xs border border-gray-200 rounded-lg px-2 py-1.5">
              <option value="aktiv">Aktiv</option>
              <option value="pausiert">Pausiert</option>
              <option value="abgeschlossen">Abgeschlossen</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Interessenten-Panel -->
    <div v-if="detailAusschr" class="fixed inset-0 bg-black/40 flex items-start justify-end z-50" @click.self="detailAusschr = null">
      <div class="bg-white h-full w-full max-w-md shadow-2xl overflow-y-auto">
        <div class="flex items-center justify-between p-5 border-b border-gray-100">
          <h3 class="font-bold text-gray-900">Interessenten: {{ detailAusschr.mbNr }}</h3>
          <button @click="detailAusschr = null"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="p-5">
          <div v-if="!detailInteressenten.length" class="text-sm text-gray-400">Noch keine Interessenten registriert.</div>
          <div v-for="i in detailInteressenten" :key="i.RowKey" class="border border-gray-100 rounded-xl p-4 mb-3">
            <div class="font-medium text-sm text-gray-800">{{ i.firma || i.name }}</div>
            <div class="text-xs text-gray-500">{{ i.email }} · {{ i.plz }} {{ i.ort }}</div>
            <div class="flex items-center gap-2 mt-2">
              <span :class="ndaClass(i.ndaStatus)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ ndaLabel(i.ndaStatus) }}</span>
              <span v-if="i.veto" class="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-medium">VETO</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Neue Ausschreibung Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-lg">
        <div class="flex items-center justify-between mb-5">
          <h3 class="font-bold text-gray-900">Neue Ausschreibung</h3>
          <button @click="showModal = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="field-label">Target *</label>
              <select v-model="form.targetId" @change="prefillFromTarget" class="input">
                <option value="">— auswählen —</option>
                <option v-for="t in targets" :key="t.RowKey" :value="t.RowKey">{{ t.mbNr }} · {{ t.verkaueferName }}</option>
              </select>
            </div>
            <div>
              <label class="field-label">mb-Nummer</label>
              <input v-model="form.mbNr" class="input" />
            </div>
          </div>
          <div><label class="field-label">Titel der Ausschreibung</label><input v-model="form.titel" placeholder="IT-Systemhaus · Managed Services" class="input" /></div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="field-label">Region</label><input v-model="form.region" class="input" /></div>
            <div><label class="field-label">Branche</label><input v-model="form.branche" class="input" /></div>
            <div><label class="field-label">Mitarbeiter</label><input v-model="form.mitarbeiter" class="input" /></div>
            <div><label class="field-label">Umsatz (ca.)</label><input v-model="form.umsatz" class="input" /></div>
          </div>
          <div><label class="field-label">Kurzprofil (anonymisiert)</label><textarea v-model="form.kurzprofil" rows="3" class="input resize-none" placeholder="Anonymisierte Beschreibung für Investoren…"></textarea></div>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="showModal = false" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl hover:bg-gray-50">Abbrechen</button>
          <button @click="create" :disabled="saving" class="flex-1 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium disabled:opacity-50">
            {{ saving ? 'Erstelle…' : 'Ausschreibung erstellen' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Users, X } from '@lucide/vue'
import { getAusschreibungen, createAusschreibung, updateAusschreibung, getTargets, getInteressenten } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const items = ref([])
const targets = ref([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const detailAusschr = ref(null)
const detailInteressenten = ref([])
const form = ref({ targetId: '', mbNr: '', titel: '', region: '', branche: '', mitarbeiter: '', umsatz: '', kurzprofil: '' })

onMounted(async () => {
  try { targets.value = await getTargets() } catch (e) { console.error('getTargets failed', e) }
  try { items.value = await getAusschreibungen() } catch (e) { items.value = [] }
  loading.value = false
})

function prefillFromTarget() {
  const t = targets.value.find(t => t.RowKey === form.value.targetId)
  if (t) { form.value.mbNr = t.mbNr; form.value.region = t.region; form.value.mitarbeiter = t.mitarbeiter; form.value.umsatz = t.umsatz; form.value.branche = t.branche }
}

async function create() {
  saving.value = true
  try {
    const a = await createAusschreibung(form.value)
    items.value.push(a)
    showModal.value = false
    form.value = { targetId: '', mbNr: '', titel: '', region: '', branche: '', mitarbeiter: '', umsatz: '', kurzprofil: '' }
  } catch (e) { toast.error('Anlegen fehlgeschlagen') }
  finally { saving.value = false }
}

async function updateStatus(a) {
  try { await updateAusschreibung(a.RowKey, { status: a.status }) } catch (e) { console.error(e) }
}

async function openDetail(a) {
  detailAusschr.value = a
  detailInteressenten.value = await getInteressenten(a.targetId || a.RowKey)
}

function ndaClass(s) {
  if (s === 'unterzeichnet') return 'bg-green-100 text-green-700'
  if (s === 'gesendet') return 'bg-yellow-100 text-yellow-700'
  if (s === 'abgelehnt') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-500'
}
function ndaLabel(s) {
  const map = { unterzeichnet: 'NDA unterzeichnet', gesendet: 'NDA gesendet', abgelehnt: 'NDA abgelehnt', ausstehend: 'NDA ausstehend' }
  return map[s] || 'NDA ausstehend'
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
.field-label { @apply block text-xs font-medium text-gray-600 mb-1; }
</style>
