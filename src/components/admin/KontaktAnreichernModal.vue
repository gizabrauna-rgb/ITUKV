<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
    <div class="bg-white rounded-2xl w-full max-w-xl shadow-2xl max-h-[80vh] flex flex-col">
      <header class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-9 h-9 rounded-full bg-purple-100 flex items-center justify-center">
            <Sparkles class="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 class="font-bold text-gray-900">Mit Assistent anreichern</h3>
            <p class="text-xs text-gray-500">{{ kontakt?.firma || '' }}</p>
          </div>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600"><X class="w-5 h-5" /></button>
      </header>

      <main class="flex-1 overflow-y-auto p-5">
        <div v-if="loading" class="py-12 text-center">
          <Loader class="w-8 h-8 text-purple-400 mx-auto animate-spin mb-3" />
          <p class="text-sm text-gray-500">Assistent recherchiert Stammdaten…</p>
        </div>
        <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-800">⚠️ {{ error }}</div>
        <div v-else-if="vorschlaege">
          <div :class="['mb-4 px-3 py-2 rounded-lg text-xs',
            vorschlaege.konfidenz === 'hoch' ? 'bg-green-50 text-green-800 border border-green-200' :
            vorschlaege.konfidenz === 'mittel' ? 'bg-amber-50 text-amber-800 border border-amber-200' :
            'bg-gray-50 text-gray-700 border border-gray-200']">
            <strong>Konfidenz: {{ vorschlaege.konfidenz || '—' }}</strong>
            <p v-if="vorschlaege.begruendung" class="mt-1">{{ vorschlaege.begruendung }}</p>
          </div>
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr><th class="text-left p-2">Übernehmen</th><th class="text-left p-2">Feld</th><th class="text-left p-2">Vorschlag</th></tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="f in felder" :key="f.key">
                <td class="p-2">
                  <input type="checkbox" v-model="accept[f.key]" :disabled="!hasValue(f.key)" />
                </td>
                <td class="p-2 text-gray-600">{{ f.label }}</td>
                <td class="p-2 font-medium" :class="hasValue(f.key) ? 'text-gray-900' : 'text-gray-300'">
                  {{ hasValue(f.key) ? vorschlaege[f.key] : '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <footer class="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
        <span class="text-[10px] text-gray-400" v-if="tokens">Tokens: {{ tokens.input }} in / {{ tokens.output }} out</span>
        <div class="flex gap-2 ml-auto">
          <button @click="$emit('close')" class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">Abbrechen</button>
          <button v-if="vorschlaege" @click="apply" :disabled="saving || !anyChecked"
            class="px-4 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700 disabled:opacity-50">
            {{ saving ? 'Übernehme…' : `Übernehmen (${checkedCount})` }}
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Sparkles, X, Loader } from '@lucide/vue'
import { authFetch, updateKontakt } from '../../api.js'

const props = defineProps({ kontakt: { type: Object, required: true } })
const emit = defineEmits(['close', 'updated'])

const loading = ref(true)
const error = ref('')
const vorschlaege = ref(null)
const tokens = ref(null)
const accept = ref({})
const saving = ref(false)

const felder = [
  { key: 'geschaeftsfuehrer', label: 'Geschäftsführer' },
  { key: 'branche', label: 'Branche' },
  { key: 'plz', label: 'PLZ' },
  { key: 'ort', label: 'Ort' },
  { key: 'mitarbeiter', label: 'Mitarbeiter' },
  { key: 'umsatzTeur', label: 'Umsatz (TEUR)' },
  { key: 'website', label: 'Website' },
]

function hasValue(k) {
  const v = vorschlaege.value?.[k]
  return v !== null && v !== undefined && v !== '' && v !== 0
}
const anyChecked = computed(() => Object.values(accept.value).some(Boolean))
const checkedCount = computed(() => Object.values(accept.value).filter(Boolean).length)

onMounted(async () => {
  try {
    const r = await authFetch('/ai-action', { method: 'POST', data: {
      action: 'kontakt-anreichern',
      kontaktId: props.kontakt.RowKey,
    }})
    if (r.error) { error.value = r.error; return }
    vorschlaege.value = r.vorschlaege || r
    tokens.value = r.tokens || null
    // Default: alle mit Wert vorhaken
    for (const f of felder) {
      if (hasValue(f.key)) accept.value[f.key] = true
    }
  } catch (e) {
    error.value = e?.response?.data?.error || e.message
  } finally { loading.value = false }
})

async function apply() {
  saving.value = true
  try {
    const payload = {}
    for (const f of felder) {
      if (accept.value[f.key] && hasValue(f.key)) payload[f.key] = vorschlaege.value[f.key]
    }
    await updateKontakt(props.kontakt.RowKey, payload)
    emit('updated', payload)
    emit('close')
  } catch (e) {
    error.value = e?.response?.data?.error || e.message
  } finally { saving.value = false }
}
</script>
