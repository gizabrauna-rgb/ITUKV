<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Dokumente</h3>
        <p class="text-xs text-gray-500">Standard-Ordnerstruktur · Drag &amp; Drop zum Hochladen</p>
      </div>
      <div v-if="selectedFolder" class="text-xs text-gray-500">
        Aktiver Ordner: <strong>{{ selectedFolder }}</strong>
      </div>
    </div>

    <!-- Ordner-Grid (immer sichtbar) -->
    <div class="grid grid-cols-3 gap-3 mb-5">
      <button
        v-for="o in ordnerListe" :key="o"
        @click="selectedFolder = o"
        :class="['bg-white rounded-xl border-2 p-4 hover:shadow-sm transition-all flex items-center gap-3 text-left',
                 selectedFolder === o ? 'border-[#097e92] bg-[#097e92]/5' : 'border-gray-100 hover:border-gray-200']">
        <Folder class="w-6 h-6 text-[#097e92] flex-shrink-0" />
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-gray-800">{{ o }}</div>
          <div class="text-xs text-gray-400">{{ countInOrdner(o) }} {{ countInOrdner(o) === 1 ? 'Datei' : 'Dateien' }}</div>
        </div>
      </button>
    </div>

    <!-- Dateien im aktiven Ordner + Upload-Zone -->
    <div v-if="selectedFolder">
      <!-- Drop-Zone -->
      <div
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
        :class="['rounded-xl p-8 mb-4 border-2 border-dashed text-center transition-colors',
                 dragOver ? 'bg-[#097e92]/10 border-[#097e92]' : 'bg-gray-50 border-gray-300']">
        <Upload class="w-10 h-10 mx-auto mb-2" :class="dragOver ? 'text-[#097e92]' : 'text-gray-400'" />
        <p class="text-sm text-gray-700 font-medium mb-1">Datei(en) hier ablegen</p>
        <p class="text-xs text-gray-500 mb-3">Oder per Klick auswählen:</p>
        <label class="inline-flex items-center gap-2 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf] cursor-pointer">
          <Upload class="w-4 h-4" /> Datei wählen
          <input type="file" multiple class="hidden" @change="onSelect" />
        </label>
        <p v-if="uploading" class="text-xs text-[#097e92] mt-3">Lade hoch… ({{ uploadCount }})</p>
      </div>

      <!-- Datei-Liste -->
      <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <div v-if="!filesInFolder.length" class="p-6 text-center text-sm text-gray-400">
          Noch keine Dateien in „{{ selectedFolder }}".
        </div>
        <div v-for="(f, idx) in filesInFolder" :key="f.RowKey || idx" class="flex items-center gap-3 px-4 py-3 border-b border-gray-50 last:border-0 hover:bg-gray-50">
          <FileText class="w-5 h-5 text-[#097e92] flex-shrink-0" />
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-800 truncate">{{ f.name }}</div>
            <div class="text-xs text-gray-400">{{ formatSize(f.size) }} · {{ formatDate(f.uploadedAt) }}</div>
          </div>
          <a v-if="f.url" :href="f.url" target="_blank" rel="noopener" class="text-gray-500 hover:text-[#097e92] p-1.5"><Download class="w-4 h-4" /></a>
          <button @click="deleteFile(f)" class="text-gray-400 hover:text-red-500 p-1.5"><Trash2 class="w-4 h-4" /></button>
        </div>
      </div>
    </div>
    <div v-else class="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-10 text-center text-sm text-gray-400">
      <Folder class="w-10 h-10 mx-auto mb-2 text-gray-300" />
      Bitte oben einen Ordner auswählen.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Folder, Upload, FileText, Download, Trash2 } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String })
const ordnerListe = ['Verträge', 'Datenraum', 'NDA', 'Exposé', 'Vertragsverhandlungen', 'Videoprotokoll']
const dokumente = ref([])
const selectedFolder = ref('Datenraum')
const dragOver = ref(false)
const uploading = ref(false)
const uploadCount = ref(0)

const filesInFolder = computed(() => dokumente.value.filter(d => d.ordner === selectedFolder.value))
function countInOrdner(o) { return dokumente.value.filter(d => d.ordner === o).length }

async function loadDokumente() {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    try { dokumente.value = JSON.parse(t.dokumenteJson || '[]') } catch { dokumente.value = [] }
  } catch (e) { console.error(e) }
}

function onSelect(e) { handleFiles(e.target.files); e.target.value = '' }
function onDrop(e) { dragOver.value = false; handleFiles(e.dataTransfer.files) }

async function handleFiles(fileList) {
  const files = Array.from(fileList || [])
  if (!files.length) return
  uploading.value = true
  uploadCount.value = 0
  for (const f of files) {
    uploadCount.value++
    try {
      // Lese als Base64 ein (vorlaeufig: in dokumenteJson speichern)
      // Achtung: nur fuer kleine Dateien geeignet (<5 MB)
      if (f.size > 5 * 1024 * 1024) {
        alert(`'${f.name}' ist groesser als 5 MB – aktuell nicht unterstuetzt.`)
        continue
      }
      const dataUrl = await new Promise((resolve, reject) => {
        const r = new FileReader()
        r.onload = () => resolve(r.result)
        r.onerror = reject
        r.readAsDataURL(f)
      })
      dokumente.value.push({
        RowKey: 'd' + Date.now() + Math.random().toString(36).slice(2, 8),
        name: f.name,
        size: f.size,
        ordner: selectedFolder.value,
        url: dataUrl,  // Inline base64
        uploadedAt: new Date().toISOString(),
      })
    } catch (e) { console.error(e); alert('Upload fehlgeschlagen: ' + f.name) }
  }
  await save()
  uploading.value = false
  uploadCount.value = 0
}

async function deleteFile(f) {
  if (!confirm(`Datei '${f.name}' wirklich löschen?`)) return
  dokumente.value = dokumente.value.filter(d => d.RowKey !== f.RowKey)
  await save()
}

async function save() {
  if (!props.targetId) return
  try {
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, dokumenteJson: JSON.stringify(dokumente.value) } })
  } catch (e) { console.error(e); alert('Speichern fehlgeschlagen') }
}

function formatSize(b) {
  if (!b) return '0 B'
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB'
  return (b / 1024 / 1024).toFixed(1) + ' MB'
}
function formatDate(iso) { return iso ? new Date(iso).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '' }

onMounted(loadDokumente)
</script>
