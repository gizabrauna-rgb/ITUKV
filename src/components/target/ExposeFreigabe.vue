<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-1">Mein Exposé</h2>
    <p class="text-sm text-gray-500 mb-5">Dein anonymisiertes Kurzexposé für die Marktansprache. Sobald du es freigibst, startet die Ausschreibung.</p>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">Lade…</div>

    <div v-else-if="!hatInhalt" class="bg-white rounded-xl border border-gray-100 p-10 text-center">
      <FileText class="w-12 h-12 mx-auto mb-3 text-gray-200" />
      <h3 class="font-semibold text-gray-700 mb-1">Exposé wird vorbereitet</h3>
      <p class="text-sm text-gray-500">
        Sobald du den Fragebogen ausgefüllt und abgegeben hast, erstellt unser Team das anonymisierte Exposé für dich.
        Es erscheint dann hier zur Freigabe.
      </p>
    </div>

    <div v-else>
      <!-- Status-Box -->
      <div :class="['rounded-xl p-5 mb-4 border', statusBoxClass]">
        <div class="flex items-start gap-3">
          <component :is="statusIcon" class="w-6 h-6 flex-shrink-0 mt-0.5" />
          <div class="flex-1">
            <h3 class="font-bold mb-1">{{ statusTitle }}</h3>
            <p class="text-sm leading-relaxed">{{ statusText }}</p>
          </div>
        </div>
      </div>

      <!-- PDF-Vorschau Button -->
      <div class="mb-4 flex justify-end">
        <button @click="openPdf" :disabled="pdfLoading" class="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50 disabled:opacity-50">
          <FileText class="w-4 h-4" /> {{ pdfLoading ? 'Lade…' : 'PDF-Vorschau öffnen' }}
        </button>
      </div>

      <!-- Exposé-Anzeige -->
      <div class="bg-white rounded-xl border border-gray-100 p-6 mb-4 space-y-5">
        <div v-if="expose.headline || expose.subheadline">
          <h1 v-if="expose.headline" class="text-xl font-bold text-gray-900 mb-1">{{ expose.headline }}</h1>
          <p v-if="expose.subheadline" class="text-sm text-gray-500">{{ expose.subheadline }}</p>
        </div>

        <section v-for="(sec, i) in (expose.sektionen || [])" :key="i" v-show="sec.body">
          <h3 class="font-semibold text-gray-800 mb-1.5">{{ sec.label }}</h3>
          <p class="text-sm text-gray-700 whitespace-pre-line leading-relaxed">{{ sec.body }}</p>
        </section>

        <section v-if="expose.finanzen?.einleitung || expose.finanzen?.jahre?.length">
          <h3 class="font-semibold text-gray-800 mb-1.5">Umsätze, Erträge, finanzielle Situation</h3>
          <p v-if="expose.finanzen.einleitung" class="text-sm text-gray-700 whitespace-pre-line leading-relaxed mb-3">{{ expose.finanzen.einleitung }}</p>
          <table v-if="expose.finanzen.jahre?.length" class="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
            <thead class="bg-gray-50"><tr>
              <th class="text-left px-3 py-2 text-xs uppercase tracking-wide text-gray-500">Position</th>
              <th v-for="j in expose.finanzen.jahre" :key="j" class="text-right px-3 py-2 text-xs uppercase tracking-wide text-gray-500">{{ j }}</th>
            </tr></thead>
            <tbody>
              <tr v-for="(row, ri) in expose.finanzen.rows || []" :key="ri" class="border-t border-gray-100">
                <td class="px-3 py-2 text-gray-700">{{ row.label }}</td>
                <td v-for="(val, ji) in row.werte" :key="ji" class="px-3 py-2 text-right text-gray-700">{{ val }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>

      <!-- Aktion: Freigabe -->
      <div v-if="expose.status === 'awaiting_approval'" class="flex gap-3">
        <button @click="korrekturwunsch" class="flex-1 flex items-center justify-center gap-2 px-4 py-3 border border-amber-200 bg-amber-50 text-amber-700 rounded-xl text-sm font-medium hover:bg-amber-100">
          <MessageSquare class="w-4 h-4" /> Korrekturwunsch
        </button>
        <button @click="freigeben" class="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-700">
          <CheckCircle class="w-4 h-4" /> Exposé freigeben
        </button>
      </div>

      <!-- Korrekturwunsch Modal -->
      <div v-if="showKorrektur" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
        <div class="bg-white rounded-2xl p-6 w-full max-w-md">
          <h3 class="font-bold text-gray-900 mb-2">Korrekturwunsch</h3>
          <p class="text-sm text-gray-500 mb-3">Was sollen wir am Exposé anpassen?</p>
          <textarea v-model="korrekturText" rows="4"
            class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 resize-none"
            placeholder="z.B. Bitte den Umsatz nicht so genau angeben, bitte Branche detaillierter beschreiben..."></textarea>
          <div class="flex gap-3 mt-4">
            <button @click="showKorrektur = false" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
            <button @click="sendKorrektur" :disabled="!korrekturText.trim() || sending" class="flex-1 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium disabled:opacity-50">
              {{ sending ? 'Wird gesendet…' : 'An Jenny senden' }}
            </button>
          </div>
        </div>
      </div>

      <!-- PDF Modal -->
      <div v-if="pdfUrl" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" @click.self="closePdf">
        <div class="bg-white rounded-2xl w-full max-w-4xl h-[90vh] flex flex-col overflow-hidden shadow-2xl">
          <div class="flex items-center justify-between px-5 py-3 border-b border-gray-100">
            <h3 class="font-bold text-gray-900 flex items-center gap-2"><FileText class="w-5 h-5 text-[#0088ba]" /> Exposé-PDF</h3>
            <button @click="closePdf" class="p-1.5 hover:bg-gray-100 rounded-lg"><X class="w-5 h-5 text-gray-500" /></button>
          </div>
          <iframe :src="pdfUrl" class="flex-1 w-full" frameborder="0"></iframe>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { FileText, CheckCircle, MessageSquare, AlertCircle, Loader2, X } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })
const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

const target = ref(null)
const expose = ref({ status: 'draft', headline: '', subheadline: '', sektionen: [], finanzen: {} })
const loading = ref(true)
const showKorrektur = ref(false)
const korrekturText = ref('')
const sending = ref(false)

const hatInhalt = computed(() => !!(expose.value.headline || expose.value.subheadline || (expose.value.sektionen || []).some(s => s.body)))

const statusTitle = computed(() => ({
  draft: 'Exposé in Bearbeitung',
  in_review: 'Exposé wird gerade von uns geprüft',
  awaiting_approval: 'Bitte prüfen und freigeben',
  changes_requested: 'Korrekturwunsch wurde gesendet',
  approved: 'Exposé freigegeben — Ausschreibung läuft!',
})[expose.value.status] || 'Exposé wird vorbereitet')

const statusText = computed(() => ({
  draft: 'Unser Team arbeitet noch am Exposé. Es erscheint hier zur Freigabe, sobald es fertig ist.',
  in_review: 'Wir prüfen das Exposé intern und melden uns bei dir, sobald es zur Freigabe bereit ist.',
  awaiting_approval: 'Wir haben das Exposé für dich vorbereitet. Bitte lies es genau durch und gib es frei — oder schreib uns, was wir noch anpassen sollen.',
  changes_requested: 'Wir haben deinen Korrekturwunsch erhalten und passen das Exposé jetzt an. Du bekommst es danach erneut zur Freigabe.',
  approved: 'Vielen Dank für die Freigabe! Wir beginnen jetzt mit der Marktansprache.',
})[expose.value.status] || '')

const statusIcon = computed(() => ({
  draft: Loader2, in_review: Loader2, awaiting_approval: AlertCircle, changes_requested: MessageSquare, approved: CheckCircle
})[expose.value.status] || Loader2)

const statusBoxClass = computed(() => ({
  draft: 'bg-gray-50 border-gray-200 text-gray-700',
  in_review: 'bg-blue-50 border-blue-200 text-blue-900',
  awaiting_approval: 'bg-amber-50 border-amber-200 text-amber-900',
  changes_requested: 'bg-amber-50 border-amber-200 text-amber-900',
  approved: 'bg-green-50 border-green-200 text-green-900',
})[expose.value.status] || 'bg-gray-50 border-gray-200 text-gray-700')

async function load() {
  if (!props.targetId) { loading.value = false; return }
  try {
    target.value = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (target.value?.exposeJson) {
      try {
        const e = JSON.parse(target.value.exposeJson)
        expose.value = { status: 'draft', headline: '', subheadline: '', sektionen: [], finanzen: {}, ...e }
      } catch {}
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}
onMounted(load)

async function persist(status) {
  const newExpose = { ...expose.value, status }
  await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, exposeJson: JSON.stringify(newExpose) } })
  expose.value = newExpose
}

async function logVerlauf(typ, betreff, beschreibung) {
  try {
    const existing = target.value?.kommunikationJson ? JSON.parse(target.value.kommunikationJson) : []
    existing.unshift({
      id: 'k' + Date.now(),
      typ,
      datum: new Date().toISOString(),
      autor: sessionStorage.getItem('userName') || 'Verkäufer',
      betreff,
      beschreibung,
      beteiligte: 'Verkäufer → mibeca',
    })
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, kommunikationJson: JSON.stringify(existing) } })
  } catch (e) { console.error('verlauf log failed', e) }
}

async function freigeben() {
  if (!confirm('Exposé freigeben? Damit startet die Marktansprache.')) return
  sending.value = true
  try {
    await persist('approved')
    await logVerlauf('wichtig', 'Exposé freigegeben', 'Der Verkäufer hat das Exposé freigegeben. Die Marktansprache kann starten.')
    toast.success('Exposé freigegeben — danke!')
  } catch (e) {
    toast.error('Freigabe fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally { sending.value = false }
}

function korrekturwunsch() { showKorrektur.value = true; korrekturText.value = '' }

async function sendKorrektur() {
  if (!korrekturText.value.trim()) return
  sending.value = true
  try {
    await persist('changes_requested')
    await logVerlauf('wichtig', 'Korrekturwunsch zum Exposé', korrekturText.value.trim())
    showKorrektur.value = false
    toast.success('Korrekturwunsch wurde an Jenny gesendet.')
  } catch (e) {
    toast.error('Senden fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally { sending.value = false }
}

// PDF-Vorschau
const pdfUrl = ref(null)
const pdfLoading = ref(false)
async function openPdf() {
  pdfLoading.value = true
  try {
    const token = sessionStorage.getItem('customerJwt') || sessionStorage.getItem('msalToken') || ''
    const r = await fetch(`${apiBase}/expose-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      body: JSON.stringify({ ...expose.value, mbNr: target.value?.mbNr }),
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value)
    const ab = await r.arrayBuffer()
    pdfUrl.value = URL.createObjectURL(new Blob([ab], { type: 'application/pdf' }))
  } catch (e) { toast.error('PDF-Vorschau fehlgeschlagen: ' + e.message) }
  finally { pdfLoading.value = false }
}
function closePdf() { if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value); pdfUrl.value = null }
</script>
