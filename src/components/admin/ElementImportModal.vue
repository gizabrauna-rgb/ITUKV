<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
    <div class="bg-white rounded-2xl w-full max-w-xl shadow-2xl max-h-[85vh] flex flex-col">
      <header class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="font-bold text-gray-900">Element-Verlauf importieren</h3>
          <p class="text-xs text-gray-500">Element/Matrix-JSON-Export einmalig in diesen Verlauf einkippen</p>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600"><X class="w-5 h-5" /></button>
      </header>

      <main class="p-5 flex-1 overflow-y-auto space-y-4">
        <!-- Schritt 1: Datei -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">1. Element-Export-Datei (.json)</label>
          <input ref="fileInput" type="file" accept=".json,application/json" @change="onFile"
            class="block w-full text-sm border border-gray-200 rounded-xl px-3 py-2 file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:bg-[#0088ba] file:text-white file:text-xs" />
          <p v-if="fileName" class="text-[11px] text-gray-500 mt-1">Datei: <strong>{{ fileName }}</strong> ({{ formatSize(fileSize) }})</p>
        </div>

        <!-- Schritt 2: mibeca-Sender -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">2. Matrix-ID des mibeca-Beraters <span class="text-gray-400">(optional)</span></label>
          <input v-model="mibecaSenderId" placeholder="z.B. @jenny:matrix.mibeca.de"
            class="block w-full text-sm border border-gray-200 rounded-xl px-3 py-2" />
          <p class="text-[11px] text-gray-500 mt-1">
            Nachrichten dieses Senders werden als „ausgehende" mail_out markiert.
            Rest als „eingehende" mail_in. Findest du in Element → eigenes Profil-Icon → Mein Profil.
          </p>
        </div>

        <!-- Schritt 3: Vorschau (nach dry-run) -->
        <div v-if="preview" class="bg-blue-50 border border-blue-100 rounded-xl p-3">
          <h4 class="text-sm font-semibold text-blue-900 mb-2">
            Vorschau: {{ preview.foundMessages }} Nachricht(en) gefunden
          </h4>
          <ul class="text-xs text-blue-900 space-y-1.5">
            <li v-for="(p, i) in preview.preview" :key="i" class="flex gap-2">
              <span :class="['text-[10px] px-1.5 py-0.5 rounded font-semibold flex-shrink-0',
                p.typ === 'mail_out' ? 'bg-[#0088ba] text-white' : 'bg-gray-200 text-gray-700']">
                {{ p.typ === 'mail_out' ? 'mibeca' : 'Mandant' }}
              </span>
              <span class="font-mono text-[10px] text-gray-500 flex-shrink-0">{{ formatDate(p.datum) }}</span>
              <span class="text-gray-800">{{ p.autor }}:</span>
              <span class="text-gray-700 italic truncate">"{{ p.body }}…"</span>
            </li>
          </ul>
        </div>

        <!-- Ergebnis nach Import -->
        <div v-if="result" class="bg-green-50 border border-green-200 rounded-xl p-3 text-sm text-green-900">
          ✅ <strong>{{ result.imported }}</strong> neue Verlauf-Einträge importiert.
          <span v-if="result.skipped > 0"> {{ result.skipped }} Doubletten übersprungen.</span>
        </div>

        <!-- Fehler -->
        <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-800">
          ⚠️ {{ error }}
        </div>

        <!-- Hinweis -->
        <div class="bg-amber-50 border border-amber-100 rounded-xl p-3 text-xs text-amber-900">
          <strong>Wichtig:</strong> Klicke erst auf <strong>„Vorschau"</strong>, schaue ob das Mapping passt,
          dann auf <strong>„Importieren"</strong>. Bereits importierte Nachrichten werden via Event-ID
          automatisch übersprungen — du kannst den Import gefahrlos mehrfach laufen lassen.
        </div>
      </main>

      <footer class="px-5 py-3 border-t border-gray-100 flex items-center justify-between gap-2">
        <button @click="$emit('close')" class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">Abbrechen</button>
        <div class="flex gap-2">
          <button @click="run(true)" :disabled="!fileData || busy"
            class="px-4 py-1.5 text-xs border border-blue-200 text-blue-700 rounded-lg hover:bg-blue-50 disabled:opacity-50">
            {{ busy && lastWasDry ? 'Prüfe…' : 'Vorschau' }}
          </button>
          <button @click="run(false)" :disabled="!fileData || busy"
            class="px-4 py-1.5 text-xs bg-[#0088ba] text-white rounded-lg hover:bg-[#00a0d8] disabled:opacity-50">
            {{ busy && !lastWasDry ? 'Importiere…' : 'Importieren' }}
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { X } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: { type: String, required: true } })
const emit = defineEmits(['close', 'imported'])

const fileInput = ref(null)
const fileData = ref('')
const fileName = ref('')
const fileSize = ref(0)
const mibecaSenderId = ref('')
const preview = ref(null)
const result = ref(null)
const error = ref('')
const busy = ref(false)
const lastWasDry = ref(false)

function onFile(e) {
  const f = e.target.files?.[0]
  if (!f) return
  fileName.value = f.name
  fileSize.value = f.size
  error.value = ''
  preview.value = null
  result.value = null
  const reader = new FileReader()
  reader.onload = () => {
    // Nur Base64 nach dem Komma
    const b64 = (reader.result || '').toString().split(',')[1] || ''
    fileData.value = b64
  }
  reader.readAsDataURL(f)
}

async function run(dryRun) {
  if (!fileData.value) return
  busy.value = true
  lastWasDry.value = dryRun
  error.value = ''
  if (dryRun) result.value = null
  try {
    const r = await authFetch('/element-import', { method: 'POST', data: {
      targetId: props.targetId,
      fileData: fileData.value,
      mibecaSenderId: mibecaSenderId.value || '',
      dryRun,
    }})
    if (dryRun) {
      preview.value = r
    } else {
      result.value = r
      emit('imported', r)
    }
  } catch (e) {
    error.value = e?.response?.data?.error || e.message
  } finally { busy.value = false }
}

function formatSize(b) {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / 1024 / 1024).toFixed(1)} MB`
}
function formatDate(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleDateString('de-DE') } catch { return '' }
}
</script>
