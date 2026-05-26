<template>
  <div class="flex gap-6 h-full">
    <!-- Linke Spalte: Target auswählen -->
    <div class="w-64 flex-shrink-0 flex flex-col" style="max-height: calc(100vh - 140px)">
      <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Target wählen</h3>
      <div class="relative mb-2">
        <input v-model="search" placeholder="Suche mb-Nr, Name, Firma…"
          class="w-full pl-8 pr-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30" />
        <Search class="w-4 h-4 text-gray-400 absolute left-2.5 top-2.5" />
      </div>
      <div class="text-xs text-gray-400 mb-2">{{ filteredTargets.length }} / {{ targets.length }}</div>
      <div class="space-y-1 overflow-y-auto pr-1 flex-1">
        <button
          v-for="t in filteredTargets" :key="t.RowKey"
          @click="selectTarget(t)"
          :class="['w-full text-left px-3 py-2 rounded-xl text-sm transition-colors', selectedTarget?.RowKey === t.RowKey ? 'bg-[#097e92] text-white' : 'hover:bg-gray-100 text-gray-700']"
        >
          <div class="font-mono text-xs opacity-70">{{ t.mbNr }}</div>
          <div class="truncate">{{ t.verkaueferName }}</div>
          <div v-if="t.firma" class="truncate text-xs opacity-60">{{ t.firma }}</div>
        </button>
      </div>
    </div>

    <!-- Rechte Spalte: Ordner + Dateien -->
    <div class="flex-1">
      <div v-if="!selectedTarget" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">
        <FolderOpen class="w-10 h-10 mx-auto mb-3 text-gray-200" />
        Bitte links ein Target auswählen.
      </div>

      <div v-else>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-900">{{ selectedTarget.mbNr }} – Dokumente</h2>
          <span v-if="selectedOrdner" class="text-sm text-[#097e92] font-medium">{{ selectedOrdner }}</span>
        </div>

        <!-- Ordner-Grid -->
        <div v-if="!selectedOrdner" class="grid grid-cols-4 gap-3">
          <button
            v-for="ordner in ordnerListe" :key="ordner"
            @click="openOrdner(ordner)"
            class="bg-white rounded-xl border border-gray-100 p-4 text-left hover:border-[#097e92]/40 hover:shadow-sm transition-all"
          >
            <Folder class="w-8 h-8 text-[#097e92] mb-2" />
            <div class="text-xs font-medium text-gray-700 leading-tight">{{ ordner }}</div>
            <div class="text-xs text-gray-400 mt-0.5">{{ countInOrdner(ordner) }} Dateien</div>
          </button>
        </div>

        <!-- Dateiliste -->
        <div v-else>
          <button @click="selectedOrdner = null" class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
            <ChevronLeft class="w-4 h-4" /> Zurück zu Ordnern
          </button>

          <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <!-- Upload-Zeile -->
            <div class="px-4 py-3 border-b border-gray-50 flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700">{{ selectedOrdner }}</span>
              <label class="flex items-center gap-2 px-3 py-1.5 bg-[#097e92] text-white rounded-lg text-xs cursor-pointer hover:bg-[#0a9aaf]">
                <Upload class="w-3.5 h-3.5" />
                Datei hochladen
                <input type="file" class="hidden" @change="uploadFile" :disabled="uploading" />
              </label>
            </div>

            <div v-if="!filteredDokumente.length" class="p-6 text-center text-gray-400 text-sm">
              Noch keine Dateien in diesem Ordner.
            </div>

            <div v-for="dok in filteredDokumente" :key="dok.RowKey" class="flex items-center justify-between px-4 py-3 border-b border-gray-50 last:border-0 hover:bg-gray-50">
              <div class="flex items-center gap-3">
                <FileText class="w-4 h-4 text-gray-400" />
                <div>
                  <div class="text-sm font-medium text-gray-700">{{ dok.dateiname }}</div>
                  <div class="text-xs text-gray-400">{{ dok.hochgeladenVon }} · {{ formatDate(dok.hochgeladenAm) }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button @click="downloadFile(dok)" class="flex items-center gap-1 text-xs text-[#097e92] hover:text-[#0a9aaf]">
                  <Download class="w-3.5 h-3.5" /> Herunterladen
                </button>
                <button @click="deleteFile(dok)" class="text-xs text-red-400 hover:text-red-600">
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { FolderOpen, Folder, ChevronLeft, Upload, FileText, Download, Trash2, Search } from '@lucide/vue'
import { getTargets, getDokumente, uploadDokument } from '../../api.js'
import { authFetch } from '../../api.js'

const targets = ref([])
const search = ref('')
const filteredTargets = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return targets.value
  return targets.value.filter(t =>
    (t.mbNr || '').toLowerCase().includes(q) ||
    (t.verkaueferName || '').toLowerCase().includes(q) ||
    (t.firma || '').toLowerCase().includes(q) ||
    (t.region || '').toLowerCase().includes(q)
  )
})
const selectedTarget = ref(null)
const selectedOrdner = ref(null)
const dokumente = ref([])
const uploading = ref(false)

const ordnerListe = ['Unterlagen Ausschreibung', 'Exposé', 'Protokoll', 'NDA', 'Gesprächsnotizen', 'Datenraum', 'Beratervertrag', 'Diverses']

onMounted(async () => { targets.value = await getTargets() })

async function selectTarget(t) {
  selectedTarget.value = t
  selectedOrdner.value = null
  dokumente.value = await getDokumente(t.RowKey)
}

async function openOrdner(ordner) {
  selectedOrdner.value = ordner
}

const filteredDokumente = computed(() =>
  dokumente.value.filter(d => d.ordner === selectedOrdner.value)
)

function countInOrdner(ordner) {
  return dokumente.value.filter(d => d.ordner === ordner).length
}

async function uploadFile(e) {
  const file = e.target.files[0]
  if (!file || !selectedTarget.value) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const result = await authFetch(
      `/targets/${selectedTarget.value.RowKey}/dokumente/upload?ordner=${encodeURIComponent(selectedOrdner.value)}&dateiname=${encodeURIComponent(file.name)}`,
      { method: 'POST', data: file, headers: { 'Content-Type': file.type } }
    )
    dokumente.value.push(result)
  } catch { alert('Upload fehlgeschlagen') }
  finally { uploading.value = false; e.target.value = '' }
}

async function downloadFile(dok) {
  try {
    const result = await authFetch(`/targets/${selectedTarget.value.RowKey}/dokumente/${dok.RowKey}/download`)
    window.open(result.url, '_blank')
  } catch { alert('Download fehlgeschlagen') }
}

async function deleteFile(dok) {
  if (!confirm(`"${dok.dateiname}" löschen?`)) return
  await authFetch(`/targets/${selectedTarget.value.RowKey}/dokumente/${dok.RowKey}`, { method: 'DELETE' })
  dokumente.value = dokumente.value.filter(d => d.RowKey !== dok.RowKey)
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
</script>
