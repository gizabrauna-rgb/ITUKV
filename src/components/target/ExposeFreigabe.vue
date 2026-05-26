<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-1">Mein Exposé</h2>
    <p class="text-sm text-gray-500 mb-5">Dein anonymisiertes Kurzexposé für die Marktansprache. Sobald du es freigibst, startet die Ausschreibung.</p>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">Lade…</div>

    <div v-else-if="!exposeText" class="bg-white rounded-xl border border-gray-100 p-10 text-center">
      <FileText class="w-12 h-12 mx-auto mb-3 text-gray-200" />
      <h3 class="font-semibold text-gray-700 mb-1">Noch kein Exposé erstellt</h3>
      <p class="text-sm text-gray-500">
        Sobald du den Fragebogen ausgefüllt hast, erstellt unser Team das anonymisierte Exposé für dich.
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

      <!-- Exposé-Anzeige -->
      <div class="bg-white rounded-xl border border-gray-100 p-6 mb-4">
        <pre class="font-serif text-sm leading-relaxed whitespace-pre-wrap text-gray-800">{{ exposeText }}</pre>
      </div>

      <!-- Aktion: Freigabe -->
      <div v-if="exposeStatus === 'awaiting_approval'" class="flex gap-3">
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
            class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 resize-none"
            placeholder="z.B. Bitte den Umsatz nicht so genau angeben, bitte Branche detaillierter beschreiben..."></textarea>
          <div class="flex gap-3 mt-4">
            <button @click="showKorrektur = false" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
            <button @click="sendKorrektur" class="flex-1 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium">An Jenny senden</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { FileText, CheckCircle, MessageSquare, AlertCircle, Loader2 } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })

const target = ref(null)
const exposeText = ref('')
const exposeStatus = ref('')
const loading = ref(true)
const showKorrektur = ref(false)
const korrekturText = ref('')

const statusTitle = computed(() => ({
  draft: 'Exposé wird erstellt',
  in_review: 'Exposé wird gerade von uns geprüft',
  awaiting_approval: 'Bitte prüfen und freigeben',
  approved: 'Exposé freigegeben — Ausschreibung läuft!',
})[exposeStatus.value] || 'Exposé wird erstellt')

const statusText = computed(() => ({
  draft: 'Sobald unser Team das Exposé fertig hat, erscheint es hier.',
  in_review: 'Wir prüfen das Exposé und melden uns bei dir, sobald es zur Freigabe bereit ist.',
  awaiting_approval: 'Wir haben das Exposé für dich vorbereitet. Bitte lies es genau durch und gib es frei — oder schreib uns, was wir noch anpassen sollen.',
  approved: 'Vielen Dank für die Freigabe! Wir beginnen jetzt mit der Marktansprache.',
})[exposeStatus.value] || '')

const statusIcon = computed(() => ({
  draft: Loader2, in_review: Loader2, awaiting_approval: AlertCircle, approved: CheckCircle
})[exposeStatus.value] || Loader2)

const statusBoxClass = computed(() => ({
  draft: 'bg-gray-50 border-gray-200 text-gray-700',
  in_review: 'bg-blue-50 border-blue-200 text-blue-900',
  awaiting_approval: 'bg-amber-50 border-amber-200 text-amber-900',
  approved: 'bg-green-50 border-green-200 text-green-900',
})[exposeStatus.value] || 'bg-gray-50 border-gray-200 text-gray-700')

onMounted(async () => {
  if (!props.targetId) { loading.value = false; return }
  try {
    target.value = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    exposeText.value = target.value.exposeText || ''
    exposeStatus.value = target.value.exposeStatus || 'draft'
  } catch (e) { console.error(e) }
  finally { loading.value = false }
})

async function freigeben() {
  if (!confirm('Exposé freigeben? Damit startet die Ausschreibung.')) return
  exposeStatus.value = 'approved'
  await authFetch('/target-update', { method: 'POST', data: { id: props.targetId,  exposeStatus: 'approved'  } })
}

function korrekturwunsch() {
  showKorrektur.value = true
  korrekturText.value = ''
}

async function sendKorrektur() {
  // Korrekturwunsch als Verlauf-Eintrag speichern + Status zurück zu in_review
  try {
    // Hole bestehende Verlauf-Einträge
    const existing = target.value.kommunikationJson ? JSON.parse(target.value.kommunikationJson) : []
    existing.push({
      id: 'k' + Date.now(),
      typ: 'wichtig',
      datum: new Date().toISOString().slice(0,16),
      autor: sessionStorage.getItem('userName') || 'Verkäufer',
      betreff: 'Korrekturwunsch zum Exposé',
      beschreibung: korrekturText.value,
      beteiligte: 'Verkäufer → Jenny',
    })
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId,  kommunikationJson: JSON.stringify(existing), exposeStatus: 'in_review'  } })
    exposeStatus.value = 'in_review'
    showKorrektur.value = false
    toast.success('Korrekturwunsch wurde an Jenny gesendet — sie passt das Exposé an und gibt es dann erneut frei.')
  } catch (e) { console.error(e); toast.error('Fehler beim Senden') }
}
</script>
