<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Datenraum</h3>
        <p class="text-xs text-gray-500">Drag &amp; Drop zum Hochladen · Klick auf Ordner zum Anzeigen</p>
      </div>
    </div>

    <!-- Ordner-Grid -->
    <div class="grid grid-cols-3 gap-3 mb-5">
      <button v-for="o in ordnerListe" :key="o" @click="selectedFolder = o"
        :class="['rounded-xl border-2 p-4 transition-all flex items-center gap-3 text-left',
                 selectedFolder === o ? 'border-[#0088ba] bg-[#0088ba]/5' : 'border-gray-100 hover:border-gray-200 bg-white']">
        <Folder class="w-6 h-6 text-[#0088ba] flex-shrink-0" />
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-gray-800">{{ o }}</div>
          <div class="text-xs text-gray-400">{{ countInOrdner(o) }} {{ countInOrdner(o) === 1 ? 'Datei' : 'Dateien' }}</div>
        </div>
      </button>
    </div>

    <!-- Upload-Zone + Dateien -->
    <div v-if="selectedFolder">
      <div
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
        :class="['rounded-xl p-8 mb-4 border-2 border-dashed text-center transition-colors',
                 dragOver ? 'bg-[#0088ba]/10 border-[#0088ba]' : 'bg-gray-50 border-gray-300']">
        <Upload class="w-10 h-10 mx-auto mb-2" :class="dragOver ? 'text-[#0088ba]' : 'text-gray-400'" />
        <p class="text-sm text-gray-700 font-medium mb-1">Datei(en) hier ablegen für „{{ selectedFolder }}"</p>
        <label class="inline-flex items-center gap-2 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8] cursor-pointer mt-2">
          <Upload class="w-4 h-4" /> Datei wählen
          <input type="file" multiple class="hidden" @change="onSelect" />
        </label>
        <p v-if="uploading" class="text-xs text-[#0088ba] mt-3">Lade hoch ({{ uploadedCount }}/{{ totalCount }})…</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <div v-if="!filesInFolder.length" class="p-6 text-center text-sm text-gray-400">Noch keine Dateien in „{{ selectedFolder }}".</div>
        <div v-for="f in filesInFolder" :key="f.RowKey" class="flex items-center gap-3 px-4 py-3 border-b border-gray-50 last:border-0 hover:bg-gray-50 cursor-pointer" @click="previewFile(f)">
          <component :is="fileIcon(f)" class="w-5 h-5 text-[#0088ba] flex-shrink-0" />
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-800 truncate">{{ f.fileName }}</div>
            <div class="text-xs text-gray-400">
              {{ formatSize(f.size) }} · {{ formatDate(f.uploadedAt) }}
              <span v-if="f.uploadedBy"> · hochgeladen von {{ f.uploadedBy }}</span>
              <span v-if="f.uploadedByRole === 'target'" class="ml-1 text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded-full font-semibold">Verkäufer</span>
            </div>
          </div>
          <!-- Ordner ändern -->
          <select :value="f.ordner" @change.stop="moveFile(f, $event.target.value)" @click.stop class="text-xs border border-gray-200 rounded-lg px-2 py-1">
            <option v-for="o in ordnerListe" :key="o" :value="o">{{ o }}</option>
          </select>
          <button @click.stop="previewFile(f)" class="text-gray-500 hover:text-[#0088ba] p-1.5" title="Anzeigen"><Eye class="w-4 h-4" /></button>
          <button @click.stop="downloadFile(f)" class="text-gray-500 hover:text-[#0088ba] p-1.5" title="Download"><Download class="w-4 h-4" /></button>
          <button v-if="!readOnly" @click.stop="deleteFile(f)" class="text-gray-400 hover:text-red-500 p-1.5" title="Löschen"><Trash2 class="w-4 h-4" /></button>
        </div>
      </div>
    </div>
    <div v-else class="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-10 text-center text-sm text-gray-400">
      <Folder class="w-10 h-10 mx-auto mb-2 text-gray-300" />
      Bitte oben einen Ordner auswählen.
    </div>

    <!-- Preview Modal -->
    <div v-if="previewFile_" class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" @click.self="closePreview">
      <div class="bg-white rounded-2xl w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden shadow-2xl">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-100">
          <div class="min-w-0 flex-1">
            <h3 class="font-bold text-gray-900 truncate">{{ previewFile_.fileName }}</h3>
            <p class="text-xs text-gray-500">{{ formatSize(previewFile_.size) }} · {{ formatDate(previewFile_.uploadedAt) }}</p>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <button @click="downloadFile(previewFile_)" class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-1.5">
              <Download class="w-3.5 h-3.5" /> Download
            </button>
            <button @click="closePreview" class="p-1.5 hover:bg-gray-100 rounded-lg"><X class="w-5 h-5 text-gray-500" /></button>
          </div>
        </div>
        <div class="flex-1 bg-gray-100 overflow-hidden">
          <div v-if="previewLoading" class="h-full flex items-center justify-center text-sm text-gray-500">Lade Vorschau…</div>
          <iframe v-else-if="previewType === 'pdf'" :src="previewUrl" class="w-full h-full" frameborder="0"></iframe>
          <div v-else-if="previewType === 'image'" class="h-full flex items-center justify-center p-4">
            <img :src="previewUrl" :alt="previewFile_.fileName" class="max-h-full max-w-full object-contain" />
          </div>
          <div v-else-if="previewType === 'video'" class="h-full flex items-center justify-center p-4">
            <video :src="previewUrl" controls autoplay class="max-h-full max-w-full"></video>
          </div>
          <div v-else-if="previewType === 'audio'" class="h-full flex items-center justify-center p-4">
            <audio :src="previewUrl" controls autoplay class="w-full max-w-md"></audio>
          </div>
          <div v-else-if="previewType === 'text'" class="h-full overflow-auto p-6 bg-white">
            <pre class="text-sm whitespace-pre-wrap">{{ previewText }}</pre>
          </div>
          <div v-else class="h-full flex flex-col items-center justify-center text-gray-500 p-8">
            <FileText class="w-16 h-16 text-gray-300 mb-3" />
            <p class="text-sm mb-4">Keine Inline-Vorschau für diesen Dateityp möglich.</p>
            <button @click="downloadFile(previewFile_)" class="px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium flex items-center gap-2">
              <Download class="w-4 h-4" /> Datei herunterladen
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Folder, Upload, FileText, Download, Trash2, Eye, X, Image as ImageIcon, Video, Music, FileType2 } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({
  targetId: String,
  readOnly: { type: Boolean, default: false },
  initialDoc: { type: Object, default: null },  // { ordner, docId } — direkt öffnen
})
const ALLE_ORDNER = ['Verträge', 'NDA', 'Exposé', 'Bilanzen & Finanzen', 'Vertragsverhandlungen', 'Videoprotokolle', 'Sonstiges']
// Read-only-Verkaeufer-Sicht: NDAs der Interessenten sind nicht einsehbar (Datenschutz)
const ordnerListe = computed(() => props.readOnly ? ALLE_ORDNER.filter(o => o !== 'NDA') : ALLE_ORDNER)
const dokumente = ref([])
const selectedFolder = ref('Verträge')
const dragOver = ref(false)
const uploading = ref(false)
const uploadedCount = ref(0)
const totalCount = ref(0)

const filesInFolder = computed(() => dokumente.value.filter(d => d.ordner === selectedFolder.value))
function countInOrdner(o) { return dokumente.value.filter(d => d.ordner === o).length }

async function load() {
  if (!props.targetId) return
  try {
    const r = await authFetch('/dokument-list', { method: 'POST', data: { targetId: props.targetId } })
    dokumente.value = r.items || []
  } catch (e) { console.error(e) }
}

function onSelect(e) { handleFiles(e.target.files); e.target.value = '' }
function onDrop(e) { dragOver.value = false; handleFiles(e.dataTransfer.files) }

async function handleFiles(fileList) {
  const files = Array.from(fileList || [])
  if (!files.length) return
  totalCount.value = files.length
  uploadedCount.value = 0
  uploading.value = true
  for (const f of files) {
    try {
      // 1. SAS-URL anfordern
      const sas = await authFetch('/dokument-upload-url', { method: 'POST', data: {
        targetId: props.targetId, ordner: selectedFolder.value,
        fileName: f.name, contentType: f.type || 'application/octet-stream',
      }})
      // 2. Direkt zu Blob Storage hochladen (umgeht Function-Limits, schnell, auch fuer Videos)
      const putRes = await fetch(sas.uploadUrl, {
        method: 'PUT',
        headers: { 'x-ms-blob-type': 'BlockBlob', 'Content-Type': f.type || 'application/octet-stream' },
        body: f,
      })
      if (!putRes.ok) throw new Error(`Blob-Upload HTTP ${putRes.status}`)
      // 3. Metadaten registrieren
      const created = await authFetch('/dokument-register', { method: 'POST', data: {
        targetId: props.targetId, ordner: selectedFolder.value,
        fileName: f.name, blobName: sas.blobName,
        contentType: f.type || 'application/octet-stream', size: f.size,
      }})
      dokumente.value.unshift({
        RowKey: created.id, PartitionKey: props.targetId,
        ordner: selectedFolder.value, fileName: f.name, size: f.size,
        uploadedAt: created.uploadedAt, uploadedBy: created.uploadedBy,
      })
      uploadedCount.value++
    } catch (e) { console.error(e); toast.error(`Upload fehlgeschlagen: ${f.name}\n${e?.response?.data?.error || e.message}`) }
  }
  uploading.value = false
  uploadedCount.value = 0
  totalCount.value = 0
}

// Preview-Logik
const previewFile_ = ref(null)
const previewUrl = ref('')
const previewType = ref('')
const previewText = ref('')
const previewLoading = ref(false)

function detectType(f) {
  const name = (f.fileName || '').toLowerCase()
  const ct = (f.contentType || '').toLowerCase()
  if (ct.startsWith('image/') || /\.(jpe?g|png|gif|webp|svg|bmp)$/.test(name)) return 'image'
  if (ct === 'application/pdf' || name.endsWith('.pdf')) return 'pdf'
  if (ct.startsWith('video/') || /\.(mp4|mov|webm|avi|mkv|m4v)$/.test(name)) return 'video'
  if (ct.startsWith('audio/') || /\.(mp3|wav|ogg|m4a)$/.test(name)) return 'audio'
  if (ct.startsWith('text/') || /\.(txt|md|csv|json|xml|log)$/.test(name)) return 'text'
  return 'other'
}

function fileIcon(f) {
  const t = detectType(f)
  if (t === 'image') return ImageIcon
  if (t === 'video') return Video
  if (t === 'audio') return Music
  if (t === 'pdf') return FileType2
  return FileText
}

async function previewFile(f) {
  previewFile_.value = f
  previewType.value = detectType(f)
  previewText.value = ''
  previewUrl.value = ''
  if (previewType.value === 'other') return
  previewLoading.value = true
  try {
    const base = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'
    const token = sessionStorage.getItem('customerJwt') || sessionStorage.getItem('msalToken') || ''
    const r = await fetch(`${base}/dokument-download?targetId=${props.targetId}&id=${f.RowKey}`, {
      headers: { 'Authorization': 'Bearer ' + token }
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    if (previewType.value === 'text') {
      previewText.value = await r.text()
    } else {
      // MIME explizit setzen — Server liefert manchmal application/octet-stream
      const mimeMap = { pdf: 'application/pdf', image: f.contentType || 'image/jpeg', video: f.contentType || 'video/mp4', audio: f.contentType || 'audio/mpeg' }
      const ab = await r.arrayBuffer()
      const blob = new Blob([ab], { type: mimeMap[previewType.value] || f.contentType || 'application/octet-stream' })
      previewUrl.value = URL.createObjectURL(blob)
    }
  } catch (e) { toast.error('Vorschau fehlgeschlagen: ' + e.message) }
  finally { previewLoading.value = false }
}

function closePreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  previewType.value = ''
  previewText.value = ''
  previewFile_.value = null
}

async function downloadFile(f) {
  const base = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'
  const token = sessionStorage.getItem('customerJwt') || sessionStorage.getItem('msalToken') || ''
  try {
    const r = await fetch(`${base}/dokument-download?targetId=${props.targetId}&id=${f.RowKey}`, {
      headers: { 'Authorization': 'Bearer ' + token }
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = f.fileName; a.click()
    URL.revokeObjectURL(url)
  } catch (e) { toast.error('Download fehlgeschlagen: ' + e.message) }
}

async function deleteFile(f) {
  if (props.readOnly) { toast.info('Du darfst keine Dateien löschen.'); return }
  if (!confirm(`Datei '${f.fileName}' wirklich löschen?`)) return
  try {
    await authFetch('/dokument-delete', { method: 'POST', data: { targetId: props.targetId, id: f.RowKey } })
    dokumente.value = dokumente.value.filter(d => d.RowKey !== f.RowKey)
  } catch (e) { toast.error('Löschen fehlgeschlagen: ' + (e?.response?.data?.error || e.message)) }
}

async function moveFile(f, neuerOrdner) {
  if (f.ordner === neuerOrdner) return
  try {
    await authFetch('/dokument-move', { method: 'POST', data: { targetId: props.targetId, id: f.RowKey, ordner: neuerOrdner } })
    f.ordner = neuerOrdner
  } catch (e) { toast.error('Verschieben fehlgeschlagen: ' + (e?.response?.data?.error || e.message)) }
}

function formatSize(b) { if (!b) return '0 B'; if (b < 1024) return b + ' B'; if (b < 1024*1024) return (b/1024).toFixed(1) + ' KB'; return (b/1024/1024).toFixed(1) + ' MB' }
function formatDate(iso) { return iso ? new Date(iso).toLocaleString('de-DE', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '' }

onMounted(async () => {
  await load()
  // Falls per Deep-Link ein Dokument gezielt geöffnet werden soll
  if (props.initialDoc?.ordner) {
    selectedFolder.value = props.initialDoc.ordner
    if (props.initialDoc.docId) {
      const f = dokumente.value.find(d => d.RowKey === props.initialDoc.docId)
      if (f) await previewFile(f)
      else {
        // Fallback: erstes Dokument im NDA-Ordner zeigen (falls Auto-ID nicht greift)
        const first = dokumente.value.find(d => d.ordner === props.initialDoc.ordner)
        if (first) await previewFile(first)
      }
    }
  }
})
</script>
