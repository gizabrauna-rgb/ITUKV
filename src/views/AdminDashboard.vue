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
            class="flex items-center gap-2 px-3 py-1.5 bg-[#097e92]/20 hover:bg-[#097e92]/30 rounded-lg text-xs font-medium text-white transition-colors">
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
              <Briefcase class="w-4 h-4 text-[#097e92]" />
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

        <!-- Posteingang / Ungelesen-Badge -->
        <button @click="tab = 'targets'" class="relative flex items-center gap-1.5 text-xs text-gray-300 hover:text-white" :title="`${unreadTotal} ungelesene Verlauf-Eintraege`">
          <Bell class="w-4 h-4" />
          <span v-if="unreadTotal > 0" class="absolute -top-1 -right-2 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[16px] h-4 px-1 flex items-center justify-center">
            {{ unreadTotal > 99 ? '99+' : unreadTotal }}
          </span>
        </button>
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
                'w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm transition-colors',
                tab === item.tab
                  ? 'bg-[#097e92]/10 text-[#097e92] font-semibold'
                  : 'text-gray-600 hover:bg-gray-50'
              ]"
            >
              <component :is="item.icon" class="w-4 h-4 flex-shrink-0" />
              {{ item.label }}
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
          <div class="bg-white rounded-xl border border-gray-100 p-6">
            <h3 class="font-semibold text-gray-800 mb-4 text-sm">Schnellzugriff</h3>
            <div class="grid grid-cols-3 gap-3">
              <button v-for="q in quickAccess" :key="q.tab" @click="tab = q.tab"
                class="flex items-center gap-3 p-4 rounded-xl border border-gray-100 hover:border-[#097e92]/30 hover:bg-[#097e92]/5 transition-all text-left">
                <component :is="q.icon" class="w-5 h-5 text-[#097e92]" />
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
          <TargetAkte v-if="akteTargetId" :target-id="akteTargetId" @close="akteTargetId = null" />
          <TargetsTab v-else @open-detail="openAkte" />
        </div>

        <!-- Pipeline -->
        <div v-else-if="tab === 'pipeline'">
          <PipelineTab />
        </div>

        <!-- CRM -->
        <div v-else-if="tab === 'crm'">
          <CrmTab />
        </div>

        <!-- Ausschreibungen -->
        <div v-else-if="tab === 'ausschreibungen'">
          <AusschreibungenTab />
        </div>

        <!-- Dokumente -->
        <div v-else-if="tab === 'dokumente'">
          <DokumenteTab />
        </div>

        <!-- Benutzer -->
        <!-- Controlling -->
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
  Users, Megaphone, FolderOpen, X, Check, Eye, ChevronDown, Settings, UserCog, Workflow, Bell, BarChart3
} from '@lucide/vue'
import { authFetch, verlaufUnreadCount } from '../api.js'
import TargetsTab from '../components/admin/TargetsTab.vue'
import PipelineTab from '../components/admin/PipelineTab.vue'
import CrmTab from '../components/admin/CrmTab.vue'
import AusschreibungenTab from '../components/admin/AusschreibungenTab.vue'
import DokumenteTab from '../components/admin/DokumenteTab.vue'
import BenutzerTab from '../components/admin/BenutzerTab.vue'
import EinstellungenTab from '../components/admin/EinstellungenTab.vue'
import Controlling from '../components/admin/Controlling.vue'
import TargetAkte from '../components/admin/TargetAkte.vue'

const props = defineProps({ userName: String })
const emit = defineEmits(['logout', 'switch-view'])

const tab = ref('uebersicht')
const showSwitcher = ref(false)

const targetTypes = ['UVE Target', 'Projekt Target', 'MC Target']
const investorTypes = ['Projekt Investoren', 'MC Investoren']

function switchTo(view) {
  showSwitcher.value = false
  emit('switch-view', view)
}
const statsLoading = ref(true)
const statsRaw = ref({ aktiveTargets: 0, offeneNdas: 0, investorenGesamt: 0, dealsAbgeschlossen: 0 })
const detailTarget = ref(null)
const detailCheckliste = ref([])
const akteTargetId = ref(null)

function openAkte(target) {
  akteTargetId.value = target.RowKey
}

const navItems = [
  { tab: 'uebersicht', label: 'Übersicht', icon: LayoutDashboard },
  { tab: 'targets', label: 'Projekte', icon: Briefcase },
  { tab: 'pipeline', label: 'Pipeline', icon: GitBranch },
  { tab: 'crm', label: 'Kundenstamm', icon: Users },
  { tab: 'ausschreibungen', label: 'Ausschreibungen', icon: Megaphone },
  { tab: 'dokumente', label: 'Dokumente', icon: FolderOpen },
  { tab: 'controlling', label: 'Controlling', icon: BarChart3 },
  { tab: 'benutzer', label: 'Benutzer', icon: UserCog },
  { tab: 'einstellungen', label: 'Einstellungen', icon: Settings },
]

const quickAccess = [
  { tab: 'targets', label: 'Targets', desc: 'Mandate verwalten', icon: Briefcase },
  { tab: 'pipeline', label: 'Pipeline', desc: 'Interessenten', icon: GitBranch },
  { tab: 'crm', label: 'Investoren', desc: 'CRM & Karte', icon: Users },
]

const statsData = computed(() => [
  { label: 'Aktive Targets', value: statsRaw.value.aktiveTargets, icon: Briefcase, color: '#097e92' },
  { label: 'Offene NDAs', value: statsRaw.value.offeneNdas, icon: GitBranch, color: '#c8b274' },
  { label: 'Investoren gesamt', value: statsRaw.value.investorenGesamt, icon: Users, color: '#3498db' },
  { label: 'Deals abgeschlossen', value: statsRaw.value.dealsAbgeschlossen, icon: Megaphone, color: '#22c55e' },
])

const checklistProgress = computed(() => {
  if (!detailCheckliste.value.length) return 0
  return Math.round((donCount.value / detailCheckliste.value.length) * 100)
})
const donCount = computed(() => detailCheckliste.value.filter(i => i.done).length)

const unreadTotal = ref(0)
async function pollUnread() {
  try {
    const r = await verlaufUnreadCount()
    unreadTotal.value = r?.total || 0
  } catch {}
}
let unreadTimer = null

onMounted(async () => {
  try { statsRaw.value = await authFetch('/stats') } finally { statsLoading.value = false }
  pollUnread()
  unreadTimer = setInterval(pollUnread, 30000)
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
