<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
    <div class="bg-white rounded-2xl w-full max-w-2xl shadow-2xl">
      <header class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-9 h-9 rounded-full bg-purple-100 flex items-center justify-center">
            <Sparkles class="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 class="font-bold text-gray-900">Verlauf-Zusammenfassung</h3>
            <p class="text-xs text-gray-500">Schneller Überblick zum aktuellen Stand</p>
          </div>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <X class="w-5 h-5" />
        </button>
      </header>

      <main class="p-5 max-h-[60vh] overflow-y-auto">
        <div v-if="loading" class="py-12 text-center">
          <Loader class="w-8 h-8 text-purple-400 mx-auto animate-spin mb-3" />
          <p class="text-sm text-gray-500">Verlauf wird gerade zusammengefasst…</p>
        </div>
        <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-800">
          ⚠️ {{ error }}
        </div>
        <div v-else-if="text" class="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">{{ text }}</div>
      </main>

      <footer class="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
        <span v-if="tokens" class="text-[10px] text-gray-400">Tokens: {{ tokens.input }} in / {{ tokens.output }} out</span>
        <div class="flex gap-2 ml-auto">
          <button v-if="text" @click="copy" class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">
            {{ copied ? '✓ Kopiert' : 'Kopieren' }}
          </button>
          <button @click="$emit('close')" class="px-4 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700">
            Schließen
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Sparkles, X, Loader } from '@lucide/vue'
import { authFetch } from '../api.js'

const props = defineProps({ targetId: { type: String, required: true } })
defineEmits(['close'])

const loading = ref(true)
const text = ref('')
const tokens = ref(null)
const error = ref('')
const copied = ref(false)

onMounted(async () => {
  try {
    const r = await authFetch('/ai-action', { method: 'POST', data: {
      action: 'verlauf-zusammenfassen',
      targetId: props.targetId,
    }})
    text.value = r.text || ''
    tokens.value = r.tokens || null
  } catch (e) {
    error.value = e?.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
})

async function copy() {
  try {
    await navigator.clipboard.writeText(text.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {}
}
</script>
