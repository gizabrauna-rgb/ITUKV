<template>
  <div v-if="text" class="bg-white rounded-xl border-2 border-amber-200 p-5 mb-4">
    <div class="flex items-start gap-3 mb-3">
      <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
        <FileText class="w-5 h-5 text-amber-600" />
      </div>
      <div class="flex-1">
        <h3 class="font-bold text-gray-900">Pressetext zur Freigabe</h3>
        <p class="text-xs text-gray-500">mibeca hat einen Pressetext zu deinem Unternehmensverkauf vorbereitet. Bitte freigeben oder kommentieren.</p>
      </div>
    </div>

    <!-- Status-Banner -->
    <div v-if="status === 'freigegeben'" class="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800 mb-3 flex items-center gap-2">
      <CheckCircle2 class="w-4 h-4" /> Du hast den Pressetext freigegeben.
    </div>
    <div v-else-if="status === 'aenderung_gewuenscht'" class="bg-orange-50 border border-orange-200 rounded-lg p-3 text-sm text-orange-800 mb-3">
      <div class="flex items-center gap-2"><AlertCircle class="w-4 h-4" /> Du hast Änderungen angefragt:</div>
      <p v-if="kommentarVor" class="text-xs ml-6 italic mt-1">„{{ kommentarVor }}"</p>
    </div>

    <!-- Pressetext (read-only) -->
    <div class="bg-gray-50 border border-gray-100 rounded-lg p-4 mb-3 max-h-96 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-gray-800">{{ text }}</div>

    <!-- Kommentar -->
    <label class="text-xs text-gray-600 mb-1 block">Kommentar / Änderungswunsch (optional)</label>
    <textarea v-model="kommentar" rows="3" placeholder="z.B. 'Im 3. Absatz bitte unsere Tochterfirma X auch erwähnen.'" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 resize-y mb-3"></textarea>

    <div class="flex gap-2">
      <button @click="freigeben(false)" :disabled="sending" class="flex-1 px-4 py-2.5 border border-orange-200 text-orange-700 rounded-xl text-sm font-medium hover:bg-orange-50 disabled:opacity-50">
        <AlertCircle class="w-4 h-4 inline" /> Änderungen anfragen
      </button>
      <button @click="freigeben(true)" :disabled="sending" class="flex-1 px-4 py-2.5 bg-green-600 text-white rounded-xl text-sm font-semibold hover:bg-green-700 disabled:opacity-50">
        <CheckCircle2 class="w-4 h-4 inline" /> Freigeben
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { FileText, CheckCircle2, AlertCircle } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })
const text = ref('')
const status = ref('')
const kommentarVor = ref('')
const kommentar = ref('')
const sending = ref(false)

async function freigeben(istFreigabe) {
  if (!istFreigabe && !kommentar.value.trim()) {
    if (!confirm('Bitte gib einen Kommentar mit deinem Änderungswunsch ein. Trotzdem senden?')) return
  }
  sending.value = true
  try {
    await authFetch('/pr-feedback', { method: 'POST', data: { targetId: props.targetId, freigabe: istFreigabe, kommentar: kommentar.value } })
    status.value = istFreigabe ? 'freigegeben' : 'aenderung_gewuenscht'
    kommentarVor.value = kommentar.value
    kommentar.value = ''
    toast.success(istFreigabe ? 'Vielen Dank für die Freigabe! Wir werden den Text zeitnah veröffentlichen.' : 'Vielen Dank für dein Feedback. mibeca passt den Text an.')
  } catch (e) { toast.error('Fehler: ' + (e?.response?.data?.error || e.message)) }
  finally { sending.value = false }
}

onMounted(async () => {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (t.presseJson) {
      try {
        const d = JSON.parse(t.presseJson)
        text.value = d.text || ''
        status.value = d.freigabeStatus || ''
        kommentarVor.value = d.freigabeKommentar || ''
      } catch {}
    }
  } catch (e) { console.error(e) }
})
</script>
