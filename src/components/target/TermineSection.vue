<template>
  <section class="bg-white rounded-xl border border-gray-100 mb-4">
    <header class="px-5 py-3 border-b border-gray-50 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <CalendarClock class="w-4 h-4 text-[#0088ba]" />
        <h3 class="font-semibold text-gray-800 text-sm">Termine &amp; Erinnerungen</h3>
      </div>
      <button v-if="!readOnly" @click="startNew" class="text-xs text-[#0088ba] hover:underline flex items-center gap-1">
        <Plus class="w-3.5 h-3.5" /> Hinzufügen
      </button>
    </header>

    <div class="p-5">
      <!-- Neuer/Bearbeiten-Eintrag -->
      <div v-if="form" class="bg-blue-50/50 border border-blue-100 rounded-lg p-3 mb-3">
        <div class="grid grid-cols-2 gap-2 mb-2">
          <input v-model="form.datum" type="date" class="px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
          <select v-model="form.typ" class="px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30">
            <option v-for="t in TYPEN" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
        <input v-model="form.titel" placeholder="Titel / Was steht an?"
          class="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
        <textarea v-model="form.notiz" rows="2" placeholder="Notiz (optional)"
          class="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30"></textarea>
        <div class="flex gap-2">
          <button @click="saveForm" :disabled="!form.datum || !form.titel || saving" class="px-3 py-1.5 bg-[#0088ba] text-white rounded-lg text-xs font-medium disabled:opacity-50">
            {{ saving ? 'Speichere…' : 'Speichern' }}
          </button>
          <button @click="form = null" class="px-3 py-1.5 border border-gray-200 rounded-lg text-xs hover:bg-gray-50">Abbrechen</button>
        </div>
      </div>

      <div v-if="!termine.length && !form" class="text-sm text-gray-400 text-center py-4">
        Noch keine Termine erfasst.
      </div>

      <ul class="space-y-1.5">
        <li v-for="t in sortedTermine" :key="t.id"
          :class="['flex items-start gap-3 p-2 rounded-lg border', t.erledigt ? 'bg-gray-50 border-gray-100 opacity-60' : t.tageBisDatum < 0 ? 'bg-red-50 border-red-200' : t.tageBisDatum <= 7 ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-100']">
          <input type="checkbox" :checked="t.erledigt" @change="toggleErledigt(t)" class="mt-1 accent-[#0088ba]" :disabled="readOnly" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-xs font-mono px-1.5 py-0.5 rounded"
                :class="t.erledigt ? 'bg-gray-200 text-gray-500' : t.tageBisDatum < 0 ? 'bg-red-200 text-red-800' : t.tageBisDatum <= 7 ? 'bg-amber-200 text-amber-800' : 'bg-blue-100 text-blue-800'">
                {{ formatDate(t.datum) }}
              </span>
              <span class="text-[10px] uppercase tracking-wide text-gray-400">{{ typLabel(t.typ) }}</span>
              <span v-if="!t.erledigt && t.tageBisDatum < 0" class="text-[10px] text-red-700 font-semibold">überfällig</span>
              <span v-else-if="!t.erledigt && t.tageBisDatum === 0" class="text-[10px] text-amber-700 font-semibold">heute</span>
              <span v-else-if="!t.erledigt && t.tageBisDatum <= 7" class="text-[10px] text-amber-700">in {{ t.tageBisDatum }} T</span>
            </div>
            <div :class="['text-sm font-medium', t.erledigt ? 'line-through text-gray-400' : 'text-gray-800']">{{ t.titel }}</div>
            <div v-if="t.notiz" class="text-xs text-gray-500 mt-0.5">{{ t.notiz }}</div>
          </div>
          <div v-if="!readOnly" class="flex items-center gap-1 flex-shrink-0">
            <button @click="startEdit(t)" class="text-gray-400 hover:text-[#0088ba] p-1" title="Bearbeiten">
              <Pencil class="w-3.5 h-3.5" />
            </button>
            <button @click="deleteTermin(t)" class="text-gray-400 hover:text-red-500 p-1" title="Löschen">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { CalendarClock, Plus, Pencil, Trash2 } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({
  targetId: { type: String, required: true },
  termineJson: { type: String, default: '' },
  readOnly: { type: Boolean, default: false },
})
const emit = defineEmits(['updated'])

const TYPEN = [
  { value: 'notar', label: 'Notartermin' },
  { value: 'dd', label: 'Due Diligence' },
  { value: 'kennenlernen', label: 'Erstkennenlernen' },
  { value: 'wiedervorlage', label: 'Wiedervorlage' },
  { value: 'gespraech', label: 'Gespräch / Call' },
  { value: 'sonstiges', label: 'Sonstiges' },
]

const termine = ref([])
const form = ref(null)
const saving = ref(false)

function loadFromJson() {
  try { termine.value = JSON.parse(props.termineJson || '[]') } catch { termine.value = [] }
}
loadFromJson()
watch(() => props.termineJson, loadFromJson)

const sortedTermine = computed(() => {
  const today = new Date(); today.setHours(0, 0, 0, 0)
  return [...termine.value].map(t => {
    const d = t.datum ? new Date(t.datum) : null
    const tage = d ? Math.round((d - today) / (1000 * 60 * 60 * 24)) : null
    return { ...t, tageBisDatum: tage }
  }).sort((a, b) => {
    if (a.erledigt !== b.erledigt) return a.erledigt ? 1 : -1
    return (a.datum || '').localeCompare(b.datum || '')
  })
})

function formatDate(s) {
  if (!s) return ''
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return s
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

function typLabel(v) {
  return TYPEN.find(t => t.value === v)?.label || 'Sonstiges'
}

function startNew() {
  form.value = { id: '', datum: new Date().toISOString().slice(0, 10), typ: 'wiedervorlage', titel: '', notiz: '' }
}
function startEdit(t) {
  form.value = { ...t }
}

async function saveForm() {
  if (!form.value.datum || !form.value.titel) return
  saving.value = true
  try {
    if (!form.value.id) form.value.id = 'tm' + Date.now()
    const idx = termine.value.findIndex(t => t.id === form.value.id)
    if (idx >= 0) termine.value.splice(idx, 1, { ...form.value })
    else termine.value.push({ ...form.value, erledigt: false })
    await persist()
    form.value = null
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

async function toggleErledigt(t) {
  if (props.readOnly) return
  const idx = termine.value.findIndex(x => x.id === t.id)
  if (idx < 0) return
  termine.value[idx] = { ...termine.value[idx], erledigt: !termine.value[idx].erledigt }
  await persist()
}

async function deleteTermin(t) {
  if (props.readOnly) return
  if (!confirm(`Termin „${t.titel}" wirklich löschen?`)) return
  termine.value = termine.value.filter(x => x.id !== t.id)
  await persist()
}

async function persist() {
  await authFetch('/target-update', {
    method: 'POST',
    data: { id: props.targetId, termineJson: JSON.stringify(termine.value) },
  })
  emit('updated', termine.value)
}
</script>
