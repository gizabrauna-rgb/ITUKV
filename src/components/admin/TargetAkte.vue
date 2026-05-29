<template>
  <div class="min-h-full bg-gray-50">
    <!-- Header der Akte -->
    <div class="bg-white border-b border-gray-100 sticky top-0 z-20">
      <div class="px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button @click="$emit('close')" class="p-2 hover:bg-gray-100 rounded-lg" title="Zurück zur Übersicht">
            <ArrowLeft class="w-5 h-5 text-gray-500" />
          </button>
          <div>
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs bg-[#0088ba]/10 text-[#0088ba] px-2 py-1 rounded font-semibold">{{ target?.mbNr }}</span>
              <span class="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">{{ target?.projekttyp }}</span>
              <span :class="statusClass(target?.status)" class="text-xs font-medium px-2 py-1 rounded-full">{{ statusLabel(target?.status) }}</span>
            </div>
            <h2 class="text-lg font-bold text-gray-900 mt-1">{{ target?.verkaueferName || '—' }} <span class="text-gray-400 font-normal text-sm">· {{ target?.firma || '' }}</span></h2>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button @click="downloadStatusReport" :disabled="reportLoading"
            class="flex items-center gap-1.5 px-3 py-1.5 border border-[#0088ba]/30 text-[#0088ba] rounded-lg text-xs font-medium hover:bg-[#0088ba]/5 disabled:opacity-50"
            title="Status-Bericht als PDF erzeugen (für den Mandanten)">
            <FileText class="w-3.5 h-3.5" />
            {{ reportLoading ? 'Erzeuge…' : 'Status-Bericht (PDF)' }}
          </button>
          <div class="text-right">
            <div class="text-xs text-gray-500">Aktuelle Phase</div>
            <div class="font-semibold text-[#0088ba]">Phase {{ currentPhase }} / {{ phasen.length || 15 }} · {{ progressPercent }}%</div>
          </div>
        </div>
      </div>

      <!-- Fortschrittsbalken -->
      <div class="px-6 pb-3">
        <div class="w-full bg-gray-100 rounded-full h-1.5">
          <div class="bg-[#0088ba] h-1.5 rounded-full transition-all" :style="`width: ${progressPercent}%`"></div>
        </div>
      </div>

      <!-- Tab-Navigation: Hauptkategorien als Pills -->
      <nav class="flex items-center gap-2 px-4 pt-3 pb-3 border-t border-gray-50 overflow-x-auto">
        <button v-for="g in tabGroups" :key="g.key" @click="selectGroup(g)"
          :class="['flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors',
                  activeGroupKey === g.key
                    ? 'bg-[#0088ba] text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200']">
          <component :is="g.icon" class="w-4 h-4" />
          {{ g.label }}
        </button>
      </nav>

      <!-- Unter-Tabs (zweite Zeile, nur wenn Gruppe > 1 Tab) -->
      <nav v-if="activeGroupTabs.length > 1" class="flex items-center gap-5 px-6 border-t border-gray-100 overflow-x-auto">
        <button v-for="t in activeGroupTabs" :key="t.tab" @click="tab = t.tab"
          :class="['flex items-center gap-1.5 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 -mb-px transition-colors',
                  tab === t.tab
                    ? 'border-[#0088ba] text-[#0088ba]'
                    : 'border-transparent text-gray-500 hover:text-gray-800']">
          <component :is="t.icon" class="w-4 h-4" />
          {{ t.label }}
          <span v-if="t.badge" class="ml-1 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold bg-[#c8b274] text-[#161e2a] rounded-full">{{ t.badge }}</span>
        </button>
      </nav>
    </div>

    <!-- Tab-Inhalte -->
    <div class="p-6">
      <!-- Übersicht -->
      <div v-if="tab === 'uebersicht'">
        <div class="grid grid-cols-3 gap-4 mb-6">
          <InfoCard :icon="MapPin" label="Region" :value="target?.region" />
          <InfoCard :icon="Tag" label="Branche" :value="target?.branche" />
          <InfoCard :icon="Users" label="Mitarbeiter" :value="target?.mitarbeiter" />
          <InfoCard :icon="Euro" label="Umsatz" :value="target?.umsatz" />
          <InfoCard :icon="Hash" label="PLZ" :value="target?.plz" />
          <InfoCard :icon="Mail" label="E-Mail" :value="target?.email" />
        </div>

        <!-- Nächste Schritte -->
        <div class="bg-gradient-to-br from-[#0088ba] to-[#00a0d8] rounded-xl p-5 mb-6 text-white">
          <div class="flex items-center gap-2 mb-2">
            <Sparkles class="w-4 h-4" />
            <span class="text-sm font-semibold uppercase tracking-wide">Was kommt als nächstes</span>
          </div>
          <div class="text-lg font-bold mb-1">Phase {{ currentPhase }}: {{ currentPhaseTitle }}</div>
          <div v-if="nextPendingTasks.length" class="space-y-1.5 mt-3">
            <div v-for="t in nextPendingTasks.slice(0, 3)" :key="t.id" class="flex items-center gap-2 text-sm">
              <Circle class="w-3.5 h-3.5 opacity-70" />
              <span>{{ t.label }}</span>
            </div>
            <button @click="tab = 'prozess'" class="text-xs underline opacity-90 hover:opacity-100 mt-2">Alle Aufgaben anzeigen →</button>
          </div>
          <div v-else class="text-sm opacity-90 mt-2">Phase abgeschlossen — gehe zur nächsten</div>
        </div>

        <!-- Wiedervorlage -->
        <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
          <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
            <CalendarClock class="w-4 h-4 text-[#0088ba]" /> Wiedervorlage
          </h3>
          <div class="flex items-center gap-3">
            <input
              type="date"
              :value="target?.wiedervorlage || ''"
              @change="saveWiedervorlage($event.target.value)"
              :class="['px-3 py-2 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30', wvInputClass]" />
            <button v-if="target?.wiedervorlage" @click="saveWiedervorlage('')" class="text-xs text-gray-400 hover:text-red-500 flex items-center gap-1">
              <X class="w-3.5 h-3.5" /> Entfernen
            </button>
            <span v-if="wvHint" :class="['text-xs', wvHintClass]">{{ wvHint }}</span>
            <span v-if="wvSaving" class="text-xs text-gray-400">Speichern…</span>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <h3 class="font-semibold text-gray-800 text-sm mb-3">Beschreibung</h3>
          <p class="text-sm text-gray-600 leading-relaxed">{{ target?.beschreibung || 'Noch keine Beschreibung hinterlegt.' }}</p>
        </div>
      </div>

      <!-- Master-Prozess -->
      <div v-else-if="tab === 'prozess'">
        <PhasenProzessEingebettet :target-id="targetId" @updated="loadTarget" />
      </div>

      <!-- Mandat-Daten -->
      <div v-else-if="tab === 'mandat'">
        <MandatDaten :target-id="targetId" />
      </div>

      <!-- Ziele & Strategie (Verkäufer: Ziele/Motivation, Käufer: Akquisitionsstrategie) -->
      <div v-else-if="tab === 'ziele'">
        <ZieleStrategieAnzeige :target-id="targetId" />
      </div>

      <!-- Fragebogen (Read-only von Kunde, Jenny sieht alle Antworten) -->
      <div v-else-if="tab === 'fragebogen'">
        <Fragebogen :target-id="targetId" />
      </div>

      <!-- Suchprofil (nur bei Kauf-Mandat) -->
      <div v-else-if="tab === 'suchprofil'">
        <Suchprofil :target-id="targetId" />
      </div>

      <!-- Long-List / Short-List (nur bei Kauf-Mandat) -->
      <div v-else-if="tab === 'longlist'">
        <LongList :target-id="targetId" />
      </div>

      <!-- Erfolgsmeldung / Presse -->
      <div v-else-if="tab === 'erfolg'">
        <Erfolgsmeldung :target-id="targetId" />
      </div>

      <!-- Lessons Learned -->
      <div v-else-if="tab === 'lessons'">
        <LessonsLearned :target-id="targetId" />
      </div>

      <!-- Bewertung (Score-System auf Basis der 33 Fragen) -->
      <div v-else-if="tab === 'bewertung'">
        <Unternehmensbewertung :target-id="targetId" />
      </div>

      <!-- Interessenten -->
      <div v-else-if="tab === 'interessenten'">
        <InteressentenTab :target-id="targetId" />
      </div>

      <!-- Dokumente -->
      <div v-else-if="tab === 'dokumente'">
        <DokumenteAkte :target-id="targetId" :initial-doc="initialDoc" />
      </div>

      <!-- Exposé -->
      <div v-else-if="tab === 'expose'">
        <ExposeGenerator :target-id="targetId" />
      </div>

      <!-- Landing-Page -->
      <div v-else-if="tab === 'landing'">
        <LandingEditor :target-id="targetId" />
      </div>

      <!-- LOI · Finale Verhandlung -->
      <div v-else-if="tab === 'loi'">
        <LoiVerhandlung :target-id="targetId" />
      </div>

      <!-- Verträge (Mandatsvertrag + NDA) -->
      <div v-else-if="tab === 'nda'">
        <!-- Sub-Tabs -->
        <div class="flex gap-1 mb-5 bg-white rounded-xl border border-gray-100 p-1 w-fit">
          <button @click="vertragSubTab = 'mandat'" :class="['px-4 py-2 rounded-lg text-sm font-medium transition-colors', vertragSubTab === 'mandat' ? 'bg-[#0088ba] text-white' : 'text-gray-600 hover:bg-gray-50']">
            Mandatsvertrag
          </button>
          <button @click="vertragSubTab = 'nda'" :class="['px-4 py-2 rounded-lg text-sm font-medium transition-colors', vertragSubTab === 'nda' ? 'bg-[#0088ba] text-white' : 'text-gray-600 hover:bg-gray-50']">
            {{ isKaufMandat ? 'NDA für Käufer' : 'NDA für Investor' }}
          </button>
        </div>
        <VertragEditor v-if="vertragSubTab === 'mandat'" :target-id="targetId" />
        <NdaGenerator v-else :target-id="targetId" />
      </div>

      <!-- Verlauf -->
      <div v-else-if="tab === 'verlauf'">
        <div class="flex justify-end mb-3">
          <button @click="showVerlaufZusammen = true"
            class="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700">
            <Sparkles class="w-3.5 h-3.5" /> Verlauf zusammenfassen
          </button>
        </div>
        <Verlauf :target-id="targetId" />
      </div>

      <!-- Zeiterfassung -->
      <div v-else-if="tab === 'zeit'">
        <Zeiterfassung :target-id="targetId" />
      </div>

      <!-- Zwischenstand -->
      <div v-else-if="tab === 'zwischenstand'">
        <Zwischenstand :target-id="targetId" />
      </div>
    </div>

    <!-- KI-Verlauf-Zusammenfassung -->
    <VerlaufZusammenfassen v-if="showVerlaufZusammen" :target-id="targetId" @close="showVerlaufZusammen = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, defineComponent, h } from 'vue'
import {
  ArrowLeft, MapPin, Tag, Users, Euro, Hash, Mail,
  Sparkles, Circle, Folder, FileText, MessageSquare,
  LayoutDashboard, Workflow, ClipboardList, FileEdit, ShieldCheck, Clock, TrendingUp, Trophy, BookOpen,
  CalendarClock, X, Globe, Handshake, Target
} from '@lucide/vue'
import { authFetch, statusReportPdf } from '../../api.js'
import { toast } from '../../composables/useToast.js'
import PhasenProzessEingebettet from './PhasenProzess.vue'
import MandatDaten from '../target/MandatDaten.vue'
import ZieleStrategieAnzeige from './ZieleStrategieAnzeige.vue'
import VerlaufZusammenfassen from '../VerlaufZusammenfassen.vue'
import Fragebogen from '../target/Fragebogen.vue'
import Unternehmensbewertung from '../target/Unternehmensbewertung.vue'
import Suchprofil from './Suchprofil.vue'
import LongList from './LongList.vue'
import Erfolgsmeldung from './Erfolgsmeldung.vue'
import LessonsLearned from './LessonsLearned.vue'
import DokumenteAkte from './DokumenteAkte.vue'
import VertragEditor from './VertragEditor.vue'
import LandingEditor from './LandingEditor.vue'
import LoiVerhandlung from './LoiVerhandlung.vue'
import InteressentenTab from './InteressentenTab.vue'
import Zwischenstand from './Zwischenstand.vue'
import Verlauf from './Verlauf.vue'
import ExposeGenerator from './ExposeGenerator.vue'
import NdaGenerator from './NdaGenerator.vue'
import Zeiterfassung from './Zeiterfassung.vue'

const props = defineProps({
  targetId: String,
  initialTab: { type: String, default: '' },
  initialDoc: { type: Object, default: null },
})
defineEmits(['close'])

const target = ref(null)
const tab = ref(props.initialTab || 'uebersicht')
const showVerlaufZusammen = ref(false)
const vertragSubTab = ref('mandat')

const isKaufMandat = computed(() => /kauf|investor/i.test(target.value?.projekttyp || ''))

const tabs = computed(() => {
  if (isKaufMandat.value) {
    return [
      { tab: 'uebersicht', label: 'Übersicht', icon: LayoutDashboard },
      { tab: 'prozess', label: 'Master-Prozess', icon: Workflow },
      { tab: 'ziele', label: 'Strategie & Ziele', icon: Target },
      { tab: 'suchprofil', label: 'Suchprofil', icon: FileEdit },
      { tab: 'mandat', label: 'Mandat-Daten', icon: ClipboardList },
      { tab: 'nda', label: 'Verträge', icon: ShieldCheck },
      { tab: 'longlist', label: 'Kandidaten-Match', icon: Users },
      { tab: 'dokumente', label: 'Dokumente', icon: Folder },
      { tab: 'zwischenstand', label: 'Zwischenstand', icon: FileEdit },
      { tab: 'loi', label: 'LOI-Verhandlung', icon: Handshake },
      { tab: 'erfolg', label: 'Erfolgsmeldung', icon: Trophy },
      { tab: 'lessons', label: 'Lessons Learned', icon: BookOpen },
      { tab: 'verlauf', label: 'Verlauf', icon: MessageSquare },
      { tab: 'zeit', label: 'Zeiterfassung', icon: Clock },
    ]
  }
  return [
    { tab: 'uebersicht', label: 'Übersicht', icon: LayoutDashboard },
    { tab: 'prozess', label: 'Master-Prozess', icon: Workflow },
    { tab: 'ziele', label: 'Ziele & Motivation', icon: Target },
    { tab: 'fragebogen', label: 'Fragebogen', icon: FileEdit },
    { tab: 'bewertung', label: 'Bewertung', icon: TrendingUp },
    { tab: 'mandat', label: 'Mandat-Daten', icon: ClipboardList },
    { tab: 'expose', label: 'Exposé', icon: FileText },
    { tab: 'landing', label: 'Landing-Page', icon: Globe },
    { tab: 'nda', label: 'Verträge', icon: ShieldCheck },
    { tab: 'interessenten', label: 'Interessenten', icon: Users },
    { tab: 'dokumente', label: 'Dokumente', icon: Folder },
    { tab: 'zwischenstand', label: 'Zwischenstand', icon: FileEdit },
    { tab: 'loi', label: 'LOI-Verhandlung', icon: Handshake },
    { tab: 'erfolg', label: 'Erfolgsmeldung', icon: Trophy },
    { tab: 'lessons', label: 'Lessons Learned', icon: BookOpen },
    { tab: 'verlauf', label: 'Verlauf', icon: MessageSquare },
    { tab: 'zeit', label: 'Zeiterfassung', icon: Clock },
  ]
})

// Falls initialTab im aktuellen Projekttyp nicht existiert (z.B. "fragebogen" bei
// Kauf-Mandat), fallback auf Übersicht. Watch NACH tabs-Definition platzieren,
// damit kein TDZ-Fehler entsteht.
watch(tabs, (newTabs) => {
  if (Array.isArray(newTabs) && newTabs.length && !newTabs.some(x => x.tab === tab.value)) {
    tab.value = 'uebersicht'
  }
}, { immediate: false })

// Wenn von außen (z.B. Glocke, Übersicht-Klick) ein neuer initialTab kommt,
// schalte aktiv um - sonst bleibt die Akte beim vorherigen Tab haengen.
watch(() => props.initialTab, (v) => {
  if (v && v !== tab.value) tab.value = v
})

// =============== Tab-Gruppen (Haupt-Kategorien + Unter-Tabs) ===============
const TAB_GROUP_DEFS = [
  { key: 'uebersicht', label: 'Übersicht', icon: LayoutDashboard, tabs: ['uebersicht', 'prozess'] },
  { key: 'mandat', label: 'Mandat', icon: ClipboardList, tabs: ['mandat', 'ziele', 'fragebogen', 'bewertung', 'suchprofil'] },
  { key: 'vertraege', label: 'Verträge', icon: ShieldCheck, tabs: ['nda'] },
  { key: 'markt', label: 'Marktansprache', icon: Users, tabs: ['expose', 'landing', 'interessenten', 'longlist'] },
  { key: 'datenraum', label: 'Datenraum', icon: Folder, tabs: ['dokumente'] },
  { key: 'abschluss', label: 'Abschluss', icon: Trophy, tabs: ['zwischenstand', 'loi', 'erfolg', 'lessons'] },
  { key: 'verwaltung', label: 'Verwaltung', icon: Clock, tabs: ['verlauf', 'zeit'] },
]

const tabGroups = computed(() => {
  const availableTabKeys = new Set(tabs.value.map(t => t.tab))
  return TAB_GROUP_DEFS
    .map(g => ({ ...g, tabs: g.tabs.filter(k => availableTabKeys.has(k)) }))
    .filter(g => g.tabs.length > 0)
})

const activeGroupKey = computed(() => {
  for (const g of tabGroups.value) {
    if (g.tabs.includes(tab.value)) return g.key
  }
  return tabGroups.value[0]?.key || 'uebersicht'
})

const activeGroupTabs = computed(() => {
  const group = tabGroups.value.find(g => g.key === activeGroupKey.value)
  if (!group) return []
  return group.tabs.map(k => tabs.value.find(t => t.tab === k)).filter(Boolean)
})

function selectGroup(g) {
  // Beim Klick auf Hauptkategorie: ersten Unter-Tab dieser Gruppe wählen
  if (g.tabs.length > 0 && !g.tabs.includes(tab.value)) {
    tab.value = g.tabs[0]
  }
}

async function loadTarget() {
  if (!props.targetId) return
  try { target.value = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } }) }
  catch (e) { console.error(e) }
}

onMounted(loadTarget)

// Wiedervorlage
const wvSaving = ref(false)
async function saveWiedervorlage(value) {
  if (!target.value) return
  wvSaving.value = true
  try {
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, wiedervorlage: value || '' } })
    target.value.wiedervorlage = value || ''
    toast.success(value ? 'Wiedervorlage gesetzt' : 'Wiedervorlage entfernt')
  } catch (e) {
    toast.error('Speichern fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally { wvSaving.value = false }
}

const reportLoading = ref(false)
async function downloadStatusReport() {
  if (!props.targetId || reportLoading.value) return
  reportLoading.value = true
  try {
    const blob = await statusReportPdf(props.targetId)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const datum = new Date().toISOString().slice(0, 10)
    a.download = `Statusbericht_${target.value?.mbNr || 'mandat'}_${datum}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    toast.success('Status-Bericht erstellt')
  } catch (e) {
    toast.error('PDF konnte nicht erstellt werden: ' + (e?.message || ''))
  } finally {
    reportLoading.value = false
  }
}

function daysUntil(dateStr) {
  if (!dateStr) return null
  const today = new Date(); today.setHours(0,0,0,0)
  const d = new Date(dateStr); d.setHours(0,0,0,0)
  return Math.round((d - today) / 86400000)
}
const wvDays = computed(() => daysUntil(target.value?.wiedervorlage))
const wvHint = computed(() => {
  const d = wvDays.value
  if (d === null) return ''
  if (d < 0) return `Überfällig (vor ${Math.abs(d)} Tagen)`
  if (d === 0) return 'Heute fällig'
  if (d === 1) return 'Morgen fällig'
  return `In ${d} Tagen fällig`
})
const wvHintClass = computed(() => {
  const d = wvDays.value
  if (d === null) return 'text-gray-400'
  if (d < 0) return 'text-red-600 font-medium'
  if (d === 0) return 'text-yellow-600 font-medium'
  if (d <= 7) return 'text-blue-600'
  return 'text-gray-500'
})
const wvInputClass = computed(() => {
  const d = wvDays.value
  if (d === null) return 'border-gray-200'
  if (d < 0) return 'border-red-300 bg-red-50 text-red-700 font-medium'
  if (d === 0) return 'border-yellow-300 bg-yellow-50 text-yellow-700 font-medium'
  if (d <= 7) return 'border-blue-200 bg-blue-50 text-blue-700'
  return 'border-gray-200'
})

const phasen = computed(() => {
  try { return JSON.parse(target.value?.phasenJson || '[]') }
  catch { return [] }
})

const currentPhase = computed(() => {
  for (let i = 0; i < phasen.value.length; i++) {
    const p = phasen.value[i]
    if (!p.aufgaben || !p.aufgaben.every(t => t.done)) return i + 1
  }
  return phasen.value.length || 1
})

const currentPhaseTitle = computed(() => {
  const p = phasen.value[currentPhase.value - 1]
  if (!p) return 'Prozess nicht initialisiert'
  return p.titel.replace(/^\d+\.\s*/, '')
})

const nextPendingTasks = computed(() => {
  const p = phasen.value[currentPhase.value - 1]
  return p?.aufgaben?.filter(t => !t.done) || []
})

const totalTasks = computed(() => phasen.value.reduce((s, p) => s + (p.aufgaben?.length || 0), 0))
const doneTasks = computed(() => phasen.value.reduce((s, p) => s + (p.aufgaben?.filter(t => t.done).length || 0), 0))
const progressPercent = computed(() => totalTasks.value ? Math.round((doneTasks.value / totalTasks.value) * 100) : 0)

function statusClass(s) {
  if (s === 'verfuegbar') return 'bg-green-100 text-green-700'
  if (s === 'in_verhandlung') return 'bg-yellow-100 text-yellow-700'
  if (s === 'pausiert') return 'bg-blue-100 text-blue-700'
  if (s === 'verkaufsstopp') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-500'
}
function statusLabel(s) {
  if (s === 'verfuegbar') return 'Verfügbar'
  if (s === 'in_verhandlung') return 'In Verhandlung'
  if (s === 'pausiert') return 'Pausiert'
  if (s === 'verkaufsstopp') return 'Verkaufsstopp'
  if (s === 'verkauft') return 'Verkauft'
  if (s === 'abgebrochen') return 'Abgebrochen'
  return s || 'Verkauft'
}

// Mini Info-Card
const InfoCard = defineComponent({
  props: ['icon', 'label', 'value'],
  setup(props) {
    return () => h('div', { class: 'bg-white rounded-xl border border-gray-100 p-4' }, [
      h('div', { class: 'flex items-center gap-2 mb-1' }, [
        h(props.icon, { class: 'w-3.5 h-3.5 text-gray-400' }),
        h('span', { class: 'text-xs text-gray-500' }, props.label),
      ]),
      h('div', { class: 'font-medium text-sm text-gray-800' }, props.value || '—'),
    ])
  }
})
</script>
