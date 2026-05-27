<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Topbar -->
    <header class="bg-[#161e2a] text-white px-6 py-3 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-3">
        <img src="/Logo_mibeca_Start.png" alt="mibeca" class="h-10 w-auto" />
        <div>
          <span class="font-bold text-sm">ITUKV Dashboard</span>
          <span class="text-gray-400 text-xs ml-2">M&A · mibeca intern</span>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <!-- Ansicht-Switcher -->
        <div class="relative">
          <button @click="showSwitcher = !showSwitcher"
            class="flex items-center gap-2 px-3 py-1.5 bg-[#0088ba]/20 hover:bg-[#0088ba]/30 rounded-lg text-xs font-medium text-white transition-colors">
            <Eye class="w-3.5 h-3.5" />
            Ansicht testen
            <ChevronDown class="w-3.5 h-3.5" />
          </button>
          <div v-if="showSwitcher" class="absolute right-0 top-full mt-1 bg-white text-gray-800 rounded-xl shadow-xl border border-gray-100 w-72 z-50 overflow-hidden">
            <div class="p-3 border-b border-gray-100">
              <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Wechsle die Sicht</div>
            </div>
            <div class="px-3 pt-2 pb-1 text-xs font-semibold text-gray-400 uppercase">Verkäufer-Ansichten</div>
            <button v-for="t in targetTypes" :key="t" @click="switchTo(t)"
              class="w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center gap-3">
              <Briefcase class="w-4 h-4 text-[#0088ba]" />
              <span class="text-sm">{{ t }}</span>
            </button>
            <div class="px-3 pt-2 pb-1 text-xs font-semibold text-gray-400 uppercase border-t border-gray-50 mt-1">Käufer-Ansichten</div>
            <button v-for="t in investorTypes" :key="t" @click="switchTo(t)"
              class="w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center gap-3">
              <Users class="w-4 h-4 text-[#3498db]" />
              <span class="text-sm">{{ t }}</span>
            </button>
          </div>
        </div>

        <!-- Posteingang / Ungelesen-Badge mit Dropdown -->
        <div class="relative">
          <button @click="showBell = !showBell" class="relative flex items-center gap-1.5 text-xs text-gray-300 hover:text-white">
            <Bell class="w-4 h-4" />
            <span v-if="unreadTotal > 0" class="absolute -top-1 -right-2 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[16px] h-4 px-1 flex items-center justify-center">
              {{ unreadTotal > 99 ? '99+' : unreadTotal }}
            </span>
          </button>
          <div v-if="showBell" class="absolute right-0 top-full mt-2 bg-white text-gray-800 rounded-xl shadow-2xl border border-gray-100 w-96 z-50 overflow-hidden">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <div class="font-semibold text-sm">Ungelesene Nachrichten</div>
              <button v-if="unreadItems.length" @click="markAllRead" class="text-xs text-gray-500 hover:text-[#0088ba]">Alle als gelesen markieren</button>
            </div>
            <div class="max-h-96 overflow-y-auto">
              <div v-if="!unreadItems.length" class="p-6 text-center text-sm text-gray-400">
                Keine ungelesenen Nachrichten ✓
              </div>
              <button v-for="i in unreadItems" :key="i.targetId" @click="openTarget(i)"
                class="w-full px-4 py-3 hover:bg-gray-50 text-left border-b border-gray-50 last:border-0 flex items-start gap-2">
                <span :class="['w-2 h-2 rounded-full mt-1.5 flex-shrink-0', typColor(i.lastTyp)]"></span>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="font-mono text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">{{ i.mbNr }}</span>
                    <span class="font-medium text-sm truncate">{{ i.firma }}</span>
                    <span class="text-[10px] bg-red-500 text-white rounded-full px-1.5 py-0.5 font-bold ml-auto">{{ i.unreadCount }}</span>
                  </div>
                  <div class="text-xs text-gray-700 mt-0.5 truncate">{{ i.lastBetreff }}</div>
                  <div class="text-[11px] text-gray-400 mt-0.5">{{ formatRelative(i.lastDatum) }}</div>
                </div>
              </button>
            </div>
          </div>
        </div>
        <span class="text-sm text-gray-300">{{ userName }}</span>
        <button @click="$emit('logout')" class="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors">
          <LogOut class="w-4 h-4" /> Abmelden
        </button>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <nav class="w-52 bg-white border-r border-gray-100 flex-shrink-0 py-4">
        <ul class="space-y-0.5 px-2">
          <li v-for="item in navItems" :key="item.tab">
            <button
              @click="tab = item.tab"
              :class="[
                'w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm transition-colors text-left',
                tab === item.tab
                  ? 'bg-[#0088ba]/10 text-[#0088ba] font-semibold'
                  : 'text-gray-600 hover:bg-gray-50'
              ]"
            >
              <component :is="item.icon" class="w-4 h-4 flex-shrink-0" />
              <span class="leading-tight">{{ item.label }}</span>
            </button>
          </li>
        </ul>
      </nav>

      <!-- Content -->
      <main class="flex-1 overflow-y-auto p-6">

        <!-- Übersicht -->
        <div v-if="tab === 'uebersicht'">
          <h2 class="text-xl font-bold text-gray-900 mb-6">Übersicht</h2>
          <div class="grid grid-cols-4 gap-4 mb-6">
            <div v-for="s in statsData" :key="s.label" class="bg-white rounded-xl border border-gray-100 p-5">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs text-gray-400 font-medium">{{ s.label }}</span>
                <div class="w-8 h-8 rounded-lg flex items-center justify-center" :style="`background: ${s.color}18`">
                  <component :is="s.icon" class="w-4 h-4" :style="`color: ${s.color}`" />
                </div>
              </div>
              <div class="text-2xl font-bold text-gray-900">{{ statsLoading ? '…' : s.value }}</div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4 mb-6">
            <!-- Wartet auf mich -->
            <div class="bg-white rounded-xl border border-gray-100 p-5">
              <div class="flex items-center justify-between mb-3">
                <h3 class="font-semibold text-gray-800 text-sm flex items-center gap-2">
                  <AlertCircle class="w-4 h-4 text-amber-500" /> Wartet auf mich
                </h3>
                <span v-if="ueberblick.totalWartet" class="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-semibold">{{ ueberblick.totalWartet }}</span>
              </div>
              <div v-if="!ueberblick.totalWartet" class="text-sm text-gray-400 py-3 text-center">Nichts dringend ✓</div>
              <div v-else class="space-y-2">
                <button v-for="v in ueberblick.wartet.vertragsGegenzeichnung || []" :key="'sig'+v.targetId" @click="openAkteWithTab(v.targetId, 'nda')"
                  class="w-full text-left flex items-center gap-2 p-2 hover:bg-amber-50 rounded-lg text-xs">
                  <span class="w-1.5 h-1.5 rounded-full bg-yellow-500 flex-shrink-0"></span>
                  <span class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ v.mbNr }}</span>
                  <span class="font-medium truncate flex-1">{{ v.firma }}</span>
                  <span class="text-gray-500">Vertrag gegenzeichnen</span>
                </button>
                <button v-for="v in ueberblick.wartet.ndaReview || []" :key="'nda'+v.interessentId"
                  @click="openNdaInAkte(v)"
                  class="w-full text-left flex items-center gap-2 p-2 hover:bg-amber-50 rounded-lg text-xs">
                  <span class="w-1.5 h-1.5 rounded-full bg-[#FF6F00] flex-shrink-0"></span>
                  <span v-if="v.mbNr" class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ v.mbNr }}</span>
                  <span class="font-medium truncate flex-1">NDA von {{ v.firma }}</span>
                  <span class="text-[#FF6F00]">prüfen</span>
                </button>
                <button v-for="v in ueberblick.wartet.wiedervorlage || []" :key="'wv'+v.targetId" @click="openAkte({ RowKey: v.targetId })"
                  class="w-full text-left flex items-center gap-2 p-2 hover:bg-amber-50 rounded-lg text-xs">
                  <span class="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0"></span>
                  <span class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ v.mbNr }}</span>
                  <span class="font-medium truncate flex-1">{{ v.firma }}</span>
                  <span class="text-red-600">Wiedervorlage</span>
                </button>
                <button v-for="v in ueberblick.wartet.mandateLaufenAus || []" :key="'ml'+v.targetId" @click="openAkteWithTab(v.targetId, 'mandat')"
                  class="w-full text-left flex items-center gap-2 p-2 hover:bg-amber-50 rounded-lg text-xs">
                  <span :class="['w-1.5 h-1.5 rounded-full flex-shrink-0', v.abgelaufen ? 'bg-red-600' : 'bg-amber-500']"></span>
                  <span class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ v.mbNr }}</span>
                  <span class="font-medium truncate flex-1">{{ v.firma }}</span>
                  <span :class="v.abgelaufen ? 'text-red-700 font-semibold' : 'text-amber-700'">
                    <template v-if="v.abgelaufen">Mandat abgelaufen ({{ -v.tageBisEnde }} T)</template>
                    <template v-else>Mandat läuft in {{ v.tageBisEnde }} T aus</template>
                  </span>
                </button>
                <button v-for="v in ueberblick.wartet.pressefreigabe || []" :key="'pr'+v.targetId" @click="openAkteWithTab(v.targetId, 'erfolg')"
                  class="w-full text-left flex items-center gap-2 p-2 hover:bg-amber-50 rounded-lg text-xs">
                  <span class="w-1.5 h-1.5 rounded-full bg-orange-500 flex-shrink-0"></span>
                  <span class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ v.mbNr }}</span>
                  <span class="font-medium truncate flex-1">Pressetext: Änderungswunsch</span>
                </button>
                <button v-for="v in ueberblick.wartet.ungelesen || []" :key="'unr'+v.targetId" @click="openAkteWithTab(v.targetId, 'verlauf')"
                  class="w-full text-left flex items-center gap-2 p-2 hover:bg-amber-50 rounded-lg text-xs">
                  <span class="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0"></span>
                  <span class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ v.mbNr }}</span>
                  <span class="font-medium truncate flex-1">{{ v.firma }}</span>
                  <span class="text-red-600">{{ v.anzahl }} ungelesen</span>
                </button>
                <button v-for="v in ueberblick.wartet.fragebogenZuPruefen || []" :key="'fb'+v.targetId" @click="openAkteWithTab(v.targetId, 'fragebogen')"
                  class="w-full text-left flex items-center gap-2 p-2 hover:bg-amber-50 rounded-lg text-xs">
                  <span class="w-1.5 h-1.5 rounded-full bg-purple-500 flex-shrink-0"></span>
                  <span class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ v.mbNr }}</span>
                  <span class="font-medium truncate flex-1">{{ v.firma }}</span>
                  <span class="text-purple-700">Fragebogen abgegeben — auswerten</span>
                </button>
                <button v-for="v in ueberblick.wartet.exposeKorrekturwunsch || []" :key="'ek'+v.targetId" @click="openAkteWithTab(v.targetId, 'expose')"
                  class="w-full text-left flex items-center gap-2 p-2 hover:bg-amber-50 rounded-lg text-xs">
                  <span class="w-1.5 h-1.5 rounded-full bg-orange-500 flex-shrink-0"></span>
                  <span class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ v.mbNr }}</span>
                  <span class="font-medium truncate flex-1">{{ v.firma }}</span>
                  <span class="text-orange-700">Exposé-Korrekturwunsch</span>
                </button>
                <button v-for="v in ueberblick.wartet.exposeFreigabeAusstehend || []" :key="'ef'+v.targetId" @click="openAkteWithTab(v.targetId, 'expose')"
                  class="w-full text-left flex items-center gap-2 p-2 hover:bg-amber-50 rounded-lg text-xs">
                  <span class="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0"></span>
                  <span class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ v.mbNr }}</span>
                  <span class="font-medium truncate flex-1">{{ v.firma }}</span>
                  <span class="text-gray-500">wartet auf Exposé-Freigabe</span>
                </button>
              </div>
            </div>

            <!-- Aktivitäts-Feed -->
            <div class="bg-white rounded-xl border border-gray-100 p-5">
              <h3 class="font-semibold text-gray-800 text-sm flex items-center gap-2 mb-3">
                <Activity class="w-4 h-4 text-[#0088ba]" /> Letzte Aktivitäten
              </h3>
              <div v-if="!ueberblick.feed?.length" class="text-sm text-gray-400 py-3 text-center">Noch keine Aktivitäten</div>
              <div v-else class="space-y-2 max-h-80 overflow-y-auto">
                <button v-for="e in ueberblick.feed" :key="e.id" @click="openAkteWithTab(e.targetId, 'verlauf')"
                  class="w-full text-left p-2 hover:bg-gray-50 rounded-lg">
                  <div class="flex items-center gap-2 text-xs mb-0.5">
                    <span class="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ e.mbNr }}</span>
                    <span class="text-gray-500 truncate flex-1">{{ e.firma }}</span>
                    <span class="text-gray-400 text-[10px]">{{ formatRel(e.datum) }}</span>
                  </div>
                  <div class="text-sm text-gray-800 truncate">{{ e.betreff }}</div>
                </button>
              </div>
            </div>
          </div>

          <!-- Anstehende Termine -->
          <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-gray-800 text-sm flex items-center gap-2">
                <CalendarClock class="w-4 h-4 text-[#0088ba]" /> Anstehende Termine (14 Tage)
              </h3>
              <span v-if="ueberblick.termineAnstehend?.length" class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-semibold">
                {{ ueberblick.termineAnstehend.length }}
              </span>
            </div>
            <div v-if="!ueberblick.termineAnstehend?.length" class="text-sm text-gray-400 py-3 text-center">Keine anstehenden Termine ✓</div>
            <div v-else class="grid grid-cols-2 gap-2">
              <button v-for="tm in ueberblick.termineAnstehend" :key="tm.id+tm.targetId" @click="openAkteWithTab(tm.targetId, 'mandat')"
                :class="['text-left flex items-start gap-2 p-2.5 rounded-lg border hover:shadow-sm transition-all',
                  tm.ueberfaellig ? 'bg-red-50 border-red-200' : tm.tageBisDatum <= 3 ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-100 hover:border-[#0088ba]/30']">
                <div :class="['text-[11px] font-mono px-1.5 py-0.5 rounded flex-shrink-0',
                  tm.ueberfaellig ? 'bg-red-200 text-red-800' : tm.tageBisDatum <= 3 ? 'bg-amber-200 text-amber-800' : 'bg-blue-100 text-blue-800']">
                  {{ formatDateShort(tm.datum) }}
                </div>
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-1 text-[11px] mb-0.5">
                    <span class="font-mono bg-gray-100 px-1 rounded">{{ tm.mbNr }}</span>
                    <span class="text-gray-500 truncate">{{ tm.firma }}</span>
                  </div>
                  <div class="text-xs font-medium text-gray-800 truncate">{{ tm.titel }}</div>
                  <div v-if="tm.ueberfaellig" class="text-[10px] text-red-700 font-semibold">überfällig ({{ -tm.tageBisDatum }} T)</div>
                </div>
              </button>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-gray-100 p-6">
            <h3 class="font-semibold text-gray-800 mb-4 text-sm">Schnellzugriff</h3>
            <div class="grid grid-cols-3 gap-3">
              <button v-for="q in quickAccess" :key="q.tab" @click="tab = q.tab"
                class="flex items-center gap-3 p-4 rounded-xl border border-gray-100 hover:border-[#0088ba]/30 hover:bg-[#0088ba]/5 transition-all text-left">
                <component :is="q.icon" class="w-5 h-5 text-[#0088ba]" />
                <div>
                  <div class="text-sm font-medium text-gray-800">{{ q.label }}</div>
                  <div class="text-xs text-gray-400">{{ q.desc }}</div>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- Targets -->
        <div v-else-if="tab === 'targets'">
          <TargetAkte v-if="akteTargetId" :target-id="akteTargetId" :initial-tab="akteInitialTab" :initial-doc="akteInitialDoc" @close="akteTargetId = null" />
          <TargetsTab v-else @open-detail="openAkte" />
        </div>

        <!-- CRM -->
        <div v-else-if="tab === 'crm'">
          <CrmTab />
        </div>

        <!-- Veröffentlichte Mandate (Landing-Pages) -->
        <div v-else-if="tab === 'ausschreibungen'">
          <AusschreibungenTab @open-akte="e => openAkteWithTab(e.targetId, e.tab || 'landing')" />
        </div>

        <!-- Dokumente -->
        <div v-else-if="tab === 'dokumente'">
          <DokumenteTab />
        </div>

        <!-- Benutzer -->
        <!-- Controlling -->
        <div v-else-if="tab === 'mailvorlagen'">
          <MailvorlagenTab />
        </div>

        <div v-else-if="tab === 'controlling'">
          <Controlling />
        </div>

        <div v-else-if="tab === 'benutzer'">
          <BenutzerTab />
        </div>

        <!-- Einstellungen -->
        <div v-else-if="tab === 'einstellungen'">
          <EinstellungenTab />
        </div>

      </main>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Building2, LogOut, LayoutDashboard, Briefcase, GitBranch,
  Users, Megaphone, FolderOpen, X, Check, Eye, ChevronDown, Settings, UserCog, Workflow, Bell, BarChart3, AlertCircle, Activity, Mail, CalendarClock,
} from '@lucide/vue'
import { authFetch, verlaufUnreadCount, verlaufMarkRead } from '../api.js'
import TargetsTab from '../components/admin/TargetsTab.vue'
import CrmTab from '../components/admin/CrmTab.vue'
import AusschreibungenTab from '../components/admin/AusschreibungenTab.vue'
import DokumenteTab from '../components/admin/DokumenteTab.vue'
import BenutzerTab from '../components/admin/BenutzerTab.vue'
import EinstellungenTab from '../components/admin/EinstellungenTab.vue'
import Controlling from '../components/admin/Controlling.vue'
import TargetAkte from '../components/admin/TargetAkte.vue'
import MailvorlagenTab from '../components/admin/MailvorlagenTab.vue'

const props = defineProps({ userName: String })
const emit = defineEmits(['logout', 'switch-view'])

const tab = ref('uebersicht')
const showSwitcher = ref(false)

const targetTypes = ['UVE Target', 'Projekt Target', 'MC Target']
const investorTypes = ['Kauf-Mandat', 'Projekt Investoren', 'MC Investoren']

function switchTo(view) {
  showSwitcher.value = false
  emit('switch-view', view)
}
const statsLoading = ref(true)
const statsRaw = ref({ aktiveTargets: 0, offeneNdas: 0, investorenGesamt: 0, dealsAbgeschlossen: 0 })
const akteTargetId = ref(null)
const akteInitialTab = ref('')
const akteInitialDoc = ref(null)

function openAkte(target) {
  akteTargetId.value = target.RowKey
  akteInitialTab.value = ''
  akteInitialDoc.value = null
  tab.value = 'targets'
}

function openAkteWithTab(targetId, initialTab) {
  akteTargetId.value = targetId
  akteInitialTab.value = initialTab
  akteInitialDoc.value = null
  tab.value = 'targets'
}

function openNdaInAkte(v) {
  akteTargetId.value = v.targetId
  akteInitialTab.value = 'dokumente'
  akteInitialDoc.value = { ordner: 'NDA', docId: v.ndaDocId }
  tab.value = 'targets'
  // NDA als geprüft markieren — Eintrag sofort aus UI entfernen + Backend nachziehen
  if (v.interessentId && ueberblick.value.wartet?.ndaReview) {
    ueberblick.value.wartet.ndaReview = ueberblick.value.wartet.ndaReview.filter(x => x.interessentId !== v.interessentId)
    ueberblick.value.totalWartet = Math.max(0, (ueberblick.value.totalWartet || 1) - 1)
    authFetch('/interessent-update', { method: 'POST', data: { id: v.interessentId, ndaReviewed: true } }).catch(() => {})
  }
}

const navItems = [
  { tab: 'uebersicht', label: 'Übersicht', icon: LayoutDashboard },
  { tab: 'targets', label: 'Projekte', icon: Briefcase },
  { tab: 'crm', label: 'Kontakte', icon: Users },
  { tab: 'ausschreibungen', label: 'Veröffentlichte Mandate', icon: Megaphone },
  { tab: 'dokumente', label: 'Dokumente', icon: FolderOpen },
  { tab: 'mailvorlagen', label: 'E-Mail-Vorlagen', icon: Mail },
  { tab: 'controlling', label: 'Controlling', icon: BarChart3 },
  { tab: 'benutzer', label: 'Benutzer', icon: UserCog },
  { tab: 'einstellungen', label: 'Einstellungen', icon: Settings },
]

const quickAccess = [
  { tab: 'targets', label: 'Targets', desc: 'Mandate verwalten', icon: Briefcase },
  { tab: 'crm', label: 'Investoren', desc: 'CRM & Karte', icon: Users },
]

const statsData = computed(() => [
  { label: 'Aktive Targets', value: statsRaw.value.aktiveTargets, icon: Briefcase, color: '#0088ba' },
  { label: 'Offene NDAs', value: statsRaw.value.offeneNdas, icon: GitBranch, color: '#c8b274' },
  { label: 'Investoren gesamt', value: statsRaw.value.investorenGesamt, icon: Users, color: '#3498db' },
  { label: 'Deals abgeschlossen', value: statsRaw.value.dealsAbgeschlossen, icon: Megaphone, color: '#22c55e' },
])


const unreadTotal = ref(0)
const unreadItems = ref([])
const showBell = ref(false)
async function pollUnread() {
  try {
    const r = await verlaufUnreadCount()
    unreadTotal.value = r?.total || 0
    unreadItems.value = r?.items || []
  } catch {}
}
function typColor(t) {
  const m = { mail_in: 'bg-blue-500', mail_out: 'bg-[#0088ba]', telefon: 'bg-purple-500', termin: 'bg-amber-500', wichtig: 'bg-red-500', notiz: 'bg-gray-400' }
  return m[t] || 'bg-gray-400'
}
function formatRelative(iso) {
  if (!iso) return ''
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return 'gerade eben'
  if (diff < 3600) return `vor ${Math.floor(diff / 60)} Min`
  if (diff < 86400) return `vor ${Math.floor(diff / 3600)} Std`
  if (diff < 7 * 86400) return `vor ${Math.floor(diff / 86400)} Tagen`
  return new Date(iso).toLocaleDateString('de-DE')
}
async function openTarget(item) {
  showBell.value = false
  akteInitialTab.value = 'verlauf'  // direkt in den Verlauf der Akte springen
  akteInitialDoc.value = null
  akteTargetId.value = item.targetId
  tab.value = 'targets'
  try {
    await verlaufMarkRead(item.targetId)
    await pollUnread()
  } catch {}
}
async function markAllRead() {
  try {
    await verlaufMarkRead('')
    await pollUnread()
    showBell.value = false
  } catch {}
}
let unreadTimer = null

const ueberblick = ref({ feed: [], wartet: {}, totalWartet: 0 })
async function loadUeberblick() {
  try { ueberblick.value = await authFetch('/dashboard-uebersicht') } catch {}
}
function formatRel(iso) {
  if (!iso) return ''
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (d < 60) return 'gerade'
  if (d < 3600) return `${Math.floor(d/60)} Min`
  if (d < 86400) return `${Math.floor(d/3600)} Std`
  if (d < 7*86400) return `${Math.floor(d/86400)} Tg`
  return new Date(iso).toLocaleDateString('de-DE')
}

function formatDateShort(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
}

onMounted(async () => {
  try { statsRaw.value = await authFetch('/stats') } finally { statsLoading.value = false }
  loadUeberblick()
  pollUnread()
  unreadTimer = setInterval(() => { pollUnread(); loadUeberblick() }, 30000)
})

import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => { if (unreadTimer) clearInterval(unreadTimer) })

async function openTargetDetail(t) {
  detailTarget.value = t
  try {
    const full = await authFetch(`/targets/${t.RowKey}`)
    detailCheckliste.value = JSON.parse(full.checklisteJson || '[]')
  } catch { detailCheckliste.value = [] }
}

async function toggleChecklist(item) {
  item.done = !item.done
  await authFetch(`/targets/${detailTarget.value.RowKey}/checkliste`, {
    method: 'PATCH', data: { id: item.id, done: item.done }
  })
}
</script>
