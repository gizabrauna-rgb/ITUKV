<template>
  <div>
    <div v-if="!embedded" class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Master-Prozess</h2>
      <select v-model="selectedTargetId" @change="loadTarget" class="text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30">
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
          <span class="text-sm font-bold text-[#0088ba]">Phase {{ activePhaseNumber }} / {{ phasen.length }} · {{ doneTasksTotal }} / {{ totalTasksTotal }} Aufgaben</span>
        </div>
        <div class="w-full bg-gray-100 rounded-full h-2">
          <div class="bg-[#0088ba] h-2 rounded-full transition-all" :style="`width: ${progressPercent}%`"></div>
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
              phaseStatus(phase) === 'active' ? 'bg-[#0088ba] text-white' :
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
                :class="['w-5 h-5 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors mt-0.5', task.done ? 'bg-[#0088ba] border-[#0088ba]' : 'border-gray-300 hover:border-[#0088ba]']"
              >
                <Check v-if="task.done" class="w-3 h-3 text-white" />
              </button>
              <div class="flex-1 min-w-0">
                <div :class="['text-sm', task.done ? 'line-through text-gray-400' : 'text-gray-800']">{{ task.label }}</div>
                <div class="grid grid-cols-3 gap-2 mt-2">
                  <input v-model="task.verantwortlich" @blur="save" placeholder="Verantwortlich" class="text-xs px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-[#0088ba]/30" />
                  <input v-model="task.datum" type="date" @blur="save" class="text-xs px-2 py-1 border border-gray-200 rounded focus:outline-none" />
                  <input v-model="task.notiz" @blur="save" placeholder="Notiz" class="text-xs px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-[#0088ba]/30" />
                </div>
              </div>
              <button @click="removeTask(phase, ti)" class="text-gray-300 hover:text-red-500" title="Aufgabe entfernen">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>

            <button @click="addTask(phase)" class="w-full px-3 py-2 border border-dashed border-gray-300 rounded-lg text-xs text-gray-500 hover:text-[#0088ba] hover:border-[#0088ba] transition-colors flex items-center justify-center gap-1.5">
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
                class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#0088ba]/30 resize-none bg-white"
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
  { id: 1, titel: '1. UVE Start — Vorbereitungs-Checkliste', notiz: '', aufgaben: [
    { id: 'uve1', label: 'MB050: Videolektionen ansehen ("Wie läuft Verkauf von A bis Z ab?")', done: false, verantwortlich: 'Kunde', datum: '', notiz: '' },
    { id: 'uve2', label: 'MB050: Fragebogen Unternehmensbewertung ausfüllen', done: false, verantwortlich: 'Kunde', datum: '', notiz: '' },
    { id: 'uve3', label: 'MB050: Due-Diligence-Datenraum nach Muster anlegen', done: false, verantwortlich: 'Kunde', datum: '', notiz: '' },
    { id: 'uve4', label: 'MB041: Verkaufsstory entwickeln (Ziele, Wunsch-Exit, W-Fragen, Deal-Struktur)', done: false, verantwortlich: 'Kunde', datum: '', notiz: '' },
    { id: 'uve5', label: 'Eigenes Unternehmensexposé erstellen (Vorlage aus Unterlagenpaket)', done: false, verantwortlich: 'Kunde', datum: '', notiz: '' },
    { id: 'uve6', label: 'Verkaufsmandat erteilen → Marktansprache durch mibeca', done: false, verantwortlich: 'Kunde', datum: '', notiz: '' },
    { id: 'uve7', label: 'Kosten-Tabelle ansehen ("Welche Kosten kommen auf Dich zu")', done: false, verantwortlich: 'Kunde', datum: '', notiz: '' },
    { id: 't1', label: 'Zahlen, Daten, Fakten zusammentragen', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Unternehmensbewertung erstellen', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Exposé-Entwurf erstellen', done: false, verantwortlich: '', datum: '', notiz: '' },
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
    { id: 'ddprep', label: 'Datenraum vollständig befüllt', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 'dda', label: 'A. Allgemeines: Ansprechpartner geklärt (Veräußerer + Erwerber)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 'ddb', label: 'B. Rechtliche DD: Gesellschaftsunterlagen, Verträge, Arbeitsrecht (~58 Items)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
    { id: 'ddc', label: 'C. Steuerliche DD: Veranlagung, Betriebsprüfungen, Verlustvorträge (~35 Items)', done: false, verantwortlich: 'Steuerberater', datum: '', notiz: '' },
    { id: 'ddd', label: 'D. Financial DD: Jahresabschlüsse, BWAs, Budgets (~95 Items)', done: false, verantwortlich: 'Steuerberater', datum: '', notiz: '' },
    { id: 'dde', label: 'E. Business DD: Markt, Wettbewerber, Vertrieb, Personal (~14 Items)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 'ddf', label: 'F. Technologische DD: IT-Architektur, Security, F&E (~16 Items)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 'ddend', label: 'DD-Bericht / Fragen-Antworten dokumentiert', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 12, titel: '12. Vertragsgestaltung', notiz: '', aufgaben: [
    { id: 't1', label: 'Deal-Struktur entscheiden: Share Deal (SPA) vs. Asset Deal', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Kaufvertrag Entwurf (Vorlage: SPA-Master oder Asset-Deal-Vertrag)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
    { id: 't3', label: 'GF-Anstellungsvertrag (falls GF im Unternehmen verbleibt)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
    { id: 't4', label: 'Gesellschaftsvertrag anpassen (falls neue Gesellschafter)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
    { id: 't5', label: 'Vertragsverhandlungen — Garantien, Earn-Out, Klauseln', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't6', label: 'Finale Version abgestimmt zwischen Käufer und Verkäufer', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 13, titel: '13. Notartermin & Closing', notiz: '', aufgaben: [
    { id: 't1', label: 'Notartermin koordiniert', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't2', label: 'Unterzeichnung beim Notar', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't3', label: 'Kaufpreis überwiesen', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 't4', label: 'Anteilsübertragung vollzogen', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
  { id: 14, titel: '14. Post-Closing — Übergabe & Kommunikation', notiz: '', aufgaben: [
    { id: 'pc1', label: 'Übergabe-Plan erstellt (Begleitung 3-12 Monate)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 'pc2', label: 'Mitarbeiter informiert', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 'pc3', label: 'Kunden-Information: "Unternehmen wurde verkauft" (Vorlage nutzen)', done: false, verantwortlich: 'Verkäufer', datum: '', notiz: '' },
    { id: 'pc4', label: 'Vertragsübergabe-Information an Kunden (Vorlage nutzen)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 'pc5', label: 'Earn-Out-Phase tracken (falls vereinbart)', done: false, verantwortlich: '', datum: '', notiz: '' },
    { id: 'pc6', label: 'Aufhebungsvertrag GF (falls GF ausscheidet)', done: false, verantwortlich: 'Anwalt', datum: '', notiz: '' },
  ]},
  { id: 15, titel: '15. Erfolgsmeldung & Abrechnung', notiz: '', aufgaben: [
    { id: 'pr1', label: 'Pressemitteilung erstellt (Vorlage: DATAreform x Knoblauch)', done: false, verantwortlich: 'Marketing', datum: '', notiz: '' },
    { id: 'pr2', label: 'Erfolgsmeldung an Branche/Newsletter', done: false, verantwortlich: 'Marketing', datum: '', notiz: '' },
    { id: 'pr3', label: 'LinkedIn-Post (anonymisiert oder mit Zustimmung)', done: false, verantwortlich: 'Marketing', datum: '', notiz: '' },
    { id: 'pr4', label: 'Erfolgshonorar berechnet & in Rechnung gestellt', done: false, verantwortlich: 'Claudia', datum: '', notiz: '' },
    { id: 'pr5', label: 'Zeiterfassung final abgerechnet', done: false, verantwortlich: 'Claudia', datum: '', notiz: '' },
    { id: 'pr6', label: 'Mandat in Ordnerstruktur archiviert', done: false, verantwortlich: '', datum: '', notiz: '' },
  ]},
])

const props = defineProps({ targetId: { type: String, default: '' } })
const embedded = computed(() => !!props.targetId)
const targets = ref([])
const selectedTargetId = ref(props.targetId || '')
const phasen = ref(PHASEN_VORLAGE())
const expanded = ref({})
const currentTarget = ref(null)

onMounted(async () => {
  if (!embedded.value) {
    try {
      const all = await getTargets()
      targets.value = [...all].sort((a, b) => {
        const na = parseInt((a.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
        const nb = parseInt((b.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
        return na - nb
      })
    } catch (e) { console.error(e) }
  }
  if (selectedTargetId.value) {
    await loadTarget()
  }
})

async function loadTarget() {
  if (!selectedTargetId.value) return
  try {
    const target = await authFetch('/target-get', { method: 'POST', data: { id: selectedTargetId.value } })
    currentTarget.value = target
    if (target.phasenJson) {
      try { phasen.value = JSON.parse(target.phasenJson) }
      catch { phasen.value = PHASEN_VORLAGE() }
    } else {
      // Erstmaliges Oeffnen: Standard-Phasen anlegen + sofort speichern,
      // damit die Uebersicht/Target-Dashboard die Phasen kennen
      phasen.value = PHASEN_VORLAGE()
      try {
        await authFetch('/target-update', { method: 'POST', data: { id: selectedTargetId.value, phasenJson: JSON.stringify(phasen.value) } })
      } catch (e) { console.error('Auto-init Phasen fehlgeschlagen', e) }
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
      await authFetch('/target-update', { method: 'POST', data: { id: selectedTargetId.value,  phasenJson: JSON.stringify(phasen.value)  } })
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
  if (s === 'active') return 'bg-[#0088ba]/10 text-[#0088ba]'
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
  return phasen.value.length
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
