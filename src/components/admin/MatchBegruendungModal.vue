<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
    <div class="bg-white rounded-2xl w-full max-w-lg shadow-2xl">
      <header class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-9 h-9 rounded-full bg-purple-100 flex items-center justify-center">
            <Sparkles class="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 class="font-bold text-gray-900">Match-Bewertung</h3>
            <p class="text-xs text-gray-500">{{ kontaktName }}</p>
          </div>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600"><X class="w-5 h-5" /></button>
      </header>

      <main class="p-5 max-h-[65vh] overflow-y-auto">
        <div v-if="loading" class="py-12 text-center">
          <Loader class="w-8 h-8 text-purple-400 mx-auto animate-spin mb-3" />
          <p class="text-sm text-gray-500">Assistent bewertet Match…</p>
        </div>
        <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-800 flex items-start gap-2">
          <AlertCircle class="w-4 h-4 flex-shrink-0 mt-0.5" /> <span>{{ error }}</span>
        </div>
        <div v-else>
          <!-- Score-Kreis -->
          <div class="flex items-center gap-4 mb-4">
            <div :class="['w-20 h-20 rounded-full flex items-center justify-center text-2xl font-bold flex-shrink-0',
                          score >= 70 ? 'bg-green-100 text-green-700' :
                          score >= 40 ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700']">
              {{ score }}%
            </div>
            <div class="flex-1">
              <h4 class="font-semibold text-gray-900 text-sm">{{ matchLabel }}</h4>
              <p v-if="begruendung" class="text-xs text-gray-600 mt-1">{{ begruendung }}</p>
            </div>
          </div>

          <!-- Pro -->
          <div v-if="pro.length" class="mb-3">
            <h5 class="text-xs font-semibold text-green-700 uppercase tracking-wide mb-1.5 flex items-center gap-1"><Check class="w-3 h-3" /> Spricht dafür</h5>
            <ul class="space-y-1">
              <li v-for="(p, i) in pro" :key="i" class="text-sm text-gray-700 bg-green-50 border border-green-100 rounded-lg px-3 py-1.5">{{ p }}</li>
            </ul>
          </div>

          <!-- Contra -->
          <div v-if="contra.length">
            <h5 class="text-xs font-semibold text-red-700 uppercase tracking-wide mb-1.5 flex items-center gap-1"><XCircle class="w-3 h-3" /> Spricht dagegen</h5>
            <ul class="space-y-1">
              <li v-for="(c, i) in contra" :key="i" class="text-sm text-gray-700 bg-red-50 border border-red-100 rounded-lg px-3 py-1.5">{{ c }}</li>
            </ul>
          </div>
        </div>
      </main>

      <footer class="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
        <span class="text-[10px] text-gray-400" v-if="tokens">Tokens: {{ tokens.input }} in / {{ tokens.output }} out</span>
        <button @click="$emit('close')" class="ml-auto px-4 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700">
          Schließen
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Sparkles, X, Loader, AlertCircle, Check, XCircle } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({
  targetId: { type: String, required: true },
  kontaktId: { type: String, required: true },
  kontaktName: { type: String, default: '' },
})
defineEmits(['close'])

const loading = ref(true)
const error = ref('')
const score = ref(0)
const pro = ref([])
const contra = ref([])
const begruendung = ref('')
const tokens = ref(null)

const matchLabel = computed(() => {
  if (score.value >= 80) return 'Sehr gutes Match'
  if (score.value >= 60) return 'Solides Match'
  if (score.value >= 40) return 'Mittelmäßiges Match'
  return 'Schwaches Match'
})

onMounted(async () => {
  try {
    const r = await authFetch('/ai-action', { method: 'POST', data: {
      action: 'match-begruendung',
      targetId: props.targetId,
      kontaktId: props.kontaktId,
    }})
    if (r.error) { error.value = r.error; return }
    score.value = Number(r.score) || 0
    pro.value = Array.isArray(r.pro) ? r.pro : []
    contra.value = Array.isArray(r.contra) ? r.contra : []
    begruendung.value = r.begruendung || ''
    tokens.value = r.tokens || null
  } catch (e) {
    error.value = e?.response?.data?.error || e.message
  } finally { loading.value = false }
})
</script>
