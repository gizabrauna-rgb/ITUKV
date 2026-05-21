<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Topbar -->
    <header class="bg-[#161e2a] text-white px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-[#097e92] rounded-lg flex items-center justify-center">
          <Building2 class="w-4 h-4 text-white" />
        </div>
        <div>
          <span class="font-bold text-sm">ITUKV Dashboard</span>
          <span class="text-gray-400 text-xs ml-2">Verkäufer-Portal</span>
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

      <!-- Tab: Mein Projekt -->
      <div v-if="tab === 'projekt'">
        <h2 class="text-xl font-bold text-gray-900 mb-5">Mein Verkaufsprojekt</h2>

        <!-- Fortschritt -->
        <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-gray-700">Gesamtfortschritt</span>
            <span class="text-sm font-bold text-[#097e92]">{{ doneCount }} / {{ checkliste.length }} erledigt</span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2">
            <div class="bg-[#097e92] h-2 rounded-full transition-all" :style="`width: ${progress}%`"></div>
          </div>
          <div class="text-xs text-gray-400 mt-1">{{ progress }}% abgeschlossen</div>
        </div>

        <!-- Checkliste -->
        <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div class="px-5 py-3 border-b border-gray-50">
            <h3 class="text-sm font-semibold text-gray-700">Aufgaben-Checkliste</h3>
          </div>
          <div v-if="loadingCheck" class="p-6 text-center text-gray-400 text-sm">Lade Checkliste…</div>
          <ul v-else class="divide-y divide-gray-50">
            <li v-for="item in checkliste" :key="item.id"
              class="flex items-center gap-4 px-5 py-3 hover:bg-gray-50 cursor-pointer"
              @click="toggleItem(item)">
              <div :class="['w-5 h-5 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors', item.done ? 'bg-[#097e92] border-[#097e92]' : 'border-gray-300 hover:border-[#097e92]']">
                <Check v-if="item.done" class="w-3 h-3 text-white" />
              </div>
              <span :class="['text-sm', item.done ? 'line-through text-gray-400' : 'text-gray-700']">{{ item.label }}</span>
              <CheckCircle v-if="item.done" class="w-4 h-4 text-green-500 ml-auto" />
              <Circle v-else class="w-4 h-4 text-gray-200 ml-auto" />
            </li>
          </ul>
        </div>
      </div>

      <!-- Tab: Interessenten -->
      <div v-else-if="tab === 'interessenten'">
        <h2 class="text-xl font-bold text-gray-900 mb-5">Meine Interessenten</h2>
        <div v-if="loadingInt" class="text-center text-gray-400 text-sm py-10">Lade Interessenten…</div>
        <div v-else-if="!interessenten.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400 text-sm">
          <Users class="w-10 h-10 mx-auto mb-3 text-gray-200" />
          Noch keine Interessenten. Sobald jemand ein NDA unterzeichnet, erscheint er hier.
        </div>
        <div v-else class="space-y-3">
          <div v-for="i in interessenten" :key="i.RowKey" class="bg-white rounded-xl border border-gray-100 p-5">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-medium text-gray-800">{{ i.firma || i.name }}</span>
                  <span :class="ndaClass(i.ndaStatus)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ ndaLabel(i.ndaStatus) }}</span>
                  <span v-if="i.veto" class="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-medium">VETO</span>
                </div>
                <div class="text-xs text-gray-400 mt-0.5">{{ i.plz }} {{ i.ort }}</div>
              </div>
              <!-- Rating -->
              <div class="flex items-center gap-0.5">
                <button v-for="n in 5" :key="n" @click="setRating(i, n)" class="p-0.5">
                  <Star :class="n <= i.rating ? 'text-[#c8b274] fill-[#c8b274]' : 'text-gray-200'" class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Aktionen -->
            <div class="flex gap-2 mt-3">
              <!-- Freigabe-Toggle -->
              <button @click="toggleFreigabe(i)"
                :class="['flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors', i.freigegebenFuerKontakt ? 'bg-green-50 text-green-700 border-green-200' : 'text-gray-500 border-gray-200 hover:bg-gray-50']">
                <UserCheck class="w-3.5 h-3.5" />
                {{ i.freigegebenFuerKontakt ? 'Freigegeben' : 'Freigabe geben' }}
              </button>

              <!-- VETO -->
              <button v-if="!i.veto" @click="openVeto(i)"
                class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors">
                <Ban class="w-3.5 h-3.5" /> VETO setzen
              </button>
              <button v-else @click="removeVeto(i)"
                class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-600 border border-red-200">
                <Ban class="w-3.5 h-3.5" /> VETO entfernen
              </button>
            </div>

            <!-- VETO Begründung -->
            <div v-if="i.veto && i.vetoBegruendung" class="mt-2 text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">
              Begründung: {{ i.vetoBegruendung }}
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Dokumente -->
      <div v-else-if="tab === 'dokumente'">
        <h2 class="text-xl font-bold text-gray-900 mb-5">Meine Dokumente</h2>

        <div v-if="!selectedOrdner" class="grid grid-cols-2 gap-3">
          <button v-for="ordner in ordnerListe" :key="ordner"
            @click="openOrdner(ordner)"
            class="bg-white rounded-xl border border-gray-100 p-4 text-left hover:border-[#097e92]/40 hover:shadow-sm transition-all flex items-center gap-3">
            <Folder class="w-6 h-6 text-[#097e92]" />
            <div>
              <div class="text-sm font-medium text-gray-700">{{ ordner }}</div>
              <div class="text-xs text-gray-400">{{ countInOrdner(ordner) }} Dateien</div>
            </div>
          </button>
        </div>

        <div v-else>
          <button @click="selectedOrdner = null" class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
            <ChevronLeft class="w-4 h-4" /> Zurück
          </button>
          <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <div class="px-4 py-3 border-b border-gray-50 flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700">{{ selectedOrdner }}</span>
              <label class="flex items-center gap-2 px-3 py-1.5 bg-[#097e92] text-white rounded-lg text-xs cursor-pointer hover:bg-[#0a9aaf]">
                <Upload class="w-3.5 h-3.5" /> Hochladen
                <input type="file" class="hidden" @change="uploadFile" />
              </label>
            </div>
            <div v-if="!filteredDok.length" class="p-6 text-center text-gray-400 text-sm">Keine Dateien in diesem Ordner.</div>
            <div v-for="dok in filteredDok" :key="dok.RowKey"
              class="flex items-center justify-between px-4 py-3 border-b border-gray-50 last:border-0">
              <div class="flex items-center gap-3">
                <FileText class="w-4 h-4 text-gray-400" />
                <div>
                  <div class="text-sm font-medium text-gray-700">{{ dok.dateiname }}</div>
                  <div class="text-xs text-gray-400">{{ formatDate(dok.hochgeladenAm) }}</div>
                </div>
              </div>
              <button @click="downloadDok(dok)" class="flex items-center gap-1 text-xs text-[#097e92] hover:text-[#0a9aaf]">
                <Download class="w-3.5 h-3.5" /> Download
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- VETO Modal -->
    <div v-if="vetoTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm">
        <h3 class="font-bold text-gray-900 mb-2">VETO setzen</h3>
        <p class="text-sm text-gray-500 mb-3">Bitte gib eine kurze Begründung an:</p>
        <textarea v-model="vetoText" rows="3" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-200 resize-none" placeholder="Begründung…"></textarea>
        <div class="flex gap-3 mt-4">
          <button @click="vetoTarget = null; vetoText = ''" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
          <button @click="confirmVeto" class="flex-1 px-4 py-2 bg-red-500 text-white rounded-xl text-sm font-medium">VETO bestätigen</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Building2, LogOut, Briefcase, Users, FolderOpen, Check, CheckCircle, Circle,
  Star, UserCheck, Ban, Folder, ChevronLeft, Upload, FileText, Download
} from '@lucide/vue'
import { authFetch, getInteressenten, updateInteressent, getDokumente } from '../api.js'

const props = defineProps({ userName: String })
const emit = defineEmits(['logout'])
const targetId = sessionStorage.getItem('targetId') || ''

const tab = ref('projekt')
const checkliste = ref([])
const interessenten = ref([])
const dokumente = ref([])
const loadingCheck = ref(true)
const loadingInt = ref(true)
const selectedOrdner = ref(null)
const vetoTarget = ref(null)
const vetoText = ref('')

const navItems = [
  { tab: 'projekt', label: 'Mein Projekt', icon: Briefcase },
  { tab: 'interessenten', label: 'Interessenten', icon: Users },
  { tab: 'dokumente', label: 'Dokumente', icon: FolderOpen },
]

const ordnerListe = ['Unterlagen Ausschreibung', 'Exposé', 'Protokoll', 'NDA', 'Gesprächsnotizen', 'Datenraum', 'Beratervertrag', 'Diverses']

const doneCount = computed(() => checkliste.value.filter(i => i.done).length)
const progress = computed(() => !checkliste.value.length ? 0 : Math.round(doneCount.value / checkliste.value.length * 100))
const filteredDok = computed(() => dokumente.value.filter(d => d.ordner === selectedOrdner.value))

function countInOrdner(o) { return dokumente.value.filter(d => d.ordner === o).length }

onMounted(async () => {
  if (targetId) {
    try {
      const full = await authFetch(`/targets/${targetId}`)
      checkliste.value = JSON.parse(full.checklisteJson || '[]')
    } finally { loadingCheck.value = false }
    try {
      interessenten.value = await getInteressenten(targetId)
    } finally { loadingInt.value = false }
    dokumente.value = await getDokumente(targetId)
  } else {
    loadingCheck.value = false; loadingInt.value = false
  }
})

async function toggleItem(item) {
  item.done = !item.done
  await authFetch(`/targets/${targetId}/checkliste`, { method: 'PATCH', data: { id: item.id, done: item.done } })
}

async function setRating(i, n) {
  i.rating = n
  await updateInteressent(targetId, i.RowKey, { rating: n })
}

async function toggleFreigabe(i) {
  i.freigegebenFuerKontakt = !i.freigegebenFuerKontakt
  await updateInteressent(targetId, i.RowKey, { freigegebenFuerKontakt: i.freigegebenFuerKontakt })
}

function openVeto(i) { vetoTarget.value = i }
async function confirmVeto() {
  vetoTarget.value.veto = true
  vetoTarget.value.vetoBegruendung = vetoText.value
  await updateInteressent(targetId, vetoTarget.value.RowKey, { veto: true, vetoBegruendung: vetoText.value })
  vetoTarget.value = null; vetoText.value = ''
}
async function removeVeto(i) {
  i.veto = false; i.vetoBegruendung = ''
  await updateInteressent(targetId, i.RowKey, { veto: false, vetoBegruendung: '' })
}

function ndaClass(s) {
  if (s === 'unterzeichnet') return 'bg-green-100 text-green-700'
  if (s === 'gesendet') return 'bg-yellow-100 text-yellow-700'
  if (s === 'abgelehnt') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-500'
}
function ndaLabel(s) {
  return { unterzeichnet:'NDA unterzeichnet', gesendet:'NDA gesendet', abgelehnt:'NDA abgelehnt' }[s] || 'NDA ausstehend'
}

async function openOrdner(o) { selectedOrdner.value = o }
async function uploadFile(e) {
  const file = e.target.files[0]; if (!file) return
  await authFetch(`/targets/${targetId}/dokumente/upload?ordner=${encodeURIComponent(selectedOrdner.value)}&dateiname=${encodeURIComponent(file.name)}`, { method: 'POST', data: file, headers: { 'Content-Type': file.type } })
  dokumente.value = await getDokumente(targetId)
  e.target.value = ''
}
async function downloadDok(dok) {
  const r = await authFetch(`/targets/${targetId}/dokumente/${dok.RowKey}/download`)
  window.open(r.url, '_blank')
}
function formatDate(iso) { return iso ? new Date(iso).toLocaleDateString('de-DE') : '' }
</script>
