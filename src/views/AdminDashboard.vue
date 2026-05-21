<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Topbar -->
    <header class="bg-[#161e2a] text-white px-6 py-3 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-[#097e92] rounded-lg flex items-center justify-center">
          <Building2 class="w-4 h-4 text-white" />
        </div>
        <div>
          <span class="font-bold text-sm">ITUKV Dashboard</span>
          <span class="text-gray-400 text-xs ml-2">M&A · mibeca intern</span>
        </div>
      </div>
      <div class="flex items-center gap-4">
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
          <TargetsTab @open-detail="openTargetDetail" />
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

      </main>
    </div>

    <!-- Target Detail Panel -->
    <div v-if="detailTarget" class="fixed inset-0 bg-black/40 flex items-start justify-end z-50" @click.self="detailTarget = null">
      <div class="bg-white h-full w-full max-w-lg shadow-2xl overflow-y-auto">
        <div class="flex items-center justify-between p-5 border-b border-gray-100 bg-[#161e2a] text-white">
          <div>
            <span class="font-mono text-xs bg-[#097e92] px-2 py-0.5 rounded mr-2">{{ detailTarget.mbNr }}</span>
            <span class="font-bold">{{ detailTarget.verkaueferName }}</span>
          </div>
          <button @click="detailTarget = null"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="p-5 space-y-4">
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-gray-400 text-xs">Region</span><div class="font-medium">{{ detailTarget.region }}</div></div>
            <div><span class="text-gray-400 text-xs">Projekttyp</span><div class="font-medium">{{ detailTarget.projekttyp }}</div></div>
            <div><span class="text-gray-400 text-xs">Branche</span><div class="font-medium">{{ detailTarget.branche || '—' }}</div></div>
            <div><span class="text-gray-400 text-xs">Mitarbeiter</span><div class="font-medium">{{ detailTarget.mitarbeiter || '—' }}</div></div>
            <div><span class="text-gray-400 text-xs">Umsatz</span><div class="font-medium">{{ detailTarget.umsatz || '—' }}</div></div>
            <div><span class="text-gray-400 text-xs">PLZ</span><div class="font-medium">{{ detailTarget.plz || '—' }}</div></div>
          </div>
          <!-- Checkliste -->
          <div class="bg-gray-50 rounded-xl p-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-3">Checkliste</h4>
            <div v-if="detailCheckliste.length">
              <div class="mb-2">
                <div class="w-full bg-gray-200 rounded-full h-1.5">
                  <div class="bg-[#097e92] h-1.5 rounded-full transition-all" :style="`width: ${checklistProgress}%`"></div>
                </div>
                <div class="text-xs text-gray-400 mt-1">{{ donCount }} / {{ detailCheckliste.length }} erledigt</div>
              </div>
              <ul class="space-y-2">
                <li v-for="item in detailCheckliste" :key="item.id" class="flex items-center gap-2">
                  <button @click="toggleChecklist(item)" :class="['w-4 h-4 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors', item.done ? 'bg-[#097e92] border-[#097e92]' : 'border-gray-300 hover:border-[#097e92]']">
                    <Check v-if="item.done" class="w-2.5 h-2.5 text-white" />
                  </button>
                  <span :class="['text-sm', item.done ? 'line-through text-gray-400' : 'text-gray-700']">{{ item.label }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Building2, LogOut, LayoutDashboard, Briefcase, GitBranch,
  Users, Megaphone, FolderOpen, X, Check
} from '@lucide/vue'
import { authFetch } from '../api.js'
import TargetsTab from '../components/admin/TargetsTab.vue'
import PipelineTab from '../components/admin/PipelineTab.vue'
import CrmTab from '../components/admin/CrmTab.vue'
import AusschreibungenTab from '../components/admin/AusschreibungenTab.vue'
import DokumenteTab from '../components/admin/DokumenteTab.vue'

const props = defineProps({ userName: String })
const emit = defineEmits(['logout'])

const tab = ref('uebersicht')
const statsLoading = ref(true)
const statsRaw = ref({ aktiveTargets: 0, offeneNdas: 0, investorenGesamt: 0, dealsAbgeschlossen: 0 })
const detailTarget = ref(null)
const detailCheckliste = ref([])

const navItems = [
  { tab: 'uebersicht', label: 'Übersicht', icon: LayoutDashboard },
  { tab: 'targets', label: 'Targets', icon: Briefcase },
  { tab: 'pipeline', label: 'Pipeline', icon: GitBranch },
  { tab: 'crm', label: 'CRM / Investoren', icon: Users },
  { tab: 'ausschreibungen', label: 'Ausschreibungen', icon: Megaphone },
  { tab: 'dokumente', label: 'Dokumente', icon: FolderOpen },
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

onMounted(async () => {
  try { statsRaw.value = await authFetch('/stats') } finally { statsLoading.value = false }
})

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
