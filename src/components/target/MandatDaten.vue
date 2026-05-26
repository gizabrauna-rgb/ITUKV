<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-1">Meine Daten</h2>
    <p class="text-sm text-gray-500 mb-5">Stammdaten zu deinem Mandat – persönliche Kontaktdaten und Vorgangsnummern.</p>

    <!-- Hinweis-Banner: wo finde ich die anderen Sachen -->
    <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-5 text-sm text-blue-900">
      <strong class="block mb-1">📍 Wo finde ich was?</strong>
      <ul class="text-xs space-y-0.5 ml-1">
        <li>· Fragebogen → eigener <strong>Fragebogen</strong>-Tab</li>
        <li>· Unternehmensbewertung → eigener <strong>Bewertung</strong>-Tab</li>
        <li>· Exposé → eigener <strong>Mein Exposé</strong>-Tab</li>
        <li>· NDA &amp; Mandatsvertrag → eigener <strong>Verträge</strong>-Tab (in der Akte)</li>
        <li>· Datenraum &amp; Dokumente → eigener <strong>Dokumente</strong>-Tab</li>
        <li>· Interessenten &amp; Käufer → eigener <strong>Interessenten</strong>-Tab</li>
      </ul>
    </div>

    <!-- Fortschritts-Übersicht -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">Vollständigkeit</span>
        <span class="text-sm font-bold text-[#097e92]">{{ filledCount }} / {{ totalFields }} Felder</span>
      </div>
      <div class="w-full bg-gray-100 rounded-full h-2">
        <div class="bg-[#097e92] h-2 rounded-full transition-all" :style="`width: ${progress}%`"></div>
      </div>
    </div>

    <!-- Persönliche Kontaktdaten -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <User class="w-4 h-4 text-[#097e92]" />
        <h3 class="font-semibold text-gray-800 text-sm">Persönliche Kontaktdaten</h3>
      </header>
      <div class="p-5 grid grid-cols-2 gap-4">
        <Field v-model="data.vorname" label="Vorname" @blur="save" />
        <Field v-model="data.name" label="Name" @blur="save" />
        <Field v-model="data.privatEmail" label="Private E-Mail-Adresse" type="email" @blur="save" />
        <Field v-model="data.privatHandy" label="Private Handy-Nummer" @blur="save" />
      </div>
    </section>

    <!-- Vorgangsnummern (mibeca-intern) -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <Database class="w-4 h-4 text-[#097e92]" />
        <h3 class="font-semibold text-gray-800 text-sm">Vorgangsnummern</h3>
      </header>
      <div class="p-5 grid grid-cols-2 gap-4">
        <Field v-model="data.kundennummer" label="Kundennummer (mibeca)" @blur="save" />
        <Field v-model="data.transaktionsnummer" label="Transaktionsnummer / mb-Nr." @blur="save" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h, defineComponent } from 'vue'
import { User, Database } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String, readOnly: Boolean })

const data = ref({
  vorname: '', name: '',
  privatEmail: '', privatHandy: '',
  kundennummer: '', transaktionsnummer: '',
})

const allFields = ['vorname', 'name', 'privatEmail', 'privatHandy', 'kundennummer', 'transaktionsnummer']
const totalFields = allFields.length
const filledCount = computed(() => allFields.filter(f => (data.value[f] || '').toString().trim()).length)
const progress = computed(() => Math.round((filledCount.value / totalFields) * 100))

onMounted(async () => {
  if (!props.targetId) return
  try {
    const target = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    for (const k of Object.keys(data.value)) {
      if (target[k] !== undefined) data.value[k] = target[k]
    }
  } catch (e) { console.error(e) }
})

let saveTimer = null
async function save() {
  if (props.readOnly || !props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try { await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, ...data.value } }) }
    catch (e) { console.error('save failed', e) }
  }, 500)
}

const Field = defineComponent({
  props: ['modelValue', 'label', 'type'],
  emits: ['update:modelValue', 'blur'],
  setup(props, { emit }) {
    return () => h('div', [
      h('label', { class: 'block text-xs font-medium text-gray-600 mb-1' }, props.label),
      h('input', {
        type: props.type || 'text',
        value: props.modelValue,
        onInput: e => emit('update:modelValue', e.target.value),
        onBlur: () => emit('blur'),
        class: 'w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]'
      })
    ])
  }
})
</script>
