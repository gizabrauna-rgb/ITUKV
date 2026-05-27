<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Datenraum</h3>
        <p class="text-xs text-gray-500">Drag &amp; Drop zum Hochladen · Klick auf Ordner zum Anzeigen</p>
      </div>
    </div>

    <!-- Upload-Zone (ganz oben) -->
    <div
      @dragover.prevent="dragOver = true"
      @dragleave.prevent="dragOver = false"
      @drop.prevent="onDrop"
      :class="['rounded-xl p-5 mb-4 border-2 border-dashed text-center transition-colors flex items-center justify-center gap-4 flex-wrap',
               dragOver ? 'bg-[#0088ba]/10 border-[#0088ba]' : 'bg-gray-50 border-gray-300']">
      <Upload class="w-6 h-6" :class="dragOver ? 'text-[#0088ba]' : 'text-gray-400'" />
      <span class="text-sm text-gray-700">
        Datei(en) hier ablegen<span v-if="selectedFolder"> für <strong>„{{ selectedFolder }}"</strong></span>
      </span>
      <label class="inline-flex items-center gap-2 px-3 py-1.5 bg-[#0088ba] text-white rounded-lg text-xs font-medium hover:bg-[#00a0d8] cursor-pointer">
        <Upload class="w-3.5 h-3.5" /> Datei wählen
        <input type="file" multiple class="hidden" @change="onSelect" :disabled="!selectedFolder" />
      </label>
      <span v-if="uploading" class="text-xs text-[#0088ba]">Lade hoch ({{ uploadedCount }}/{{ totalCount }})…</span>
    </div>

    <!-- Ordner-Grid: alle nebeneinander, kompakt -->
    <div class="grid grid-cols-7 gap-2 mb-4">
      <button v-for="o in ordnerListe" :key="o" @click="selectedFolder = o"
        :class="['rounded-lg border-2 p-2.5 transition-all flex flex-col items-center text-center',
                 selectedFolder === o ? 'border-[#0088ba] bg-[#0088ba]/5' : 'border-gray-100 hover:border-gray-200 bg-white']">
        <Folder class="w-5 h-5 text-[#0088ba] mb-1" />
        <div class="text-[11px] font-medium text-gray-800 leading-tight">{{ o }}</div>
        <div class="text-[10px] text-gray-400 mt-0.5">{{ countInOrdner(o) }}</div>
      </button>
    </div>

    <!-- Dateien -->
    <div v-if="selectedFolder">
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
          <button v-if="!readOnly && isPdf(f)" @click.stop="aiAnalyze(f)"
            :class="['flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded-lg',
                     pdfWarn(f) ? 'bg-amber-500 hover:bg-amber-600 text-white' : 'bg-purple-600 hover:bg-purple-700 text-white']"
            :title="pdfWarn(f)
              ? `Achtung: ${Math.round((f.size||0)/1024/1024*10)/10} MB - bei vielen Seiten kann die Analyse abbrechen (Tier-1-Limit)`
              : 'KI-Analyse: Kennzahlen automatisch aus dem PDF ziehen (empfohlen: bis ~20 Seiten)'">
            <Sparkles class="w-3.5 h-3.5" /> KI-Analyse
          </button>
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

    <!-- KI-Vorschlag Modal -->
    <div v-if="aiResult" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="aiResult = null">
      <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <Sparkles class="w-5 h-5 text-purple-600" />
            <h3 class="font-bold text-gray-900">KI-Vorschlag</h3>
            <span v-if="aiResult.dokumentTyp" class="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">{{ aiResult.dokumentTyp }}</span>
          </div>
          <button @click="aiResult = null"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="p-5 overflow-y-auto flex-1">
          <p class="text-xs text-gray-500 mb-4">Die KI hat folgende Werte aus dem Dokument gelesen. Wähle aus welche du übernehmen möchtest — kein Wert wird ohne dein „Übernehmen"-Klick gespeichert.</p>
          <div v-if="aiResult.extracted.kennzahlenText" class="mb-4 p-3 bg-purple-50 border border-purple-100 rounded-lg text-sm text-purple-900 italic">
            „{{ aiResult.extracted.kennzahlenText }}"
          </div>
          <div class="space-y-2">
            <label v-for="field in aiFieldList" :key="field.key"
              :class="['flex items-center gap-3 p-3 rounded-lg border', aiAccept[field.key] ? 'bg-purple-50 border-purple-200' : 'bg-white border-gray-100']">
              <input type="checkbox" v-model="aiAccept[field.key]" :disabled="!hasValue(field.key)" class="rounded text-[#0088ba]" />
              <div class="flex-1 min-w-0">
                <div class="text-xs font-medium text-gray-600">{{ field.label }}</div>
                <div :class="['text-sm', hasValue(field.key) ? 'text-gray-900 font-semibold' : 'text-gray-300 italic']">
                  {{ hasValue(field.key) ? aiResult.extracted[field.key] : '— nicht erkannt —' }}
                </div>
              </div>
            </label>
          </div>
          <div v-if="aiResult.tokens" class="mt-4 text-[11px] text-gray-400 text-right">
            Token verbraucht: {{ aiResult.tokens.input }} input / {{ aiResult.tokens.output }} output
          </div>
        </div>
        <div class="flex gap-3 p-4 border-t border-gray-100 bg-gray-50">
          <button @click="aiResult = null" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl bg-white hover:bg-gray-50">Verwerfen</button>
          <button @click="applyAiSuggestions" :disabled="!aiAcceptedCount || aiApplying"
            class="flex-1 px-4 py-2 bg-purple-600 text-white rounded-xl text-sm font-semibold hover:bg-purple-700 disabled:opacity-50">
            {{ aiApplying ? 'Übernehme…' : `${aiAcceptedCount} Wert(e) übernehmen` }}
          </button>
        </div>
      </div>
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
            <video :src="previewUrl" controls preload="metadata" class="max-h-full max-w-full"></video>
          </div>
          <div v-else-if="previewType === 'audio'" class="h-full flex items-center justify-center p-4">
            <audio :src="previewUrl" controls preload="metadata" class="w-full max-w-md"></audio>
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
import { Folder, Upload, FileText, Download, Trash2, Eye, X, Image as ImageIcon, Video, Music, FileType2, Sparkles } from '@lucide/vue'
import { authFetch, aiAnalyzeDocument, updateTarget } from '../../api.js'
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
        blobName: sas.blobName,
        contentType: f.type || 'application/octet-stream',
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
    // Bei Video/Audio: direkte SAS-URL fürs Streaming (Range-Requests, Seeking).
    // Bei PDF/Bild/Text: download via API + blob (kleinere Dateien, einfacher Auth).
    if (previewType.value === 'video' || previewType.value === 'audio') {
      const sas = await authFetch('/dokument-stream-url', { method: 'POST', data: { targetId: props.targetId, id: f.RowKey } })
      previewUrl.value = sas.streamUrl
    } else {
      const base = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'
      const token = sessionStorage.getItem('customerJwt') || sessionStorage.getItem('msalToken') || ''
      const r = await fetch(`${base}/dokument-download?targetId=${props.targetId}&id=${f.RowKey}`, {
        headers: { 'Authorization': 'Bearer ' + token }
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      if (previewType.value === 'text') {
        previewText.value = await r.text()
      } else {
        const mimeMap = { pdf: 'application/pdf', image: f.contentType || 'image/jpeg' }
        const ab = await r.arrayBuffer()
        const blob = new Blob([ab], { type: mimeMap[previewType.value] || f.contentType || 'application/octet-stream' })
        previewUrl.value = URL.createObjectURL(blob)
      }
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

// ============== KI-Analyse ==============
function isPdf(f) {
  const n = (f.fileName || '').toLowerCase()
  const ct = (f.contentType || '').toLowerCase()
  return ct === 'application/pdf' || n.endsWith('.pdf')
}

const aiResult = ref(null)        // { extracted: {...}, dokumentTyp, tokens }
const aiAccept = ref({})          // { feldname: true/false }
const aiApplying = ref(false)

const aiFieldList = [
  { key: 'geschaeftsfuehrer', label: 'Geschäftsführer', kind: 'kontakt-or-target' },
  { key: 'branche', label: 'Branche', kind: 'both' },
  { key: 'mitarbeiter', label: 'Mitarbeiter', kind: 'both' },
  { key: 'umsatzTeur', label: 'Umsatz (TEUR)', kind: 'target-as-umsatz' },
  { key: 'ebitMarge', label: 'EBIT-Marge (%)', kind: 'target-only-meta' },
  { key: 'recurringPct', label: 'Wiederkehrender Umsatz (%)', kind: 'target-only-meta' },
  { key: 'rechtsform', label: 'Rechtsform', kind: 'meta' },
  { key: 'gruendungsjahr', label: 'Gründungsjahr', kind: 'meta' },
]

function hasValue(key) {
  if (!aiResult.value) return false
  const v = aiResult.value.extracted[key]
  return v !== null && v !== undefined && v !== ''
}

const aiAcceptedCount = computed(() =>
  Object.entries(aiAccept.value).filter(([k, v]) => v && hasValue(k)).length
)

async function aiAnalyze(f) {
  if (!isPdf(f)) { toast.warn('KI-Analyse aktuell nur für PDFs'); return }
  // 1) Pruefen ob Akte schon fuer KI freigegeben ist
  try {
    const target = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (!target.kiAnalyseErlaubt) {
      const ok = confirm(
        'KI-Analyse für diese Akte freigeben?\n\n' +
        'Das PDF wird einmalig an Anthropic Claude (USA) übermittelt zur Auswertung. ' +
        'Anthropic verarbeitet die Daten als Auftragsverarbeiter und nutzt sie NICHT zum Training. ' +
        'Aufbewahrung bei Anthropic max. 30 Tage. AVV liegt vor.\n\n' +
        'Klicke OK um diese Akte einmalig für KI-Analyse freizugeben.'
      )
      if (!ok) return
      await updateTarget(props.targetId, {
        kiAnalyseErlaubt: true,
        kiAnalyseErlaubtSeit: new Date().toISOString(),
        kiAnalyseErlaubtVon: sessionStorage.getItem('userName') || '',
      })
      toast.success('Akte für KI-Analyse freigegeben')
    }
  } catch (e) { /* nicht-blockierend */ }

  toast.info('KI analysiert das Dokument… kann 10-30 Sekunden dauern')
  try {
    const r = await aiAnalyzeDocument(props.targetId, f.blobName)
    aiResult.value = r
    // Standard: alle erkannten Werte vorhaken
    aiAccept.value = {}
    for (const field of aiFieldList) {
      aiAccept.value[field.key] = hasValue(field.key)
    }
  } catch (e) {
    const msg = e?.response?.data?.error || e.message
    toast.error('KI-Analyse fehlgeschlagen: ' + msg)
  }
}

async function applyAiSuggestions() {
  if (!aiResult.value) return
  aiApplying.value = true
  try {
    // Werte sammeln — alle Felder landen direkt am Target (keine versteckten JSON-Blobs)
    const payload = {}
    for (const field of aiFieldList) {
      if (!aiAccept.value[field.key] || !hasValue(field.key)) continue
      const val = aiResult.value.extracted[field.key]
      // umsatzTeur (Zahl) wird zu umsatz (Freitext: „2,5 Mio. €") konvertiert
      if (field.key === 'umsatzTeur' && val) {
        const mio = val / 1000
        payload.umsatz = `${mio.toFixed(1).replace('.', ',')} Mio. €`.replace(',0 Mio', ' Mio')
      } else if (['mitarbeiter', 'gruendungsjahr', 'ebitMarge', 'recurringPct'].includes(field.key)) {
        payload[field.key] = Number(val) || val
      } else if (['branche', 'geschaeftsfuehrer', 'rechtsform'].includes(field.key)) {
        payload[field.key] = String(val)
      }
    }
    // Kennzahlen-Text + Metadaten zusätzlich als KI-Stand-Vermerk speichern
    if (aiResult.value.extracted.kennzahlenText) {
      payload.bewertungKIJson = JSON.stringify({
        kennzahlenText: aiResult.value.extracted.kennzahlenText,
        quelle: 'KI-Analyse',
        stand: new Date().toISOString(),
        dokumentTyp: aiResult.value.dokumentTyp || '',
      })
    }
    if (Object.keys(payload).length) {
      await updateTarget(props.targetId, payload)
    }
    // 2) Verlauf-Eintrag „KI-Analyse: …" (eigener Endpoint - auch ohne ai-agent rolle, weil admin)
    try {
      await authFetch('/ai-verlauf-add', { method: 'POST', data: {
        targetId: props.targetId,
        typ: 'ki_analyse',
        betreff: `KI-Analyse: ${aiResult.value.dokumentTyp || 'Dokument'}`,
        beschreibung: aiResult.value.extracted.kennzahlenText || 'Werte wurden aus Dokument extrahiert und übernommen.',
      }})
    } catch {}
    toast.success(`${aiAcceptedCount.value} Wert(e) übernommen + Verlauf-Eintrag erstellt`)
    aiResult.value = null
  } catch (e) {
    toast.error('Übernehmen fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally {
    aiApplying.value = false
  }
}
</script>
