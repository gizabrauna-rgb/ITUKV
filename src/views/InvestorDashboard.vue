<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Topbar -->
    <header class="bg-[#161e2a] text-white px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <img src="/Logo_mibeca_Start.png" alt="mibeca" class="h-10 w-auto" />
        <div>
          <span class="font-bold text-sm">ITUKV Dashboard</span>
          <span class="text-gray-400 text-xs ml-2">Investor-Portal</span>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-sm text-gray-300">{{ userName }}</span>
        <button @click="$emit('logout')" class="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white">
          <LogOut class="w-4 h-4" /> Abmelden
        </button>
      </div>
    </header>

    <div class="max-w-4xl mx-auto px-6 py-8">
      <!-- Tab Nav -->
      <div class="flex gap-1 mb-6 bg-white rounded-xl border border-gray-100 p-1 w-fit">
        <button v-for="item in navItems" :key="item.tab" @click="tab = item.tab"
          :class="['flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors', tab === item.tab ? 'bg-[#097e92] text-white' : 'text-gray-600 hover:bg-gray-50']">
          <component :is="item.icon" class="w-4 h-4" />
          {{ item.label }}
        </button>
      </div>

      <!-- Tab: Ausschreibungen -->
      <div v-if="tab === 'ausschreibungen'">
        <h2 class="text-xl font-bold text-gray-900 mb-2">Verfügbare IT-Unternehmen</h2>
        <p class="text-sm text-gray-500 mb-5">Anonymisierte Kurzprofile. Nach NDA-Unterzeichnung erhalten Sie das vollständige Exposé.</p>

        <div v-if="loading" class="text-center text-gray-400 text-sm py-10">Lade Ausschreibungen…</div>
        <div v-else-if="!ausschreibungen.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400 text-sm">
          Aktuell keine aktiven Ausschreibungen.
        </div>
        <div v-else class="space-y-4">
          <div v-for="a in ausschreibungen" :key="a.RowKey" class="bg-white rounded-xl border border-gray-100 p-5 hover:border-[#097e92]/30 transition-all">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-mono text-xs bg-[#097e92]/10 text-[#097e92] px-2 py-0.5 rounded font-semibold">{{ a.mbNr }}</span>
                  <span class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">verfügbar</span>
                </div>
                <h3 class="font-semibold text-gray-900">{{ a.titel }}</h3>
                <p class="text-sm text-gray-500 mt-0.5">{{ a.region }} · {{ a.mitarbeiter }} Mitarbeiter · {{ a.umsatz }}</p>
                <p class="text-sm text-gray-500 mt-2 max-w-xl">{{ a.kurzprofil }}</p>
              </div>
              <div class="flex-shrink-0">
                <!-- Status-abhängiger Button -->
                <button v-if="!getNdaStatus(a.RowKey)" @click="openNdaModal(a)"
                  class="flex items-center gap-2 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf] transition-colors">
                  <FileText class="w-4 h-4" /> Exposé anfordern
                </button>
                <div v-else-if="getNdaStatus(a.RowKey) === 'gesendet'" class="flex items-center gap-2 px-4 py-2 bg-yellow-50 text-yellow-700 rounded-xl text-sm border border-yellow-200">
                  <Clock class="w-4 h-4" /> NDA ausstehend
                </div>
                <button v-else-if="getNdaStatus(a.RowKey) === 'unterzeichnet'" @click="downloadExpose(a)"
                  class="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-700 transition-colors">
                  <Download class="w-4 h-4" /> Exposé herunterladen
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Meine Prozesse -->
      <div v-else-if="tab === 'prozesse'">
        <h2 class="text-xl font-bold text-gray-900 mb-5">Meine Prozesse</h2>
        <div v-if="!meineInteressenten.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400 text-sm">
          <GitBranch class="w-10 h-10 mx-auto mb-3 text-gray-200" />
          Noch keine aktiven Prozesse. Fordern Sie ein Exposé an, um zu starten.
        </div>
        <div v-else class="space-y-4">
          <div v-for="i in meineInteressenten" :key="i.RowKey" class="bg-white rounded-xl border border-gray-100 p-5">
            <div class="flex items-center justify-between mb-3">
              <div>
                <span class="font-mono text-xs bg-[#097e92]/10 text-[#097e92] px-2 py-0.5 rounded font-semibold mr-2">{{ i.mbNr || '—' }}</span>
                <span class="font-medium text-gray-800">Verkaufsprozess</span>
              </div>
              <span :class="ndaClass(i.ndaStatus)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ ndaLabel(i.ndaStatus) }}</span>
            </div>
            <!-- Status-Timeline -->
            <div class="flex items-center gap-0 mb-3 overflow-x-auto">
              <div v-for="(step, idx) in pipeline" :key="step.status" class="flex items-center">
                <div :class="['flex flex-col items-center px-2', isActiveOrPast(i.pipelineStatus, step.status) ? 'text-[#097e92]' : 'text-gray-300']">
                  <div :class="['w-3 h-3 rounded-full', isActive(i.pipelineStatus, step.status) ? 'bg-[#097e92] ring-2 ring-[#097e92]/30' : isActiveOrPast(i.pipelineStatus, step.status) ? 'bg-[#097e92]' : 'bg-gray-200']"></div>
                  <span class="text-xs mt-1 whitespace-nowrap">{{ step.label }}</span>
                </div>
                <div v-if="idx < pipeline.length - 1" :class="['h-0.5 w-6 flex-shrink-0', isActiveOrPast(i.pipelineStatus, pipeline[idx+1].status) ? 'bg-[#097e92]' : 'bg-gray-200']"></div>
              </div>
            </div>
            <!-- Notizen -->
            <div>
              <label class="text-xs text-gray-400 mb-1 block">Meine Notizen</label>
              <textarea v-model="i.notizen" @blur="saveNotizen(i)" rows="2" class="w-full border border-gray-100 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[#097e92]/30 resize-none bg-gray-50"></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Checkliste -->
      <div v-else-if="tab === 'checkliste'">
        <h2 class="text-xl font-bold text-gray-900 mb-5">Meine Checkliste</h2>
        <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <ul class="divide-y divide-gray-50">
            <li v-for="item in checkliste" :key="item.id"
              class="flex items-center gap-4 px-5 py-3 hover:bg-gray-50 cursor-pointer"
              @click="item.done = !item.done">
              <div :class="['w-5 h-5 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors', item.done ? 'bg-[#097e92] border-[#097e92]' : 'border-gray-300 hover:border-[#097e92]']">
                <Check v-if="item.done" class="w-3 h-3 text-white" />
              </div>
              <div class="flex-1">
                <span :class="['text-sm', item.done ? 'line-through text-gray-400' : 'text-gray-700']">{{ item.label }}</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- NDA Modal -->
    <div v-if="ndaModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl w-full max-w-md p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-900">Vertraulichkeitsvereinbarung (NDA)</h3>
          <button @click="ndaModal = null"><X class="w-5 h-5 text-gray-400" /></button>
        </div>

        <div v-if="!ndaSent">
          <!-- NDA Text -->
          <div class="bg-gray-50 rounded-xl p-4 mb-4 text-xs text-gray-600 h-40 overflow-y-auto leading-relaxed">
            <p class="font-semibold mb-2">Vertraulichkeitsvereinbarung</p>
            <p>Hiermit verpflichtet sich der Unterzeichner, alle im Rahmen dieses M&A-Prozesses erhaltenen Informationen über das Zielunternehmen ({{ ndaModal.mbNr }}) streng vertraulich zu behandeln. Die Informationen dürfen weder an Dritte weitergegeben noch für andere Zwecke verwendet werden als für die Prüfung eines möglichen Erwerbs. Diese Vereinbarung gilt für einen Zeitraum von 24 Monaten ab Unterzeichnung.</p>
            <p class="mt-2">Vermittler: mibeca GmbH · M&A Beratung für IT-Unternehmen</p>
          </div>
          <!-- Kontaktdaten -->
          <div class="grid grid-cols-2 gap-3 mb-4">
            <div><label class="text-xs text-gray-500 mb-1 block">Ihr Name *</label><input v-model="ndaForm.name" class="input" /></div>
            <div><label class="text-xs text-gray-500 mb-1 block">Firma *</label><input v-model="ndaForm.firma" class="input" /></div>
            <div class="col-span-2"><label class="text-xs text-gray-500 mb-1 block">E-Mail *</label><input v-model="ndaForm.email" type="email" class="input" /></div>
          </div>
          <label class="flex items-start gap-2 mb-4 cursor-pointer">
            <input type="checkbox" v-model="ndaAccepted" class="mt-0.5 rounded" />
            <span class="text-xs text-gray-600">Ich akzeptiere die Vertraulichkeitsvereinbarung und stimme der Verarbeitung meiner Daten zu.</span>
          </label>
          <div class="flex gap-3">
            <button @click="ndaModal = null" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
            <button @click="sendNda" :disabled="!ndaAccepted || sendingNda"
              class="flex-1 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium disabled:opacity-50">
              {{ sendingNda ? 'Sende…' : 'NDA senden & Exposé anfordern' }}
            </button>
          </div>
        </div>

        <div v-else class="text-center py-4">
          <CheckCircle class="w-12 h-12 text-green-500 mx-auto mb-3" />
          <h4 class="font-semibold text-gray-900 mb-2">NDA erfolgreich gesendet</h4>
          <p class="text-sm text-gray-500">Sie erhalten in Kürze eine E-Mail mit dem NDA-Dokument zur Unterzeichnung. Nach Ihrer Unterschrift wird das Exposé für Sie freigeschaltet.</p>
          <button @click="ndaModal = null; ndaSent = false" class="mt-4 px-5 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium">Verstanden</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  Building2, LogOut, Megaphone, GitBranch, CheckSquare,
  FileText, Clock, Download, Check, CheckCircle, X
} from '@lucide/vue'
import { getAusschreibungen, requestExpose, getInteressenten } from '../api.js'
import { toast } from '../composables/useToast.js'
import { authFetch } from '../api.js'

const props = defineProps({ userName: String })
const emit = defineEmits(['logout'])

const tab = ref('ausschreibungen')
const ausschreibungen = ref([])
const meineInteressenten = ref([])
const ndaStatusMap = ref({})
const loading = ref(true)
const ndaModal = ref(null)
const ndaAccepted = ref(false)
const sendingNda = ref(false)
const ndaSent = ref(false)
const ndaForm = ref({ name: '', firma: '', email: '' })

const navItems = [
  { tab: 'ausschreibungen', label: 'Ausschreibungen', icon: Megaphone },
  { tab: 'prozesse', label: 'Meine Prozesse', icon: GitBranch },
  { tab: 'checkliste', label: 'Checkliste', icon: CheckSquare },
]

const pipeline = [
  { status: 'nda', label: 'NDA' },
  { status: 'nda_unterzeichnet', label: 'NDA ✓' },
  { status: 'erstgespraech', label: 'Erstgespräch' },
  { status: 'gebot', label: 'Gebot' },
  { status: 'zusage', label: 'Zusage' },
]

const pipelineOrder = pipeline.map(p => p.status)

const checkliste = ref([
  { id: '1', label: 'NDA unterzeichnet', done: false },
  { id: '2', label: 'Exposé erhalten und geprüft', done: false },
  { id: '3', label: 'Element-Raum / Datenraum geöffnet', done: false },
  { id: '4', label: 'Erstgespräch vereinbart', done: false },
  { id: '5', label: 'Gebot abgegeben', done: false },
])

onMounted(async () => {
  try {
    ausschreibungen.value = await getAusschreibungen()
  } finally { loading.value = false }
})

function getNdaStatus(ausschrId) {
  return ndaStatusMap.value[ausschrId] || null
}

function isActive(current, step) { return current === step }
function isActiveOrPast(current, step) {
  const ci = pipelineOrder.indexOf(current)
  const si = pipelineOrder.indexOf(step)
  return ci >= si && ci >= 0
}

function ndaClass(s) {
  if (s === 'unterzeichnet') return 'bg-green-100 text-green-700'
  if (s === 'gesendet') return 'bg-yellow-100 text-yellow-700'
  return 'bg-gray-100 text-gray-500'
}
function ndaLabel(s) {
  return { unterzeichnet:'NDA unterzeichnet', gesendet:'NDA gesendet' }[s] || 'Offen'
}

function openNdaModal(a) {
  ndaModal.value = a
  ndaAccepted.value = false
  ndaSent.value = false
  ndaForm.value = { name: sessionStorage.getItem('userName') || '', firma: '', email: '' }
}

async function sendNda() {
  sendingNda.value = true
  try {
    await requestExpose(ndaModal.value.RowKey, ndaForm.value)
    ndaStatusMap.value[ndaModal.value.RowKey] = 'gesendet'
    ndaSent.value = true
  } catch { toast.error('Fehler beim Senden des NDA. Bitte erneut versuchen.') }
  finally { sendingNda.value = false }
}

async function downloadExpose(a) {
  try {
    const docs = await authFetch(`/targets/${a.targetId}/dokumente?ordner=Expos%C3%A9`)
    if (docs.length) {
      const r = await authFetch(`/targets/${a.targetId}/dokumente/${docs[0].RowKey}/download`)
      window.open(r.url, '_blank')
    } else {
      toast.error('Exposé noch nicht hinterlegt. Bitte kontaktieren Sie mibeca.')
    }
  } catch { toast.error('Fehler beim Abrufen des Exposés.') }
}

async function saveNotizen(i) {
  await authFetch(`/targets/${i.targetId}/interessenten/${i.RowKey}`, { method: 'PATCH', data: { notizen: i.notizen } })
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]; }
</style>
