<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Interessenten-Pipeline</h2>
      <select v-model="selectedTargetId" @change="loadInteressenten" class="text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#097e92]/30">
        <option value="">— Target auswählen —</option>
        <option v-for="t in targets" :key="t.RowKey" :value="t.RowKey">{{ t.mbNr }} · {{ t.verkaueferName }}</option>
      </select>
    </div>

    <div v-if="!selectedTargetId" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">
      Bitte wähle oben ein Target aus.
    </div>

    <div v-else-if="loading" class="text-center text-gray-400 text-sm py-10">Lade Interessenten…</div>

    <!-- Kanban Board -->
    <div v-else class="flex gap-3 overflow-x-auto pb-4">
      <div
        v-for="col in columns" :key="col.status"
        class="flex-shrink-0 w-56"
        @dragover.prevent
        @drop="onDrop($event, col.status)"
      >
        <div class="flex items-center justify-between mb-2 px-1">
          <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">{{ col.label }}</span>
          <span class="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5">{{ getCol(col.status).length }}</span>
        </div>
        <div class="space-y-2 min-h-20">
          <div
            v-for="i in getCol(col.status)" :key="i.RowKey"
            draggable="true"
            @dragstart="onDragStart($event, i)"
            @click="openDetail(i)"
            class="bg-white rounded-xl border border-gray-100 p-3 cursor-pointer hover:border-[#097e92]/30 hover:shadow-sm transition-all"
          >
            <div class="font-medium text-sm text-gray-800 truncate">{{ i.firma || i.name }}</div>
            <div class="text-xs text-gray-500 mt-0.5">{{ i.name }}</div>
            <div class="text-xs text-gray-400">{{ i.plz }} {{ i.ort }}</div>
            <div class="flex items-center gap-0.5 mt-2">
              <Star v-for="n in 5" :key="n" :class="n <= i.rating ? 'text-[#c8b274] fill-[#c8b274]' : 'text-gray-200'" class="w-3 h-3" />
            </div>
            <div v-if="i.veto" class="mt-1">
              <span class="text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded font-medium">VETO</span>
            </div>
            <!-- NDA Badge -->
            <span :class="ndaClass(i.ndaStatus)" class="text-xs px-1.5 py-0.5 rounded mt-1 inline-block">{{ ndaLabel(i.ndaStatus) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Panel -->
    <div v-if="detailItem" class="fixed inset-0 bg-black/40 flex items-start justify-end z-50" @click.self="detailItem = null">
      <div class="bg-white h-full w-full max-w-md shadow-2xl overflow-y-auto">
        <div class="flex items-center justify-between p-5 border-b border-gray-100">
          <div>
            <div class="font-bold text-gray-900">{{ detailItem.firma || detailItem.name }}</div>
            <div class="text-sm text-gray-500">{{ detailItem.email }}</div>
          </div>
          <button @click="detailItem = null"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="p-5 space-y-4">
          <!-- Kontakt -->
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-gray-400">Name</span><div class="font-medium">{{ detailItem.name }}</div></div>
            <div><span class="text-gray-400">Telefon</span><div class="font-medium">{{ detailItem.telefon || '—' }}</div></div>
            <div><span class="text-gray-400">PLZ / Ort</span><div class="font-medium">{{ detailItem.plz }} {{ detailItem.ort }}</div></div>
            <div><span class="text-gray-400">NDA</span><div><span :class="ndaClass(detailItem.ndaStatus)" class="text-xs px-2 py-0.5 rounded font-medium">{{ ndaLabel(detailItem.ndaStatus) }}</span></div></div>
            <div><span class="text-gray-400">Ansprache</span><div class="font-medium">{{ detailItem.ansprache }}</div></div>
            <div><span class="text-gray-400">Gebot</span><div class="font-medium">{{ detailItem.aktuellesGebot || '—' }}</div></div>
          </div>

          <!-- Pipeline Status -->
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Pipeline-Status</label>
            <select v-model="detailItem.pipelineStatus" @change="saveDetail" class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#097e92]/30">
              <option v-for="col in columns" :key="col.status" :value="col.status">{{ col.label }}</option>
            </select>
          </div>

          <!-- Rating -->
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Bewertung</label>
            <div class="flex gap-1">
              <button v-for="n in 5" :key="n" @click="setRating(n)" class="p-0.5 hover:scale-110 transition-transform">
                <Star :class="n <= detailItem.rating ? 'text-[#c8b274] fill-[#c8b274]' : 'text-gray-300'" class="w-6 h-6" />
              </button>
            </div>
          </div>

          <!-- Gebot -->
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Aktuelles Gebot</label>
            <input v-model="detailItem.aktuellesGebot" @blur="saveDetail" placeholder="z. B. 1,2 Mio. €" class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#097e92]/30" />
          </div>

          <!-- Notizen -->
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Notizen</label>
            <textarea v-model="detailItem.notizen" @blur="saveDetail" rows="3" class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 resize-none"></textarea>
          </div>

          <!-- Freigabe -->
          <div class="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
            <div>
              <div class="text-sm font-medium text-gray-700">Freigabe für Kontakt</div>
              <div class="text-xs text-gray-400">Verkäufer sieht Kontaktdaten</div>
            </div>
            <button @click="toggleFreigabe" :class="detailItem.freigegebenFuerKontakt ? 'bg-green-500' : 'bg-gray-200'" class="relative w-10 h-6 rounded-full transition-colors">
              <span :class="detailItem.freigegebenFuerKontakt ? 'translate-x-5' : 'translate-x-1'" class="absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform block"></span>
            </button>
          </div>

          <!-- VETO -->
          <div v-if="!detailItem.veto">
            <button @click="showVeto = true" class="w-full px-4 py-2 border border-red-200 text-red-600 rounded-xl text-sm font-medium hover:bg-red-50">
              VETO setzen
            </button>
          </div>
          <div v-else class="p-3 bg-red-50 rounded-xl border border-red-100">
            <div class="text-sm font-semibold text-red-700">VETO gesetzt</div>
            <div class="text-xs text-red-500 mt-1">{{ detailItem.vetoBegruendung }}</div>
            <button @click="removeVeto" class="text-xs text-red-400 hover:text-red-600 mt-2">VETO entfernen</button>
          </div>
        </div>
      </div>
    </div>

    <!-- VETO Modal -->
    <div v-if="showVeto" class="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm">
        <h3 class="font-bold text-gray-900 mb-3">VETO setzen</h3>
        <p class="text-sm text-gray-500 mb-3">Begründung für den Verkäufer:</p>
        <textarea v-model="vetoText" rows="3" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 resize-none" placeholder="Begründung…"></textarea>
        <div class="flex gap-3 mt-4">
          <button @click="showVeto = false; vetoText = ''" class="flex-1 px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50">Abbrechen</button>
          <button @click="confirmVeto" class="flex-1 px-4 py-2 bg-red-500 text-white rounded-xl text-sm font-medium hover:bg-red-600">VETO bestätigen</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { X, Star } from '@lucide/vue'
import { getTargets, getInteressenten, updateInteressent } from '../../api.js'

const targets = ref([])
const selectedTargetId = ref('')
const interessenten = ref([])
const loading = ref(false)
const detailItem = ref(null)
const showVeto = ref(false)
const vetoText = ref('')
const dragItem = ref(null)

const columns = [
  { status: 'neu', label: 'Neu' },
  { status: 'nda', label: 'NDA angefordert' },
  { status: 'nda_unterzeichnet', label: 'NDA unterzeichnet' },
  { status: 'erstgespraech', label: 'Erstgespräch' },
  { status: 'gebot', label: 'Gebot' },
  { status: 'zusage', label: 'Zusage' },
  { status: 'absage', label: 'Absage' },
]

onMounted(async () => { targets.value = await getTargets() })

async function loadInteressenten() {
  if (!selectedTargetId.value) return
  loading.value = true
  try { interessenten.value = await getInteressenten(selectedTargetId.value) }
  finally { loading.value = false }
}

function getCol(status) {
  return interessenten.value.filter(i => i.pipelineStatus === status)
}

function ndaClass(s) {
  if (s === 'unterzeichnet') return 'bg-green-100 text-green-700'
  if (s === 'gesendet') return 'bg-yellow-100 text-yellow-700'
  if (s === 'abgelehnt') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-500'
}
function ndaLabel(s) {
  if (s === 'unterzeichnet') return 'NDA ✓'
  if (s === 'gesendet') return 'NDA gesendet'
  if (s === 'abgelehnt') return 'NDA abgelehnt'
  return 'NDA ausstehend'
}

function openDetail(item) { detailItem.value = { ...item } }

async function saveDetail() {
  if (!detailItem.value) return
  const updated = await updateInteressent(selectedTargetId.value, detailItem.value.RowKey, detailItem.value)
  const idx = interessenten.value.findIndex(i => i.RowKey === detailItem.value.RowKey)
  if (idx >= 0) interessenten.value[idx] = updated
}

async function setRating(n) {
  detailItem.value.rating = n
  await saveDetail()
}

async function toggleFreigabe() {
  detailItem.value.freigegebenFuerKontakt = !detailItem.value.freigegebenFuerKontakt
  await saveDetail()
}

async function confirmVeto() {
  detailItem.value.veto = true
  detailItem.value.vetoBegruendung = vetoText.value
  await saveDetail()
  showVeto.value = false
  vetoText.value = ''
}

async function removeVeto() {
  detailItem.value.veto = false
  detailItem.value.vetoBegruendung = ''
  await saveDetail()
}

function onDragStart(e, item) { dragItem.value = item }
async function onDrop(e, status) {
  if (!dragItem.value) return
  dragItem.value.pipelineStatus = status
  await updateInteressent(selectedTargetId.value, dragItem.value.RowKey, { pipelineStatus: status })
  const idx = interessenten.value.findIndex(i => i.RowKey === dragItem.value.RowKey)
  if (idx >= 0) interessenten.value[idx].pipelineStatus = status
  dragItem.value = null
}
</script>
