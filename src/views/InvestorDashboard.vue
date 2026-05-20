<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Topbar -->
    <header class="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Building2 class="w-6 h-6 text-blue-900" />
        <span class="font-bold text-gray-900">ITUKV</span>
        <span class="text-gray-400 text-sm">· Investor-Portal</span>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-sm text-gray-600">{{ userName }}</span>
        <button @click="logout" class="text-sm text-gray-400 hover:text-gray-700 flex items-center gap-1">
          <LogOut class="w-4 h-4" />
          Abmelden
        </button>
      </div>
    </header>

    <div class="max-w-5xl mx-auto px-6 py-8">
      <!-- Tab Navigation -->
      <div class="flex gap-1 mb-8 bg-white rounded-xl border border-gray-100 p-1 w-fit">
        <button
          v-for="item in navItems" :key="item.tab"
          @click="tab = item.tab"
          :class="[
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            tab === item.tab ? 'bg-blue-900 text-white' : 'text-gray-600 hover:bg-gray-50'
          ]"
        >
          <component :is="item.icon" class="w-4 h-4" />
          {{ item.label }}
        </button>
      </div>

      <!-- Tab: Ausschreibungen -->
      <div v-if="tab === 'ausschreibungen'">
        <h2 class="text-xl font-bold text-gray-900 mb-2">Verfügbare IT-Unternehmen</h2>
        <p class="text-sm text-gray-500 mb-6">Anonymisierte Kurzprofile. Nach NDA-Unterzeichnung erhalten Sie das vollständige Exposé.</p>

        <div class="space-y-4">
          <div v-for="item in demoTargets" :key="item.id" class="bg-white rounded-xl border border-gray-100 p-6 hover:border-blue-200 transition-colors">
            <div class="flex items-start justify-between">
              <div>
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-xs font-mono bg-blue-50 text-blue-900 px-2 py-0.5 rounded">{{ item.mbNr }}</span>
                  <span class="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded font-medium">verfügbar</span>
                </div>
                <h3 class="font-semibold text-gray-900">{{ item.bezeichnung }}</h3>
                <p class="text-sm text-gray-500 mt-1">{{ item.region }} · {{ item.mitarbeiter }} Mitarbeiter · {{ item.umsatz }}</p>
              </div>
              <button class="flex items-center gap-2 px-4 py-2 bg-blue-900 text-white rounded-xl text-sm font-medium hover:bg-blue-800 transition-colors">
                <FileText class="w-4 h-4" />
                Exposé anfordern
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Meine Prozesse -->
      <div v-else-if="tab === 'prozesse'">
        <h2 class="text-xl font-bold text-gray-900 mb-6">Meine Prozesse</h2>
        <div class="bg-white rounded-xl border border-gray-100 p-6">
          <p class="text-sm text-gray-400">Sobald Sie ein NDA unterzeichnet haben, erscheinen Ihre aktiven Prozesse hier. (Phase 4)</p>
        </div>
      </div>

      <!-- Tab: Checkliste -->
      <div v-else-if="tab === 'checkliste'">
        <h2 class="text-xl font-bold text-gray-900 mb-6">Meine Checkliste</h2>
        <div class="bg-white rounded-xl border border-gray-100 p-6">
          <ul class="space-y-3">
            <li v-for="item in checkliste" :key="item.id" class="flex items-center gap-3">
              <div :class="['w-5 h-5 rounded-full border-2 flex-shrink-0', item.done ? 'bg-green-500 border-green-500' : 'border-gray-300']">
                <Check v-if="item.done" class="w-3 h-3 text-white m-auto mt-0.5" />
              </div>
              <span :class="['text-sm', item.done ? 'line-through text-gray-400' : 'text-gray-700']">{{ item.label }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Building2, LogOut, Megaphone, GitBranch, CheckSquare, FileText, Check } from '@lucide/vue'

const props = defineProps({ userName: String })
const emit = defineEmits(['logout'])

const tab = ref('ausschreibungen')

const navItems = [
  { tab: 'ausschreibungen', label: 'Ausschreibungen', icon: Megaphone },
  { tab: 'prozesse', label: 'Meine Prozesse', icon: GitBranch },
  { tab: 'checkliste', label: 'Checkliste', icon: CheckSquare },
]

const demoTargets = [
  { id: 1, mbNr: 'mb-202', bezeichnung: 'IT-Systemhaus · Managed Services', region: 'Raum Nürnberg', mitarbeiter: '12', umsatz: 'ca. 2,1 Mio. €' },
  { id: 2, mbNr: 'mb-219', bezeichnung: 'IT-Dienstleister · Cloud & Security', region: 'Raum München', mitarbeiter: '8', umsatz: 'ca. 1,4 Mio. €' },
  { id: 3, mbNr: 'mb-232', bezeichnung: 'IT-Systemhaus · Infrastruktur', region: 'Raum Darmstadt', mitarbeiter: '15', umsatz: 'ca. 2,8 Mio. €' },
]

const checkliste = ref([
  { id: 1, label: 'NDA unterzeichnet', done: false },
  { id: 2, label: 'Exposé erhalten und geprüft', done: false },
  { id: 3, label: 'Element-Raum / Datenraum geöffnet', done: false },
  { id: 4, label: 'Erstgespräch vereinbart', done: false },
  { id: 5, label: 'Gebot abgegeben', done: false },
])

function logout() {
  sessionStorage.clear()
  emit('logout')
}
</script>
