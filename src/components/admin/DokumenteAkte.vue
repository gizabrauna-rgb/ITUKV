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
                 selectedFolder === o ? 'border-[#097e92] bg-[#097e92]/5' : 'border-gray-100 hover:border-gray-200 bg-white']">
        <Folder class="w-6 h-6 text-[#097e92] flex-shrink-0" />
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
                 dragOver ? 'bg-[#097e92]/10 border-[#097e92]' : 'bg-gray-50 border-gray-300']">
        <Upload class="w-10 h-10 mx-auto mb-2" :class="dragOver ? 'text-[#097e92]' : 'text-gray-400'" />
        <p class="text-sm text-gray-700 font-medium mb-1">Datei(en) hier ablegen für „{{ selectedFolder }}"</p>
        <label class="inline-flex items-center gap-2 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf] cursor-pointer mt-2">
          <Upload class="w-4 h-4" /> Datei wählen
          <input type="file" multiple class="hidden" @change="onSelect" />
        </label>
        <p v-if="uploading" class="text-xs text-[#097e92] mt-3">Lade hoch ({{ uploadedCount }}/{{ totalCount }})…</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <div v-if="!filesInFolder.length" class="p-6 text-center text-sm text-gray-400">Noch keine Dateien in „{{ selectedFolder }}".</div>
        <div v-for="f in filesInFolder" :key="f.RowKey" class="flex items-center gap-3 px-4 py-3 border-b border-gray-50 last:border-0 hover:bg-gray-50">
          <FileText class="w-5 h-5 text-[#097e92] flex-shrink-0" />
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-800 truncate">{{ f.fileName }}</div>
            <div class="text-xs text-gray-400">
              {{ formatSize(f.size) }} · {{ formatDate(f.uploadedAt) }}
              <span v-if="f.uploadedBy"> · hochgeladen von {{ f.uploadedBy }}</span>
              <span v-if="f.uploadedByRole === 'target'" class="ml-1 text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded-full font-semibold">Verkäufer</span>
            </div>
          </div>
          <!-- Ordner ändern -->
          <select :value="f.ordner" @change="moveFile(f, $event.target.value)" class="text-xs border border-gray-200 rounded-lg px-2 py-1">
            <option v-for="o in ordnerListe" :key="o" :value="o">{{ o }}</option>
          </select>
          <button @click="downloadFile(f)" class="text-gray-500 hover:text-[#097e92] p-1.5"><Download class="w-4 h-4" /></button>
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

const props = defineProps({ targetId: String, readOnly: { type: Boolean, default: false } })
const ordnerListe = ['Verträge', 'NDA', 'Exposé', 'Bilanzen & Finanzen', 'Vertragsverhandlungen', 'Videoprotokolle', 'Sonstiges']
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
    } catch (e) { console.error(e); alert(`Upload fehlgeschlagen: ${f.name}\n${e?.response?.data?.error || e.message}`) }
  }
  uploading.value = false
  uploadedCount.value = 0
  totalCount.value = 0
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
  } catch (e) { alert('Download fehlgeschlagen: ' + e.message) }
}

async function deleteFile(f) {
  if (props.readOnly) { alert('Du darfst keine Dateien löschen.'); return }
  if (!confirm(`Datei '${f.fileName}' wirklich löschen?`)) return
  try {
    await authFetch('/dokument-delete', { method: 'POST', data: { targetId: props.targetId, id: f.RowKey } })
    dokumente.value = dokumente.value.filter(d => d.RowKey !== f.RowKey)
  } catch (e) { alert('Löschen fehlgeschlagen: ' + (e?.response?.data?.error || e.message)) }
}

async function moveFile(f, neuerOrdner) {
  if (f.ordner === neuerOrdner) return
  try {
    await authFetch('/dokument-move', { method: 'POST', data: { targetId: props.targetId, id: f.RowKey, ordner: neuerOrdner } })
    f.ordner = neuerOrdner
  } catch (e) { alert('Verschieben fehlgeschlagen: ' + (e?.response?.data?.error || e.message)) }
}

function formatSize(b) { if (!b) return '0 B'; if (b < 1024) return b + ' B'; if (b < 1024*1024) return (b/1024).toFixed(1) + ' KB'; return (b/1024/1024).toFixed(1) + ' MB' }
function formatDate(iso) { return iso ? new Date(iso).toLocaleString('de-DE', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '' }

onMounted(load)
</script>
