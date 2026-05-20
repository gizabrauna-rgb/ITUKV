<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Topbar -->
    <header class="bg-blue-900 text-white px-6 py-4 flex items-center justify-between shadow">
      <div class="flex items-center gap-3">
        <Building2 class="w-6 h-6" />
        <span class="font-bold text-lg">ITUKV Dashboard</span>
        <span class="text-blue-300 text-sm ml-2">mibeca intern</span>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-sm text-blue-200">{{ userName }}</span>
        <button @click="logout" class="text-sm text-blue-300 hover:text-white flex items-center gap-1">
          <LogOut class="w-4 h-4" />
          Abmelden
        </button>
      </div>
    </header>

    <div class="flex">
      <!-- Sidebar Navigation -->
      <nav class="w-56 min-h-screen bg-white border-r border-gray-100 pt-6 flex-shrink-0">
        <ul class="space-y-1 px-3">
          <li v-for="item in navItems" :key="item.tab">
            <button
              @click="tab = item.tab"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors',
                tab === item.tab
                  ? 'bg-blue-50 text-blue-900'
                  : 'text-gray-600 hover:bg-gray-50'
              ]"
            >
              <component :is="item.icon" class="w-4 h-4" />
              {{ item.label }}
            </button>
          </li>
        </ul>
      </nav>

      <!-- Main Content -->
      <main class="flex-1 p-8">
        <!-- Tab: Übersicht -->
        <div v-if="tab === 'uebersicht'">
          <h2 class="text-xl font-bold text-gray-900 mb-6">Übersicht</h2>
          <div class="grid grid-cols-4 gap-4 mb-8">
            <div v-for="stat in stats" :key="stat.label" class="bg-white rounded-xl border border-gray-100 p-5">
              <div class="text-2xl font-bold text-gray-900">{{ stat.value }}</div>
              <div class="text-sm text-gray-500 mt-1">{{ stat.label }}</div>
            </div>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 p-6">
            <h3 class="font-semibold text-gray-800 mb-4">Letzte Aktivitäten</h3>
            <p class="text-sm text-gray-400">Noch keine Aktivitäten vorhanden.</p>
          </div>
        </div>

        <!-- Tab: Targets -->
        <div v-else-if="tab === 'targets'">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold text-gray-900">Targets (Verkaufsmandate)</h2>
            <button class="flex items-center gap-2 px-4 py-2 bg-blue-900 text-white rounded-xl text-sm font-medium hover:bg-blue-800">
              <Plus class="w-4 h-4" />
              Neues Mandat
            </button>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 p-6">
            <p class="text-sm text-gray-400">Targets werden hier angezeigt. Backend-Anbindung folgt in Phase 2.</p>
          </div>
        </div>

        <!-- Tab: Pipeline -->
        <div v-else-if="tab === 'pipeline'">
          <h2 class="text-xl font-bold text-gray-900 mb-6">Interessenten-Pipeline</h2>
          <div class="bg-white rounded-xl border border-gray-100 p-6">
            <p class="text-sm text-gray-400">Kanban-Pipeline folgt in Phase 2.</p>
          </div>
        </div>

        <!-- Tab: CRM -->
        <div v-else-if="tab === 'crm'">
          <h2 class="text-xl font-bold text-gray-900 mb-6">CRM / Investoren-Datenbank</h2>
          <div class="bg-white rounded-xl border border-gray-100 p-6">
            <p class="text-sm text-gray-400">CRM-Import und Kartenansicht folgen in Phase 3.</p>
          </div>
        </div>

        <!-- Tab: Ausschreibungen -->
        <div v-else-if="tab === 'ausschreibungen'">
          <h2 class="text-xl font-bold text-gray-900 mb-6">Ausschreibungen</h2>
          <div class="bg-white rounded-xl border border-gray-100 p-6">
            <p class="text-sm text-gray-400">Ausschreibungsübersicht folgt in Phase 2.</p>
          </div>
        </div>

        <!-- Tab: Dokumente -->
        <div v-else-if="tab === 'dokumente'">
          <h2 class="text-xl font-bold text-gray-900 mb-6">Dokumente</h2>
          <div class="bg-white rounded-xl border border-gray-100 p-6">
            <p class="text-sm text-gray-400">Dokumentenverwaltung folgt in Phase 2.</p>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Building2, LogOut, LayoutDashboard, Briefcase, GitBranch, Users, Megaphone, FolderOpen, Plus } from '@lucide/vue'

const props = defineProps({ userName: String })
const emit = defineEmits(['logout'])

const tab = ref('uebersicht')

const navItems = [
  { tab: 'uebersicht', label: 'Übersicht', icon: LayoutDashboard },
  { tab: 'targets', label: 'Targets', icon: Briefcase },
  { tab: 'pipeline', label: 'Pipeline', icon: GitBranch },
  { tab: 'crm', label: 'CRM / Investoren', icon: Users },
  { tab: 'ausschreibungen', label: 'Ausschreibungen', icon: Megaphone },
  { tab: 'dokumente', label: 'Dokumente', icon: FolderOpen },
]

const stats = [
  { label: 'Aktive Targets', value: '—' },
  { label: 'Offene NDAs', value: '—' },
  { label: 'Investoren gesamt', value: '—' },
  { label: 'Deals abgeschlossen', value: '—' },
]

function logout() {
  sessionStorage.clear()
  emit('logout')
}
</script>
