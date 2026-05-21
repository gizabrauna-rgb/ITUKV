<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Master-Prozess</h2>
      <select v-model="selectedTargetId" @change="loadTarget" class="text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#097e92]/30">
        <option value="">— Target auswählen —</option>
        <option v-for="t in targets" :key="t.RowKey" :value="t.RowKey">{{ t.mbNr }} · {{ t.verkaueferName }}</option>
      </select>
    </div>

    <div v-if="!selectedTargetId" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">
      <Workflow class="w-10 h-10 mx-auto mb-3 text-gray-200" />
      Bitte oben ein Target auswählen, um den Prozess-Verlauf anzuzeigen.
    </div>

    <div v-else>
      <!-- Fortschrittsbalken gesamt -->
      <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-gray-700">Gesamtfortschritt M&A-Prozess</span>
          <span class="text-sm font-bold text-[#097e92]">Phase {{ activePhaseNumber }} / 13 · {{ doneTasksTotal }} / {{ totalTasksTotal }} Aufgaben</span>
        </div>
        <div class="w-full bg-gray-100 rounded-full h-2">
          <div class="bg-[#097e92] h-2 rounded-full transition-all" :style="`width: ${progressPercent}%`"></div>
        </div>
        <div class="text-xs text-gray-400 mt-1">{{ progressPercent }}% komplett</div>
      </div>

      <!-- Phasen-Sektionen -->
      <div class="space-y-2">
        <section v-for="(phase, idx) in phasen" :key="phase.id" class="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <button
            @click="expanded[phase.id] = !expanded[phase.id]"
            class="w-full px-5 py-3 flex items-center gap-3 hover:bg-gray-50 transition-colors text-left"
          >
            <!-- Status-Indikator -->
            <div :class="[
              'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0',
              phaseStatus(phase) === 'done' ? 'bg-green-500 text-white' :
              phaseStatus(phase) === 'active' ? 'bg-[#097e92] text-white' :
              'bg-gray-100 text-gray-400'
            ]">
              <Check v-if="phaseStatus(phase) === 'done'" class="w-3.5 h-3.5" />
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="font-semibold text-sm text-gray-900">{{ phase.titel }}</div>
              <div class="text-xs text-gray-500 mt-0.5">{{ countDoneInPhase(phase) }} / {{ phase.aufgaben.length }} Aufgaben erledigt</div>
            </div>
            <div class="flex items-center gap-2">
              <span :class="phaseBadgeClass(phase)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ phaseBadgeLabel(phase) }}</span>
              <ChevronDown :class="['w-4 h-4 text-gray-400 transition-transform', expanded[phase.id] && 'rotate-180']" />
            </div>
          </button>

          <!-- Aufgaben -->
          <div v-if="expanded[phase.id]" class="border-t border-gray-50 px-5 py-3 bg-gray-50">
            <div v-for="(task, ti) in phase.aufgaben" :key="task.id" class="bg-white rounded-lg p-3 mb-2 last:mb-0 flex items-start gap-3">
              <button
                @click="toggleTask(phase, task)"
                :class="['w-5 h-5 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors mt-0.5', task.done ? 'bg-[#097e92] border-[#097e92]' : 'border-gray-300 hover:border-[#097e92]']"
              >
                <Check v-if="task.done" class="w-3 h-3 text-white" />
              </button>
              <div class="flex-1 min-w-0">
                <div :class="['text-sm', task.done ? 'line-through text-gray-400' : 'text-gray-800']">{{ task.label }}</div>
                <div class="grid grid-cols-3 gap-2 mt-2">
                  <input v-model="task.verantwortlich" @blur="save" placeholder="Verantwortlich" class="text-xs px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-[#097e92]/30" />
                  <input v-model="task.datum" type="date" @blur="save" class="text-xs px-2 py-1 border border-gray-200 rounded focus:outline-none" />
                  <input v-model="task.notiz" @blur="save" placeholder="Notiz" class="text-xs px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-[#097e92]/30" />
                </div>
              </div>
              <button @click="removeTask(phase, ti)" class="text-gray-300 hover:text-red-500" title="Aufgabe entfernen">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>

            <button @click="addTask(phase)" class="w-full px-3 py-2 border border-dashed border-gray-300 rounded-lg text-xs text-gray-500 hover:text-[#097e92] hover:border-[#097e92] transition-colors flex items-center justify-center gap-1.5">
              <Plus class="w-3.5 h-3.5" /> Aufgabe hinzufügen
            </button>

            <!-- Phasen-Notizen -->
            <div class="mt-3">
              <label class="text-xs font-medium text-gray-500 mb-1 block">Phasen-Notizen</label>
              <textarea
                v-model="phase.notiz"
                @blur="save"
                rows="2"
                placeholder="Notizen zur gesamten Phase…"
                class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#097e92]/30 resize-none bg-white"
              ></textarea>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Check, ChevronDown, Plus, Trash2, Workflow } from '@lucide/vue'
import { getTargets, authFetch } from '../../api.js'

// Master-Prozess Vorlage (13 Phasen aus Jennys Doku)
const PHASEN_VORLAGE = () => ([
  { id: 1, titel: '1. UVE Start — Unterlagen erstellen', notiz: '', aufgaben: [
    { id: 't1', label: 'Zahlen, Daten, Fakten sammeln', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Unternehmensbewertung erstellen', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Checkliste Unternehmensbewertung', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't4', label: 'Exposé-Entwurf erstellen', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 2, titel: '2. UVE Abschluss — Verkaufsmandat-Eröffnung', notiz: '', aufgaben: [
    { id: 't1', label: 'Verkaufsmandat unterzeichnet (12 Monate)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Standard-Ordner anlegen: ITUKV/UVE/mb-XX', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Onboarding durch Jenny (+ Content)', done: false, verantwortlich: 'Jenny', datum: '', notiz: '' },
    { id: 't4', label: 'Kundenakte angelegt', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 3, titel: '3. Marktansprache — Interessenten anschreiben', notiz: '', aufgaben: [
    { id: 't1', label: 'Landing-Page online (it-unternehmen-kaufen-verkaufen.de/mb-XX)', done: false, verantwortlich: 'Marketing', datum: '', notiz: '' },
    { id: 't2', label: 'Erstinteressenten aus Kundenstamm filtern (PLZ-Radius)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Anschreiben über zahlreiche Kanäle (Mail/Brief/Telefon)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't4', label: 'KEINE Exklusivität zugesagt!', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 4, titel: '4. NDA von Interessenten abholen', notiz: '', aufgaben: [
    { id: 't1', label: 'NDA-Anfragen prüfen & freigeben', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'VETO-Check mit Verkäufer', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Signierte NDAs in Akte ablegen', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 5, titel: '5. Erstes Kennenlernen — Interessent ↔ Verkäufer', notiz: '', aufgaben: [
    { id: 't1', label: 'Termin koordinieren (3er-Gespräch)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Gespräch durchgeführt + Notizen', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Eindruck dokumentieren', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 6, titel: '6. Datenraum / Kommunikationsraum in Element', notiz: '', aufgaben: [
    { id: 't1', label: 'Element-Raum eröffnet', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Beteiligte eingeladen', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Zugang verifiziert', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 7, titel: '7. Austausch von Unterlagen', notiz: '', aufgaben: [
    { id: 't1', label: 'Erweiterte Unterlagen freigegeben', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Rückfragen beantwortet', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 8, titel: '8. Indikatives Angebot', notiz: '', aufgaben: [
    { id: 't1', label: 'Erstes Gebot eingegangen', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Bewertung des Angebots mit Verkäufer', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Rückmeldung an Käufer', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 9, titel: '9. Verhandlungen', notiz: '', aufgaben: [
    { id: 't1', label: 'Preis verhandelt', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Struktur (Share Deal / Asset Deal) festgelegt', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Bedingungen (Earn-Out, GF-Verbleib) geklärt', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 10, titel: '10. Letter of Intent (LOI)', notiz: '', aufgaben: [
    { id: 't1', label: 'LOI erstellt', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'LOI unterzeichnet', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 11, titel: '11. Due Diligence', notiz: '', aufgaben: [
    { id: 't1', label: 'Datenraum vollständig befüllt', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'DD-Anforderungsliste abgearbeitet', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Rechtliche Prüfung (Anwalt)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't4', label: 'Steuerliche Prüfung (Steuerberater)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't5', label: 'Finanzielle Prüfung', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 12, titel: '12. Vertragsgestaltung (SPA)', notiz: '', aufgaben: [
    { id: 't1', label: 'SPA-Entwurf vom Anwalt', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Vertragsverhandlungen Klauseln', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Finale Version abgestimmt', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 13, titel: '13. Notartermin & Closing', notiz: '', aufgaben: [
    { id: 't1', label: 'Notartermin koordiniert', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Unterzeichnung beim Notar', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Kaufpreis überwiesen', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't4', label: 'Anteilsübertragung vollzogen', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't5', label: 'Erfolgshonorar berechnet & gestellt', done: false, verantwortlich: 'Claudia', datum: '', notiz: '' },
  ]},
])

const targets = ref([])
const selectedTargetId = ref('')
const phasen = ref(PHASEN_VORLAGE())
const expanded = ref({})
const currentTarget = ref(null)

onMounted(async () => {
  try {
    const all = await getTargets()
    targets.value = [...all].sort((a, b) => {
      const na = parseInt((a.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
      const nb = parseInt((b.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
      return na - nb
    })
  } catch (e) { console.error(e) }
})

async function loadTarget() {
  if (!selectedTargetId.value) return
  try {
    const target = await authFetch(`/targets/${selectedTargetId.value}`)
    currentTarget.value = target
    if (target.phasenJson) {
      try { phasen.value = JSON.parse(target.phasenJson) }
      catch { phasen.value = PHASEN_VORLAGE() }
    } else {
      phasen.value = PHASEN_VORLAGE()
    }
    expanded.value = {}
    // aktive Phase aufklappen
    const active = phasen.value.find(p => !phaseAllDone(p))
    if (active) expanded.value[active.id] = true
  } catch (e) { console.error(e) }
}

let saveTimer = null
async function save() {
  if (!selectedTargetId.value) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch(`/targets/${selectedTargetId.value}`, {
        method: 'PATCH',
        data: { phasenJson: JSON.stringify(phasen.value) }
      })
    } catch (e) { console.error('save phasen', e) }
  }, 500)
}

function phaseAllDone(p) {
  return p.aufgaben.length > 0 && p.aufgaben.every(t => t.done)
}
function phaseSomeDone(p) {
  return p.aufgaben.some(t => t.done)
}
function phaseStatus(p) {
  if (phaseAllDone(p)) return 'done'
  if (phaseSomeDone(p)) return 'active'
  return 'pending'
}
function phaseBadgeClass(p) {
  const s = phaseStatus(p)
  if (s === 'done') return 'bg-green-100 text-green-700'
  if (s === 'active') return 'bg-[#097e92]/10 text-[#097e92]'
  return 'bg-gray-100 text-gray-500'
}
function phaseBadgeLabel(p) {
  const s = phaseStatus(p)
  if (s === 'done') return 'abgeschlossen'
  if (s === 'active') return 'in Arbeit'
  return 'offen'
}
function countDoneInPhase(p) {
  return p.aufgaben.filter(t => t.done).length
}

const activePhaseNumber = computed(() => {
  for (const p of phasen.value) {
    if (!phaseAllDone(p)) return p.id
  }
  return 13
})
const totalTasksTotal = computed(() => phasen.value.reduce((s, p) => s + p.aufgaben.length, 0))
const doneTasksTotal = computed(() => phasen.value.reduce((s, p) => s + p.aufgaben.filter(t => t.done).length, 0))
const progressPercent = computed(() => totalTasksTotal.value ? Math.round((doneTasksTotal.value / totalTasksTotal.value) * 100) : 0)

function toggleTask(phase, task) {
  task.done = !task.done
  save()
}

function addTask(phase) {
  const newId = 't' + Date.now()
  phase.aufgaben.push({ id: newId, label: 'Neue Aufgabe', done: false, verantwortlich: '', datum: '', notiz: '' })
  save()
}

function removeTask(phase, idx) {
  if (!confirm('Aufgabe wirklich entfernen?')) return
  phase.aufgaben.splice(idx, 1)
  save()
}
</script>
