<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4 py-8 overflow-y-auto">
    <div class="bg-white rounded-2xl p-6 w-full max-w-4xl my-auto">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-xl font-bold text-gray-900">Welche Kosten kommen auf Dich zu?</h3>
          <p class="text-sm text-gray-500 mt-1">Betragsbeispiel im Verkaufsprozess</p>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <X class="w-5 h-5" />
        </button>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm border-collapse">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-200">
              <th class="text-left p-3 font-semibold text-gray-700">Investitionen</th>
              <th colspan="3" class="text-center p-3 font-semibold text-gray-700 border-l border-gray-200">
                Beispiel A – Verkaufserlös 500.000 €
              </th>
              <th colspan="3" class="text-center p-3 font-semibold text-gray-700 border-l border-gray-200">
                Beispiel B – Verkaufserlös 1.500.000 €
              </th>
            </tr>
            <tr class="bg-gray-50 border-b border-gray-200 text-xs text-gray-500">
              <th></th>
              <th class="p-2 border-l border-gray-200">fest</th>
              <th class="p-2">minimal</th>
              <th class="p-2">maximal</th>
              <th class="p-2 border-l border-gray-200">fest</th>
              <th class="p-2">minimal</th>
              <th class="p-2">maximal</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="row in zeilen" :key="row.label" :class="row.highlight ? 'bg-blue-50 font-semibold' : ''">
              <td class="p-3 text-gray-800">{{ row.label }}</td>
              <td class="p-3 text-right border-l border-gray-100">{{ format(row.a_fest) }}</td>
              <td class="p-3 text-right">{{ format(row.a_min) }}</td>
              <td class="p-3 text-right">{{ format(row.a_max) }}</td>
              <td class="p-3 text-right border-l border-gray-100">{{ format(row.b_fest) }}</td>
              <td class="p-3 text-right">{{ format(row.b_min) }}</td>
              <td class="p-3 text-right">{{ format(row.b_max) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3">
        <div class="bg-green-50 border border-green-200 rounded-xl p-4">
          <div class="text-xs text-green-700 font-semibold uppercase">Einzelunternehmen / GmbH & Co. KG</div>
          <div class="text-[11px] text-green-600 mb-2">Steuersatz ca. 42,5%</div>
          <div class="text-sm text-gray-700">Beispiel A: <strong>248k – 262k €</strong></div>
          <div class="text-sm text-gray-700">Beispiel B: <strong>773k – 794k €</strong></div>
        </div>
        <div class="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div class="text-xs text-blue-700 font-semibold uppercase">GmbH</div>
          <div class="text-[11px] text-blue-600 mb-2">Steuersatz ca. 30%</div>
          <div class="text-sm text-gray-700">Beispiel A: <strong>302k – 319k €</strong></div>
          <div class="text-sm text-gray-700">Beispiel B: <strong>967k – 984k €</strong></div>
        </div>
        <div class="bg-purple-50 border border-purple-200 rounded-xl p-4">
          <div class="text-xs text-purple-700 font-semibold uppercase">Holding-Struktur</div>
          <div class="text-[11px] text-purple-600 mb-2">Steuersatz ca. 1,5%</div>
          <div class="text-sm text-gray-700">Beispiel A: <strong>425k – 449k €</strong></div>
          <div class="text-sm text-gray-700">Beispiel B: <strong>1,36 Mio – 1,39 Mio €</strong></div>
        </div>
      </div>

      <p class="text-xs text-gray-500 mt-4 leading-relaxed">
        Hinweis: Die Beträge sind Beispielwerte und können je nach Komplexität deines Verkaufs abweichen.
        Frag Jenny bei konkreten Fragen zu deinem individuellen Fall.
      </p>

      <div class="flex gap-3 mt-6">
        <button v-if="bestaetigtAm" class="flex-1 bg-green-50 border border-green-200 text-green-800 rounded-xl py-3 text-sm font-medium flex items-center justify-center gap-2">
          <Check class="w-4 h-4" /> Bereits zur Kenntnis genommen am {{ formatDate(bestaetigtAm) }}
        </button>
        <button v-else @click="bestaetigen" :disabled="saving" class="flex-1 bg-[#0088ba] hover:bg-[#00a0d8] text-white rounded-xl py-3 text-sm font-medium disabled:opacity-50">
          {{ saving ? 'Speichere…' : 'Verstanden – Kosten zur Kenntnis genommen' }}
        </button>
        <button @click="$emit('close')" class="px-6 py-3 border border-gray-200 rounded-xl text-sm">Schließen</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { X, Check } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({
  targetId: String,
  bestaetigtAm: String,
})
const emit = defineEmits(['close', 'confirmed'])

const saving = ref(false)

async function bestaetigen() {
  saving.value = true
  try {
    const ts = new Date().toISOString()
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, kostenInfoBestaetigtAm: ts } })
    emit('confirmed', ts)
  } catch (e) {
    alert('Fehler beim Speichern: ' + (e.response?.data?.error || e.message))
  } finally { saving.value = false }
}

function format(v) {
  if (v === null || v === undefined || v === '') return '–'
  return Number(v).toLocaleString('de-DE') + ' €'
}
function formatDate(iso) {
  return iso ? new Date(iso).toLocaleDateString('de-DE') : ''
}

// Tabellenzeilen (aus der Excel-Vorlage von Jenny)
const zeilen = [
  { label: 'UVE-Coaching / MC-Coaching + Interessenten-Flatrate', a_fest: 10000, a_min: '', a_max: '', b_fest: 10000, b_min: '', b_max: '' },
  { label: 'Erfolgsvergütung mibeca 5% vom Verkaufserlös', a_fest: 25000, a_min: '', a_max: '', b_fest: 75000, b_min: '', b_max: '' },
  { label: 'Beratungsvergütung mibeca (Stundenbasis)', a_fest: '', a_min: 3000, a_max: 6000, b_fest: '', b_min: 3000, b_max: 6000 },
  { label: 'Anwaltskanzlei (Vertragserstellung + Verhandlung)', a_fest: '', a_min: 6000, a_max: 25000, b_fest: '', b_min: 6000, b_max: 25000 },
  { label: 'Notarkosten', a_fest: '', a_min: 0, a_max: 3000, b_fest: '', b_min: 0, b_max: 3000 },
  { label: 'Investition gesamt', a_fest: '', a_min: 44000, a_max: 69000, b_fest: '', b_min: 94000, b_max: 119000, highlight: true },
  { label: 'Verkaufserlös vor Steuern', a_fest: '', a_min: 431000, a_max: 456000, b_fest: '', b_min: 1381000, b_max: 1406000, highlight: true },
]
</script>
