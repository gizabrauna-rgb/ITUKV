<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Zwischenstandsgespräch</h3>
        <p class="text-xs text-gray-500">UVE · Strukturiertes Beratungsgespräch · {{ filledCount }} / {{ totalFields }} Felder ausgefüllt</p>
      </div>
      <button @click="exportPdf" class="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 rounded-lg text-xs hover:bg-gray-50">
        <Download class="w-3.5 h-3.5" /> Drucken
      </button>
    </div>

    <!-- Fortschritt -->
    <div class="bg-white rounded-xl border border-gray-100 p-4 mb-4">
      <div class="w-full bg-gray-100 rounded-full h-1.5">
        <div class="bg-[#0088ba] h-1.5 rounded-full transition-all" :style="`width: ${progress}%`"></div>
      </div>
    </div>

    <!-- Kopfdaten -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4 grid grid-cols-3 gap-4">
      <div>
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1 block">Datum</label>
        <input v-model="data.datum" type="date" @blur="save" class="input" />
      </div>
      <div>
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1 block">Name (Berater)</label>
        <input v-model="data.beraterName" @blur="save" class="input" />
      </div>
      <div>
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1 block">UVE seit</label>
        <input v-model="data.uveSeit" type="month" @blur="save" class="input" />
      </div>
    </div>

    <!-- Kategorien -->
    <div v-for="(cat, ci) in categories" :key="ci" class="bg-white rounded-xl border border-gray-100 mb-4 overflow-hidden">
      <header class="px-5 py-3 border-b border-gray-50 bg-gray-50">
        <h4 class="font-semibold text-sm text-[#0088ba]">{{ cat.roman }}. {{ cat.titel }}</h4>
      </header>
      <div class="divide-y divide-gray-50">
        <div v-for="(f, fi) in cat.fragen" :key="fi" class="px-5 py-4 grid grid-cols-2 gap-4">
          <div class="text-sm text-gray-700 leading-snug">{{ f }}</div>
          <textarea
            v-model="data.antworten[fieldId(ci, fi)]"
            @blur="save"
            rows="2"
            placeholder="Antwort eintragen…"
            class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba] resize-none"
          ></textarea>
        </div>
      </div>
    </div>

    <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm text-blue-900">
      <Info class="w-4 h-4 inline mr-1" />
      Antworten werden automatisch gespeichert.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Download, Info } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String })

const categories = [
  { roman: 'I', titel: 'Ausgangslage', fragen: [
    'Kurze Zusammenfassung der bisherigen Schritte im UVE-Prozess',
    'Erwartungen des Verkäufers zu Beginn vs. aktueller Stand',
    'Investition: 10.000 € für Coaching – was wurde bisher erreicht?',
  ]},
  { roman: 'II', titel: 'Verkaufsfähigkeit bewerten', fragen: [
    'Ist das Unternehmen aktuell verkaufsfähig? Warum (nicht)?',
    'Welche Faktoren beeinflussen die Verkaufsfähigkeit?',
    'Gibt es strukturelle, finanzielle oder marktspezifische Hindernisse?',
  ]},
  { roman: 'III', titel: 'Unternehmensbewertung', fragen: [
    'Was ist das Unternehmen Stand heute wert?',
    'Welche Bewertungsmethoden wurden angewendet?',
    'Gibt es Optimierungspotenziale für eine höhere Bewertung?',
  ]},
  { roman: 'IV', titel: 'Marktresonanz & Interessenten', fragen: [
    'Gibt es potenzielle Käufer? Falls ja, wer?',
    'Welche Angebote oder Interessenbekundungen liegen vor?',
    'Welche Preisvorstellungen haben potenzielle Käufer?',
    'Falls keine Interessenten: Woran liegt es?',
  ]},
  { roman: 'V', titel: 'Preisfindung & Verkaufsstrategie', fragen: [
    'Zu welchem Preis würde der Verkäufer die Firma verkaufen?',
    'Deckt sich dieser Preis mit den Marktrückmeldungen?',
    'Falls nicht: Gibt es Spielraum zur Anpassung?',
  ]},
  { roman: 'VI', titel: 'Handlungsempfehlungen zur Steigerung des Unternehmenswerts', fragen: [
    'Welche konkreten Maßnahmen sind notwendig, um das Unternehmen attraktiver für Käufer zu machen?',
    'Optimierungspotenziale in den Bereichen: Finanzen/Jahresabschlüsse, Prozesse im UN, Kundenstruktur/Klumpenrisiko, Abhängigkeiten im Unternehmen vom Unternehmer',
    'Zeitrahmen für die Umsetzung der Maßnahmen',
  ]},
  { roman: 'VII', titel: 'Nächste Schritte & Unterstützung durch uns', fragen: [
    'Welche Unterstützung bieten wir weiterhin an?',
    'Welche weiteren Coaching- oder Beratungsleistungen sind sinnvoll?',
    'Klärung der Option: Weiterarbeit an der Verkaufsfähigkeit und Rückweg ins Coaching (UC)',
  ]},
]

const data = ref({
  datum: '',
  beraterName: '',
  uveSeit: '',
  antworten: {},
})

const totalFields = computed(() =>
  categories.reduce((sum, c) => sum + c.fragen.length, 0)
)
const filledCount = computed(() =>
  Object.values(data.value.antworten).filter(v => (v || '').trim()).length
)
const progress = computed(() => Math.round((filledCount.value / totalFields.value) * 100))

function fieldId(catIdx, fragenIdx) {
  return `${categories[catIdx].roman}_${fragenIdx}`
}

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch('/target-update', { method: 'POST', data: { id: props.targetId,  zwischenstandJson: JSON.stringify(data.value)  } })
    } catch (e) { console.error('save zwischenstand', e) }
  }, 600)
}

onMounted(async () => {
  if (!props.targetId) return
  try {
    const target = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (target.zwischenstandJson) {
      const parsed = JSON.parse(target.zwischenstandJson)
      data.value = { datum: parsed.datum || '', beraterName: parsed.beraterName || '',
                     uveSeit: parsed.uveSeit || '', antworten: parsed.antworten || {} }
    }
  } catch (e) { console.error(e) }
})

function exportPdf() {
  window.print()
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
