<template>
  <div>
    <div class="mb-5">
      <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
        <Users class="w-6 h-6 text-[#0088ba]" /> Vorschläge von mibeca
      </h2>
      <p class="text-sm text-gray-500 mt-1">Hier siehst du die Target-Vorschläge, die mibeca für dich freigegeben hat. Bitte gib pro Vorschlag dein Feedback.</p>
    </div>

    <div v-if="loading" class="text-center text-sm text-gray-400 py-10">Lade Vorschläge…</div>

    <div v-else-if="!vorschlaege.length" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">
      <Users class="w-10 h-10 mx-auto mb-3 text-gray-200" />
      Noch keine Vorschläge von mibeca. Sobald passende Kandidaten gefunden sind, siehst du sie hier.
    </div>

    <div v-else class="space-y-3">
      <div v-for="k in vorschlaege" :key="k.id" class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-start justify-between gap-3 mb-3">
          <div class="flex-1 min-w-0">
            <div class="font-bold text-base text-gray-900">{{ k.firma }}</div>
            <div v-if="k.name" class="text-sm text-gray-700 mt-0.5">Ansprechpartner: {{ k.name }}</div>
            <div class="text-xs text-gray-500 mt-1">
              <span v-if="k.plz || k.ort">{{ k.plz }} {{ k.ort }}</span>
              <span v-if="k.mitarbeiter"> · {{ k.mitarbeiter }} Mitarbeiter</span>
              <span v-if="k.umsatz"> · {{ k.umsatz }}</span>
            </div>
          </div>
          <!-- Status-Badge (nur wenn schon Feedback gegeben) -->
          <div v-if="feedback[k.id]?.interesse" class="flex-shrink-0">
            <span v-if="feedback[k.id].interesse === 'ja'" class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium flex items-center gap-1">
              <Check class="w-3 h-3" /> Interesse
            </span>
            <span v-else-if="feedback[k.id].interesse === 'nein'" class="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full font-medium flex items-center gap-1">
              <X class="w-3 h-3" /> Kein Interesse
            </span>
            <span v-else-if="feedback[k.id].interesse === 'rueckfrage'" class="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-full font-medium flex items-center gap-1">
              <MessageCircle class="w-3 h-3" /> Rückfrage
            </span>
          </div>
        </div>

        <!-- Feedback-Buttons -->
        <div class="flex gap-2 mt-3">
          <button @click="setFeedback(k.id, 'ja')" :class="['flex-1 px-3 py-2 rounded-xl text-sm font-medium border-2 transition-colors flex items-center justify-center gap-1.5',
            feedback[k.id]?.interesse === 'ja' ? 'bg-green-500 text-white border-green-500' : 'border-gray-200 text-gray-600 hover:border-green-300']">
            <Check class="w-4 h-4" /> Interesse
          </button>
          <button @click="setFeedback(k.id, 'rueckfrage')" :class="['flex-1 px-3 py-2 rounded-xl text-sm font-medium border-2 transition-colors flex items-center justify-center gap-1.5',
            feedback[k.id]?.interesse === 'rueckfrage' ? 'bg-amber-500 text-white border-amber-500' : 'border-gray-200 text-gray-600 hover:border-amber-300']">
            <MessageCircle class="w-4 h-4" /> Rückfrage
          </button>
          <button @click="setFeedback(k.id, 'nein')" :class="['flex-1 px-3 py-2 rounded-xl text-sm font-medium border-2 transition-colors flex items-center justify-center gap-1.5',
            feedback[k.id]?.interesse === 'nein' ? 'bg-red-500 text-white border-red-500' : 'border-gray-200 text-gray-600 hover:border-red-300']">
            <X class="w-4 h-4" /> Kein Interesse
          </button>
        </div>

        <!-- Kommentar -->
        <div v-if="feedback[k.id]?.interesse" class="mt-3">
          <textarea v-model="feedback[k.id].kommentar" @blur="save" rows="2"
            placeholder="Kommentar an mibeca (optional, z.B. Begründung oder Rückfrage)"
            class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 resize-y"></textarea>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Users, Check, X, MessageCircle } from '@lucide/vue'
import { authFetch, getKontakte } from '../../api.js'

const props = defineProps({ targetId: String })

const allKontakte = ref([])
const allTargets = ref([])
const fuerKaeuferIds = ref([])
const feedback = ref({})
const loading = ref(true)

const vorschlaege = computed(() => {
  const result = []
  for (const id of fuerKaeuferIds.value) {
    const k = allKontakte.value.find(x => (x.RowKey || x.id) === id)
    if (k) {
      result.push({ ...k, id: k.RowKey || k.id })
      continue
    }
    if (id.startsWith && id.startsWith('target-')) {
      const tid = id.slice(7)
      const tt = allTargets.value.find(t => t.RowKey === tid)
      if (tt) {
        result.push({
          id, firma: tt.verkaueferName || tt.firma || tt.mbNr,
          name: tt.gfName || tt.verkaueferName || '',
          plz: tt.plz, ort: tt.region || tt.ort,
          mitarbeiter: tt.mitarbeiter, umsatz: tt.umsatz,
        })
      }
    }
  }
  return result
})

function setFeedback(id, interesse) {
  if (!feedback.value[id]) feedback.value[id] = { interesse: '', kommentar: '' }
  feedback.value[id].interesse = interesse
  save()
}

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, kaeuferFeedbackJson: JSON.stringify(feedback.value) } })
    } catch (e) { console.error(e) }
  }, 400)
}

onMounted(async () => {
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    try { fuerKaeuferIds.value = JSON.parse(t.fuerKaeuferIdsJson || '[]') } catch {}
    try { feedback.value = JSON.parse(t.kaeuferFeedbackJson || '{}') } catch {}
    allKontakte.value = (await getKontakte()) || []
    try {
      const tres = await authFetch('/targets')
      allTargets.value = tres || []
    } catch {}
  } catch (e) { console.error(e) }
  finally { loading.value = false }
})
</script>
