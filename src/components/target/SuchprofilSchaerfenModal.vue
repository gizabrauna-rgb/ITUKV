<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
    <div class="bg-white rounded-2xl w-full max-w-xl shadow-2xl">
      <header class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-9 h-9 rounded-full bg-purple-100 flex items-center justify-center">
            <Sparkles class="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 class="font-bold text-gray-900">Suchprofil schärfen</h3>
            <p class="text-xs text-gray-500">Assistent stellt Rückfragen, die dein Profil verbessern</p>
          </div>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600"><X class="w-5 h-5" /></button>
      </header>

      <main class="p-5 max-h-[60vh] overflow-y-auto">
        <div v-if="loading" class="py-12 text-center">
          <Loader class="w-8 h-8 text-purple-400 mx-auto animate-spin mb-3" />
          <p class="text-sm text-gray-500">Assistent denkt nach…</p>
        </div>
        <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-800 flex items-start gap-2">
          <AlertCircle class="w-4 h-4 flex-shrink-0 mt-0.5" /> <span>{{ error }}</span>
        </div>
        <div v-else>
          <p v-if="begruendung" class="text-xs text-gray-500 italic mb-4">{{ begruendung }}</p>
          <ol class="space-y-3">
            <li v-for="(f, i) in fragen" :key="i"
              class="flex items-start gap-3 bg-purple-50 border border-purple-100 rounded-xl p-3">
              <span class="w-6 h-6 rounded-full bg-purple-600 text-white text-xs font-bold flex items-center justify-center flex-shrink-0">{{ i + 1 }}</span>
              <span class="text-sm text-gray-800">{{ f }}</span>
            </li>
          </ol>
        </div>
      </main>

      <footer class="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
        <span class="text-[10px] text-gray-400" v-if="tokens">Tokens: {{ tokens.input }} in / {{ tokens.output }} out</span>
        <button @click="$emit('close')" class="ml-auto px-4 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700">
          Verstanden
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Sparkles, X, Loader, AlertCircle } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: { type: String, required: true } })
defineEmits(['close'])

const loading = ref(true)
const error = ref('')
const fragen = ref([])
const begruendung = ref('')
const tokens = ref(null)

onMounted(async () => {
  try {
    const r = await authFetch('/ai-action', { method: 'POST', data: {
      action: 'suchprofil-schaerfen',
      targetId: props.targetId,
    }})
    if (r.error) { error.value = r.error; return }
    fragen.value = Array.isArray(r.fragen) ? r.fragen : []
    begruendung.value = r.begruendung || ''
    tokens.value = r.tokens || null
  } catch (e) {
    error.value = e?.response?.data?.error || e.message
  } finally { loading.value = false }
})
</script>
