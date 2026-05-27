<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Zeiterfassung</h3>
        <p class="text-xs text-gray-500">Beraterstunden für die monatliche Abrechnung dokumentieren</p>
      </div>
      <div class="flex items-center gap-3">
        <select v-model="filterMonat" class="text-sm border border-gray-200 rounded-xl px-3 py-2">
          <option value="">Alle Monate</option>
          <option v-for="m in monate" :key="m" :value="m">{{ formatMonat(m) }}</option>
        </select>
        <button @click="openNew" class="flex items-center gap-2 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8]">
          <Plus class="w-4 h-4" /> Zeit erfassen
        </button>
      </div>
    </div>

    <!-- Summary -->
    <div class="grid grid-cols-3 gap-3 mb-4">
      <div class="bg-white rounded-xl border border-gray-100 p-4">
        <div class="text-xs text-gray-500 mb-1">Stunden gesamt</div>
        <div class="text-2xl font-bold text-gray-900">{{ totalStunden.toFixed(2) }}</div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-4">
        <div class="text-xs text-gray-500 mb-1">Stunden im Filterzeitraum</div>
        <div class="text-2xl font-bold text-[#0088ba]">{{ filterStunden.toFixed(2) }}</div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-4">
        <div class="text-xs text-gray-500 mb-1">Einträge im Zeitraum</div>
        <div class="text-2xl font-bold text-gray-900">{{ filtered.length }}</div>
      </div>
    </div>

    <!-- Tabelle -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div v-if="!filtered.length" class="p-8 text-center text-gray-400 text-sm">
        Noch keine Zeit-Einträge {{ filterMonat ? 'in diesem Monat' : '' }}.
      </div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Datum</th>
            <th class="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase">Zeit</th>
            <th class="text-right px-3 py-3 text-xs font-semibold text-gray-500 uppercase">Std.</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Berater</th>
            <th class="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase">Ort</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Tätigkeit</th>
            <th class="text-right px-3 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="e in filtered" :key="e.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm text-gray-700">{{ formatDate(e.datum) }}</td>
            <td class="px-3 py-3 text-xs text-gray-500 font-mono whitespace-nowrap">
              <span v-if="e.von || e.bis">{{ e.von || '?' }}–{{ e.bis || '?' }}</span>
              <span v-else class="text-gray-300">—</span>
            </td>
            <td class="px-3 py-3 text-sm text-right font-mono font-semibold">{{ Number(e.stunden).toFixed(2) }}</td>
            <td class="px-4 py-3 text-sm text-gray-800 font-medium">{{ e.berater }}</td>
            <td class="px-3 py-3 text-xs">
              <span v-if="e.ort" class="inline-block px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">{{ e.ort }}</span>
              <span v-else class="text-gray-300">—</span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ e.taetigkeit }}</td>
            <td class="px-3 py-3 text-right">
              <button @click="deleteEntry(e)" class="text-gray-300 hover:text-red-500 p-1"><Trash2 class="w-3.5 h-3.5" /></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex gap-2 mt-3">
      <button @click="exportCsv" :disabled="!entries.length" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50 disabled:opacity-50">
        <Download class="w-4 h-4" /> Als CSV exportieren (für Abrechnung)
      </button>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-900">Zeit erfassen</h3>
          <button @click="showModal = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="space-y-3">
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Datum *</label>
            <input v-model="form.datum" type="date" class="input" />
          </div>
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Von</label>
              <input v-model="form.von" type="time" class="input" />
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Bis</label>
              <input v-model="form.bis" type="time" class="input" />
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Stunden *</label>
              <input v-model="form.stunden" type="number" step="0.25" placeholder="auto" class="input" />
            </div>
          </div>
          <p v-if="form.von && form.bis" class="text-xs text-gray-400 -mt-1">
            Aus Zeitraum berechnet: <strong>{{ computedStunden.toFixed(2) }} h</strong> (kann oben überschrieben werden)
          </p>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Berater *</label>
              <input v-model="form.berater" placeholder="z.B. Jenny, Mike, Claudia…" class="input" />
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Ort</label>
              <select v-model="form.ort" class="input">
                <option value="">— wählen —</option>
                <option>Telefon</option>
                <option>Video-Call</option>
                <option>Remote / Büro</option>
                <option>Vor Ort beim Kunden</option>
                <option>Notartermin</option>
                <option>Sonstiges</option>
              </select>
            </div>
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Tätigkeit *</label>
            <textarea v-model="form.taetigkeit" rows="3" placeholder="Was wurde gemacht? z.B. Telefonat mit Käufer-Kandidat, Verhandlung..." class="input resize-none"></textarea>
          </div>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="showModal = false" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
          <button @click="save" :disabled="!canSave" class="flex-1 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium disabled:opacity-50">Speichern</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Plus, X, Trash2, Download } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String })

const target = ref(null)
const entries = ref([])
const showModal = ref(false)
const filterMonat = ref('')

const form = ref({
  datum: new Date().toISOString().slice(0, 10),
  von: '',
  bis: '',
  stunden: '',
  ort: '',
  berater: sessionStorage.getItem('userName') || '',
  taetigkeit: '',
})

// Auto-Stunden aus Von/Bis (Differenz in Stunden, auf 0.25 gerundet)
const computedStunden = computed(() => {
  if (!form.value.von || !form.value.bis) return 0
  const [vh, vm] = form.value.von.split(':').map(Number)
  const [bh, bm] = form.value.bis.split(':').map(Number)
  let mins = (bh * 60 + bm) - (vh * 60 + vm)
  if (mins < 0) mins += 24 * 60   // ueber Mitternacht
  const h = mins / 60
  return Math.round(h * 4) / 4
})

// Wenn von/bis aendert und Stunden noch leer/auto → setze auto-berechneten Wert
watch([() => form.value.von, () => form.value.bis], () => {
  if (form.value.von && form.value.bis) {
    form.value.stunden = computedStunden.value
  }
})

const canSave = computed(() => form.value.datum && form.value.stunden && form.value.berater && form.value.taetigkeit)

const monate = computed(() => {
  const s = new Set(entries.value.map(e => (e.datum || '').slice(0, 7)).filter(Boolean))
  return [...s].sort().reverse()
})

const filtered = computed(() => {
  let r = entries.value
  if (filterMonat.value) r = r.filter(e => (e.datum || '').startsWith(filterMonat.value))
  return [...r].sort((a, b) => (a.datum < b.datum ? 1 : -1))
})

const totalStunden = computed(() => entries.value.reduce((s, e) => s + (Number(e.stunden) || 0), 0))
const filterStunden = computed(() => filtered.value.reduce((s, e) => s + (Number(e.stunden) || 0), 0))

onMounted(async () => {
  if (!props.targetId) return
  try {
    target.value = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (target.value.zeiterfassungJson) {
      try { entries.value = JSON.parse(target.value.zeiterfassungJson) } catch { entries.value = [] }
    }
  } catch (e) { console.error(e) }
})

function openNew() {
  form.value = {
    datum: new Date().toISOString().slice(0, 10),
    von: '',
    bis: '',
    stunden: '',
    ort: '',
    berater: sessionStorage.getItem('userName') || '',
    taetigkeit: '',
  }
  showModal.value = true
}

async function save() {
  entries.value.push({ id: 'z' + Date.now(), ...form.value })
  await persist()
  showModal.value = false
}

async function deleteEntry(e) {
  if (!confirm('Eintrag löschen?')) return
  entries.value = entries.value.filter(x => x.id !== e.id)
  await persist()
}

async function persist() {
  await authFetch('/target-update', { method: 'POST', data: { id: props.targetId,  zeiterfassungJson: JSON.stringify(entries.value)  } })
}

function formatDate(s) {
  return s ? new Date(s).toLocaleDateString('de-DE') : ''
}
function formatMonat(m) {
  const [y, mo] = m.split('-')
  return new Date(+y, +mo - 1, 1).toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })
}

function exportCsv() {
  const fields = ['datum','von','bis','stunden','berater','ort','taetigkeit']
  const header = ['Datum','Von','Bis','Stunden','Berater','Ort','Tätigkeit'].join(';')
  const rows = entries.value.map(e => fields.map(f => `"${(e[f] || '').toString().replaceAll('"', '""')}"`).join(';'))
  const csv = '﻿' + [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url
  a.download = `Zeiterfassung_${target.value?.mbNr || 'mandat'}_${filterMonat.value || 'gesamt'}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
