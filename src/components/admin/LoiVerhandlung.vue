<template>
  <div v-if="!loaded" class="text-center py-12 text-gray-400 text-sm">Lade…</div>

  <div v-else>
    <div class="flex items-start justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">LOI · Finale Verhandlung</h3>
        <p class="text-xs text-gray-500">Punkt-für-Punkt-Tabelle für das Verhandlungs-Gespräch · Verkäufer & Käufer auf einem Bildschirm</p>
      </div>
      <div class="flex gap-2">
        <button @click="zoomMode = !zoomMode" :class="['flex items-center gap-2 px-3 py-2 rounded-xl text-sm', zoomMode ? 'bg-[#0088ba] text-white' : 'border border-gray-200 hover:bg-gray-50']">
          <Maximize2 v-if="!zoomMode" class="w-4 h-4" />
          <Minimize2 v-else class="w-4 h-4" />
          {{ zoomMode ? 'Gesprächs-Modus verlassen' : 'Gesprächs-Modus' }}
        </button>
        <button @click="downloadPdf" :disabled="pdfLoading" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50 disabled:opacity-50">
          <FileText class="w-4 h-4" /> {{ pdfLoading ? 'Lade…' : 'Als PDF speichern' }}
        </button>
      </div>
    </div>

    <!-- Kopfdaten -->
    <div v-if="!zoomMode" class="bg-white rounded-xl border border-gray-100 p-5 mb-3">
      <h4 class="font-semibold text-gray-800 text-sm mb-3">Kopfdaten</h4>
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="lbl">Datum</label>
          <input v-model="loi.datum" @blur="save" type="date" class="input" />
        </div>
        <div>
          <label class="lbl">Käufer</label>
          <input v-model="loi.kaeufer" @blur="save" placeholder="Käufer-Firma + Name" class="input" />
        </div>
        <div>
          <label class="lbl">Verkäufer</label>
          <input v-model="loi.verkaeufer" @blur="save" placeholder="Verkäufer-Firma + Name" class="input" />
        </div>
      </div>
    </div>

    <!-- Gesprächs-Leitfaden (Spickzettel) -->
    <details v-if="!zoomMode" class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-3 text-sm" :open="!loi.einleitungGelesen">
      <summary class="font-semibold text-amber-900 cursor-pointer">Gesprächs-Leitfaden (vor der Verhandlung lesen)</summary>
      <div class="mt-3 space-y-2 text-amber-900 leading-relaxed">
        <p>1. <strong>Einstieg:</strong> „Heute geht es um den Abschluss der LOI-Verhandlungen. Sobald die durch sind, ist der schwierigste Teil geschafft."</p>
        <p>2. <strong>Bestand aufnehmen:</strong> Punkt-für-Punkt durchgehen, alle abhaken die schon einig sind.</p>
        <p>3. <strong>Offene Punkte verhandeln:</strong> Vorstellungen von Käufer und Verkäufer in der Tabelle gegenüberstellen — auf einem Bildschirm sichtbar.</p>
        <p>4. <strong>Tipp 1:</strong> Tauschhandel anbieten (z.B. höherer Preis ↔ GF bleibt einen Monat länger).</p>
        <p>5. <strong>Tipp 2:</strong> WIN-WIN-Ergebnis anstreben — beide Seiten haben in der Übergangsphase noch miteinander zu tun.</p>
        <p class="text-xs italic mt-2">In 9 von 10 Fällen wird eine Einigung erzielt.</p>
        <label class="flex items-center gap-2 mt-3">
          <input type="checkbox" v-model="loi.einleitungGelesen" @change="save" class="rounded" />
          <span class="text-xs">Leitfaden gelesen — diesen Block dauerhaft eingeklappt</span>
        </label>
      </div>
    </details>

    <!-- Tabelle -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden mb-3">
      <table class="w-full" :class="zoomMode ? 'text-base' : 'text-sm'">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-1/5">LOI-Punkt</th>
            <th class="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-1/6">Angebot Verkäufer</th>
            <th class="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-1/6">Angebot Käufer</th>
            <th class="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-1/6 bg-[#0088ba]/5">Einigung</th>
            <th class="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-1/5">Erläuterung</th>
            <th class="text-center px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-20">Final</th>
            <th class="px-2 py-3 w-8"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="(row, idx) in loi.punkte" :key="idx" :class="row.final ? 'bg-green-50/40' : ''">
            <td class="px-3 py-2">
              <input v-model="row.punkt" @blur="save" placeholder="z.B. Kaufpreis Front-Up" class="cell" />
            </td>
            <td class="px-3 py-2">
              <input v-model="row.angebotVerkaeufer" @blur="save" class="cell" />
            </td>
            <td class="px-3 py-2">
              <input v-model="row.angebotKaeufer" @blur="save" class="cell" />
            </td>
            <td class="px-3 py-2 bg-[#0088ba]/5">
              <input v-model="row.einigung" @blur="save" class="cell font-medium" />
            </td>
            <td class="px-3 py-2">
              <input v-model="row.erlaeuterung" @blur="save" class="cell" />
            </td>
            <td class="px-3 py-2 text-center">
              <button @click="row.final = !row.final; save()" :class="['inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-semibold', row.final ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-400 hover:bg-gray-200']" :title="row.final ? 'Final verhandelt' : 'Noch offen'">
                <Check v-if="row.final" class="w-4 h-4" />
                <span v-else>—</span>
              </button>
            </td>
            <td class="px-2 py-2">
              <button @click="removeRow(idx)" class="text-gray-300 hover:text-red-500 p-1" title="Zeile löschen">
                <X class="w-3.5 h-3.5" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <button @click="addRow" class="w-full px-3 py-2.5 text-sm text-[#0088ba] hover:bg-[#0088ba]/5 border-t border-gray-100 flex items-center justify-center gap-1">
        <Plus class="w-4 h-4" /> Zeile hinzufügen
      </button>
    </div>

    <!-- Stand-Stats -->
    <div v-if="!zoomMode" class="grid grid-cols-3 gap-3 mb-3">
      <div class="bg-white rounded-xl border border-gray-100 p-4 text-center">
        <div class="text-2xl font-bold text-gray-800">{{ loi.punkte.length }}</div>
        <div class="text-xs text-gray-500">LOI-Punkte gesamt</div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-4 text-center">
        <div class="text-2xl font-bold text-green-600">{{ finalCount }}</div>
        <div class="text-xs text-gray-500">final verhandelt</div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-4 text-center">
        <div class="text-2xl font-bold text-amber-600">{{ loi.punkte.length - finalCount }}</div>
        <div class="text-xs text-gray-500">noch offen</div>
      </div>
    </div>

    <p v-if="!zoomMode" class="text-xs text-gray-400 text-center">Auto-Speichern beim Verlassen jedes Feldes.</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, X, Check, FileText, Maximize2, Minimize2 } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })
const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

const STANDARD_PUNKTE = [
  'Kaufpreis Front-Up Zahlung',
  'Earn-Out (variable Kaufpreis-Anteile)',
  'Verbleib Geschäftsführer im Unternehmen',
  'Übergangsphase / Beratungszeitraum',
  'Mitarbeiter-Übernahme & Garantien',
  'Wettbewerbsverbot',
  'Garantien & Gewährleistungen (Reps & Warranties)',
  'Stichtag / Closing-Termin',
  'Geschäftsführer-Gehalt während Übergangsphase',
  'Kundenverträge & Lieferanten-Übergang',
  'Vertraulichkeit & Exklusivität',
  'Aufschiebende Bedingungen (Due Diligence)',
]

const loaded = ref(false)
const target = ref(null)
const zoomMode = ref(false)
const pdfLoading = ref(false)
const loi = ref({
  datum: new Date().toISOString().slice(0, 10),
  kaeufer: '',
  verkaeufer: '',
  einleitungGelesen: false,
  punkte: STANDARD_PUNKTE.map(p => ({ punkt: p, angebotVerkaeufer: '', angebotKaeufer: '', einigung: '', erlaeuterung: '', final: false })),
})

const finalCount = computed(() => loi.value.punkte.filter(p => p.final).length)

onMounted(async () => {
  if (!props.targetId) { loaded.value = true; return }
  try {
    target.value = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (target.value?.loiJson) {
      try {
        const parsed = JSON.parse(target.value.loiJson)
        loi.value = { ...loi.value, ...parsed, punkte: Array.isArray(parsed.punkte) && parsed.punkte.length ? parsed.punkte : loi.value.punkte }
      } catch {}
    }
    if (!loi.value.verkaeufer && target.value?.verkaueferName) loi.value.verkaeufer = `${target.value.verkaueferName}${target.value.firma ? ' (' + target.value.firma + ')' : ''}`
  } catch (e) { console.error(e) }
  finally { loaded.value = true }
})

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, loiJson: JSON.stringify(loi.value) } })
    } catch (e) { console.error(e) }
  }, 400)
}

function addRow() {
  loi.value.punkte.push({ punkt: '', angebotVerkaeufer: '', angebotKaeufer: '', einigung: '', erlaeuterung: '', final: false })
  save()
}
function removeRow(idx) {
  if (!confirm('Diese Zeile löschen?')) return
  loi.value.punkte.splice(idx, 1)
  save()
}

async function downloadPdf() {
  pdfLoading.value = true
  try {
    const token = sessionStorage.getItem('customerJwt') || sessionStorage.getItem('msalToken') || ''
    const res = await fetch(`${apiBase}/loi-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      body: JSON.stringify({ targetId: props.targetId, mbNr: target.value?.mbNr, ...loi.value }),
    })
    if (!res.ok) throw new Error('HTTP ' + res.status)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `LOI_${target.value?.mbNr || 'Entwurf'}.pdf`
    a.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (e) {
    toast.error('PDF-Erstellung fehlgeschlagen: ' + e.message)
  } finally { pdfLoading.value = false }
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border-2 border-gray-200 bg-white rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
.lbl { @apply block text-xs font-medium text-gray-600 mb-1; }
.cell { @apply w-full px-2 py-1.5 border border-transparent hover:border-gray-200 focus:border-[#0088ba] rounded-md bg-transparent focus:bg-white focus:outline-none; }
</style>
