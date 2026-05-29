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
          <div v-if="m.role === 'user'"
            class="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap bg-[#0088ba] text-white">
            {{ m.text }}
          </div>
          <div v-else
            class="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm bg-white border border-gray-100 text-gray-800 assi-md"
            v-html="renderMd(m.text)"></div>
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

// Minimaler Markdown-Renderer fuer Assistent-Antworten.
// Unterstuetzt: H2/H3, bold, italic, code, Listen (- / *), nummerierte Listen,
// Tabellen (Pipe-Format) und Absaetze.
function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
function renderMd(text) {
  if (!text) return ''
  const lines = text.split('\n')
  const out = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    // Horizontal rule
    if (/^---+\s*$/.test(line)) { out.push('<hr/>'); i++; continue }
    // Headings
    const h = line.match(/^(#{1,6})\s+(.+)$/)
    if (h) {
      const lvl = Math.min(h[1].length + 1, 6)  // # -> h2 (h1 nicht im chat)
      out.push(`<h${lvl}>${inline(h[2])}</h${lvl}>`)
      i++; continue
    }
    // Tables (Pipe-Format)
    if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\s*\|[\s\-:|]+\|\s*$/.test(lines[i+1])) {
      const header = splitRow(line)
      i += 2
      const rows = []
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
        rows.push(splitRow(lines[i]))
        i++
      }
      out.push('<table><thead><tr>' + header.map(c => `<th>${inline(c)}</th>`).join('') + '</tr></thead><tbody>'
        + rows.map(r => '<tr>' + r.map(c => `<td>${inline(c)}</td>`).join('') + '</tr>').join('')
        + '</tbody></table>')
      continue
    }
    // Lists
    if (/^\s*[-*]\s+/.test(line)) {
      const items = []
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ''))
        i++
      }
      out.push('<ul>' + items.map(it => `<li>${inline(it)}</li>`).join('') + '</ul>')
      continue
    }
    if (/^\s*\d+\.\s+/.test(line)) {
      const items = []
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ''))
        i++
      }
      out.push('<ol>' + items.map(it => `<li>${inline(it)}</li>`).join('') + '</ol>')
      continue
    }
    // Leerzeile -> Paragraph-Break
    if (line.trim() === '') { out.push(''); i++; continue }
    // Sonst: Absatz (mit folgenden nicht-leeren Zeilen zusammen)
    const para = [line]
    while (i + 1 < lines.length && lines[i+1].trim() !== ''
           && !/^(#{1,6})\s+/.test(lines[i+1])
           && !/^\s*[-*]\s+/.test(lines[i+1])
           && !/^\s*\d+\.\s+/.test(lines[i+1])
           && !/^\s*\|.*\|\s*$/.test(lines[i+1])) {
      i++
      para.push(lines[i])
    }
    out.push(`<p>${inline(para.join(' '))}</p>`)
    i++
  }
  return out.join('')
}
function splitRow(line) {
  return line.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map(c => c.trim())
}
function inline(s) {
  s = escapeHtml(s)
  // bold + italic
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/__([^_]+)__/g, '<strong>$1</strong>')
  s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  // inline code
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>')
  return s
}
</script>

<style scoped>
@reference "tailwindcss";
.assi-md :deep(h2) { @apply text-base font-bold mt-3 mb-1.5; }
.assi-md :deep(h3) { @apply text-sm font-bold mt-2 mb-1; }
.assi-md :deep(h4), .assi-md :deep(h5), .assi-md :deep(h6) { @apply text-sm font-semibold mt-2 mb-1; }
.assi-md :deep(p) { @apply mb-2 leading-relaxed; }
.assi-md :deep(p:last-child) { @apply mb-0; }
.assi-md :deep(strong) { @apply font-semibold; }
.assi-md :deep(em) { @apply italic; }
.assi-md :deep(ul) { @apply list-disc ml-5 mb-2 space-y-0.5; }
.assi-md :deep(ol) { @apply list-decimal ml-5 mb-2 space-y-0.5; }
.assi-md :deep(li) { @apply leading-snug; }
.assi-md :deep(code) { @apply bg-gray-100 text-purple-700 px-1 py-0.5 rounded text-xs; }
.assi-md :deep(table) { @apply w-full text-xs border border-gray-200 my-2 rounded overflow-hidden; }
.assi-md :deep(thead) { @apply bg-gray-50; }
.assi-md :deep(th) { @apply text-left px-2 py-1.5 font-semibold border-b border-gray-200; }
.assi-md :deep(td) { @apply px-2 py-1 border-b border-gray-100; }
.assi-md :deep(hr) { @apply border-gray-100 my-2; }
</style>
