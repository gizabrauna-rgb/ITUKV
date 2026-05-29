<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
    <div class="bg-white rounded-2xl w-full max-w-2xl h-[80vh] flex flex-col shadow-2xl">
      <header class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-9 h-9 rounded-full bg-purple-100 flex items-center justify-center">
            <Sparkles class="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 class="font-bold text-gray-900">Assistent</h3>
            <p class="text-xs text-gray-500">Antwortet zu M&amp;A-Themen rund ums ITUKV-Dashboard</p>
          </div>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <X class="w-5 h-5" />
        </button>
      </header>

      <main ref="chatEl" class="flex-1 overflow-y-auto p-5 space-y-3 bg-gray-50">
        <div v-if="!messages.length" class="text-center py-12">
          <Sparkles class="w-10 h-10 text-purple-300 mx-auto mb-3" />
          <p class="text-sm text-gray-500">Stell deine Frage zum M&amp;A-Prozess oder zum Dashboard.</p>
          <div class="mt-4 space-y-2 max-w-md mx-auto">
            <button v-for="bsp in beispieleFragen" :key="bsp" @click="frage = bsp; senden()"
              class="block w-full text-left text-xs px-3 py-2 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 text-gray-600">
              💬 {{ bsp }}
            </button>
          </div>
        </div>

        <div v-for="(m, i) in messages" :key="i"
          :class="['flex gap-2', m.role === 'user' ? 'justify-end' : 'justify-start']">
          <div :class="['max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap',
                       m.role === 'user' ? 'bg-[#0088ba] text-white' : 'bg-white border border-gray-100 text-gray-800']">
            {{ m.text }}
          </div>
        </div>

        <div v-if="loading" class="flex gap-2 justify-start">
          <div class="bg-white border border-gray-100 rounded-2xl px-4 py-2.5 text-sm text-gray-500 italic">
            Einen Moment…
          </div>
        </div>
      </main>

      <footer class="px-5 py-3 border-t border-gray-100">
        <div class="flex gap-2">
          <textarea v-model="frage" @keydown.enter.exact.prevent="senden" rows="2"
            placeholder="Deine Frage… (Enter zum Senden, Shift+Enter für neue Zeile)"
            class="flex-1 px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-300 resize-none"></textarea>
          <button @click="senden" :disabled="!frage.trim() || loading"
            class="px-5 py-2 bg-purple-600 text-white rounded-xl text-sm font-medium hover:bg-purple-700 disabled:opacity-50 self-end">
            <Send class="w-4 h-4" />
          </button>
        </div>
        <p class="text-[10px] text-gray-400 mt-1.5">
          Allgemeine Antworten. Für individuelle Beratung: Jenny (jk@mike-bergmann.de).
        </p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { Sparkles, X, Send } from '@lucide/vue'
import { authFetch } from '../api.js'

const props = defineProps({
  kontext: { type: String, default: '' },
  beispieleFragen: { type: Array, default: () => [
    'Was bedeutet Earn-Out?',
    'Wie lange dauert ein typischer Unternehmensverkauf?',
    'Was kommt bei der Due Diligence auf mich zu?',
    'Welche Unterlagen brauche ich für die Bewertung?',
  ]}
})
defineEmits(['close'])

const frage = ref('')
const messages = ref([])
const loading = ref(false)
const chatEl = ref(null)

async function senden() {
  const text = frage.value.trim()
  if (!text || loading.value) return
  messages.value.push({ role: 'user', text })
  frage.value = ''
  loading.value = true
  await scrollDown()
  try {
    const r = await authFetch('/ai-action', { method: 'POST', data: {
      action: 'frag-ki',
      frage: text,
      kontext: props.kontext || '',
      conversation: messages.value.slice(0, -1).map(m => ({ role: m.role, text: m.text })),
    }})
    messages.value.push({ role: 'assistant', text: r.text || 'Keine Antwort erhalten.' })
  } catch (e) {
    messages.value.push({ role: 'assistant', text: '⚠️ Fehler: ' + (e?.response?.data?.error || e.message) })
  } finally {
    loading.value = false
    await scrollDown()
  }
}

async function scrollDown() {
  await nextTick()
  if (chatEl.value) chatEl.value.scrollTop = chatEl.value.scrollHeight
}
</script>
