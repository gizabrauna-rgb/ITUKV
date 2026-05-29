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

    <!-- KI-Analyse für diese Akte (Compliance / Opt-In) -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <Sparkles class="w-4 h-4 text-purple-600" />
        <h3 class="font-semibold text-gray-800 text-sm">KI-Analyse für diese Akte</h3>
      </header>
      <div class="p-5">
        <div class="flex items-start gap-4">
          <div class="flex-1">
            <p class="text-xs text-gray-600 leading-relaxed">
              Wenn aktiv, darf der Assistent Dokumente in dieser Akte analysieren und Stammdaten anreichern.
              Dokumente werden dafür einmalig an Anthropic (USA, AVV-konform) übertragen, nicht für Training verwendet,
              max 30 Tage gespeichert.
            </p>
            <p v-if="data.kiAnalyseErlaubt" class="text-[11px] text-gray-500 mt-2">
              Freigegeben am {{ formatDate(data.kiAnalyseErlaubtSeit) }}
              <span v-if="data.kiAnalyseErlaubtVon">von {{ data.kiAnalyseErlaubtVon }}</span>
            </p>
          </div>
          <button v-if="!readOnly" @click="toggleKi" type="button"
            :class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0',
                     data.kiAnalyseErlaubt ? 'bg-purple-600' : 'bg-gray-300']"
            :title="data.kiAnalyseErlaubt ? 'Freigegeben – klick zum Sperren' : 'Gesperrt – klick zum Freigeben'">
            <span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                           data.kiAnalyseErlaubt ? 'translate-x-6' : 'translate-x-1']"></span>
          </button>
          <span v-else :class="['text-xs px-2 py-1 rounded-full font-medium',
                                data.kiAnalyseErlaubt ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-500']">
            {{ data.kiAnalyseErlaubt ? 'freigegeben' : 'nicht freigegeben' }}
          </span>
        </div>
      </div>
    </section>

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
import { User, Database, Clock, Building2, Sparkles } from '@lucide/vue'
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
  // KI-Analyse Opt-In
  kiAnalyseErlaubt: false, kiAnalyseErlaubtSeit: '', kiAnalyseErlaubtVon: '',
})

async function toggleKi() {
  if (props.readOnly || !props.targetId) return
  const neu = !data.value.kiAnalyseErlaubt
  data.value.kiAnalyseErlaubt = neu
  if (neu) {
    data.value.kiAnalyseErlaubtSeit = new Date().toISOString()
    data.value.kiAnalyseErlaubtVon = sessionStorage.getItem('userName') || ''
  }
  try {
    await authFetch('/target-update', { method: 'POST', data: {
      id: props.targetId,
      kiAnalyseErlaubt: neu,
      kiAnalyseErlaubtSeit: data.value.kiAnalyseErlaubtSeit,
      kiAnalyseErlaubtVon: data.value.kiAnalyseErlaubtVon,
    }})
  } catch (e) {
    // bei Fehler zurueckdrehen
    data.value.kiAnalyseErlaubt = !neu
  }
}

function formatDate(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleDateString('de-DE') } catch { return '' }
}
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
