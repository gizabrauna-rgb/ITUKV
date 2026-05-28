<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-1">Meine Daten</h2>
    <p class="text-sm text-gray-500 mb-5">Stammdaten zu deinem Mandat – persönliche Kontaktdaten und Vorgangsnummern.</p>

    <!-- Fortschritts-Übersicht -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">Vollständigkeit</span>
        <span class="text-sm font-bold text-[#0088ba]">{{ filledCount }} / {{ totalFields }} Felder</span>
      </div>
      <div class="w-full bg-gray-100 rounded-full h-2">
        <div class="bg-[#0088ba] h-2 rounded-full transition-all" :style="`width: ${progress}%`"></div>
      </div>
    </div>

    <!-- Persönliche Kontaktdaten -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <User class="w-4 h-4 text-[#0088ba]" />
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
        <Database class="w-4 h-4 text-[#0088ba]" />
        <h3 class="font-semibold text-gray-800 text-sm">Vorgangsnummern</h3>
      </header>
      <div class="p-5 grid grid-cols-2 gap-4">
        <Field v-model="data.kundennummer" label="Kundennummer (mibeca)" readonly hint="Wird von mibeca vergeben – nicht änderbar." />
        <Field v-model="data.transaktionsnummer" label="Transaktionsnummer / mb-Nr." readonly hint="Wird von mibeca vergeben – nicht änderbar." />
      </div>
    </section>

    <!-- Unternehmens-Stammdaten (von KI-Analyse oder manuell) -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <Building2 class="w-4 h-4 text-[#0088ba]" />
        <h3 class="font-semibold text-gray-800 text-sm">Unternehmens-Stammdaten</h3>
        <span class="ml-auto text-[10px] text-gray-400">manuell oder aus KI-Analyse befüllt</span>
      </header>
      <div class="p-5 grid grid-cols-2 gap-4">
        <Field v-model="data.geschaeftsfuehrer" label="Geschäftsführer" @blur="save" />
        <Field v-model="data.rechtsform" label="Rechtsform (GmbH, AG, …)" @blur="save" />
        <Field v-model="data.gruendungsjahr" label="Gründungsjahr" type="number" @blur="save" />
        <Field v-model="data.branche" label="Branche" @blur="save" />
        <Field v-model="data.mitarbeiter" label="Mitarbeiter (Anzahl)" type="number" @blur="save" />
        <Field v-model="data.umsatz" label="Umsatz (z.B. 2,5 Mio. €)" @blur="save" />
        <Field v-model="data.ebitMarge" label="EBIT-Marge (%)" type="number" @blur="save" />
        <Field v-model="data.recurringPct" label="Wiederkehrende Umsätze (%)" type="number" @blur="save" />
      </div>
    </section>

    <!-- Termine & Erinnerungen -->
    <TermineSection :target-id="targetId" :termine-json="termineJson" :read-only="!!readOnly" @updated="onTermineUpdated" />

    <!-- Mandatslaufzeit -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <Clock class="w-4 h-4 text-[#0088ba]" />
        <h3 class="font-semibold text-gray-800 text-sm">Mandatslaufzeit</h3>
      </header>
      <div class="p-5 grid grid-cols-3 gap-4 items-end">
        <Field v-model="data.mandatStart" label="Mandat-Beginn" type="date" @blur="save" />
        <div>
          <label class="block text-xs font-medium text-gray-600 mb-1">Laufzeit (Monate)</label>
          <input v-model.number="data.mandatLaufzeitMonate" type="number" min="1" max="60" step="1"
            @blur="save"
            class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]" />
          <p class="text-[11px] text-gray-400 mt-1">Empfehlung: 12 Monate</p>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 mb-1">Läuft bis</label>
          <div :class="['px-3 py-2 rounded-xl text-sm border',
              !mandatEnde ? 'bg-gray-50 border-gray-100 text-gray-400'
              : tageBisEnde < 0 ? 'bg-red-50 border-red-200 text-red-700 font-semibold'
              : tageBisEnde <= 60 ? 'bg-amber-50 border-amber-200 text-amber-700 font-semibold'
              : 'bg-green-50 border-green-200 text-green-700']">
            {{ mandatEnde || '—' }}
            <span v-if="mandatEnde" class="block text-[11px] font-normal mt-0.5">
              <template v-if="tageBisEnde < 0">vor {{ -tageBisEnde }} Tagen abgelaufen</template>
              <template v-else-if="tageBisEnde === 0">heute</template>
              <template v-else>in {{ tageBisEnde }} Tagen</template>
            </span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h, defineComponent } from 'vue'
import { User, Database, Clock, Building2 } from '@lucide/vue'
import { authFetch } from '../../api.js'
import TermineSection from './TermineSection.vue'

const props = defineProps({ targetId: String, readOnly: Boolean })

const data = ref({
  vorname: '', name: '',
  privatEmail: '', privatHandy: '',
  kundennummer: '', transaktionsnummer: '',
  mandatStart: '', mandatLaufzeitMonate: 12,
  // Unternehmens-Stammdaten
  geschaeftsfuehrer: '', rechtsform: '', gruendungsjahr: '',
  branche: '', mitarbeiter: '', umsatz: '',
  ebitMarge: '', recurringPct: '',
})
const termineJson = ref('')

function onTermineUpdated(arr) {
  termineJson.value = JSON.stringify(arr || [])
}

const mandatEnde = computed(() => {
  if (!data.value.mandatStart || !data.value.mandatLaufzeitMonate) return ''
  const start = new Date(data.value.mandatStart)
  if (Number.isNaN(start.getTime())) return ''
  const end = new Date(start)
  end.setMonth(end.getMonth() + Number(data.value.mandatLaufzeitMonate))
  return end.toISOString().slice(0, 10)
})

const tageBisEnde = computed(() => {
  if (!mandatEnde.value) return null
  const end = new Date(mandatEnde.value)
  const today = new Date(); today.setHours(0, 0, 0, 0)
  return Math.round((end - today) / (1000 * 60 * 60 * 24))
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
    termineJson.value = target.termineJson || ''
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
  props: ['modelValue', 'label', 'type', 'readonly', 'hint'],
  emits: ['update:modelValue', 'blur'],
  setup(props, { emit }) {
    return () => h('div', [
      h('label', { class: 'block text-xs font-medium text-gray-600 mb-1' }, props.label),
      h('input', {
        type: props.type || 'text',
        value: props.modelValue,
        readonly: props.readonly || undefined,
        onInput: e => !props.readonly && emit('update:modelValue', e.target.value),
        onBlur: () => !props.readonly && emit('blur'),
        class: 'w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba] '
          + (props.readonly ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : '')
      }),
      props.hint ? h('p', { class: 'text-[10px] text-gray-400 mt-1' }, props.hint) : null,
    ])
  }
})
</script>
