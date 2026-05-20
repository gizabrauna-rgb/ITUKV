<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Topbar -->
    <header class="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Building2 class="w-6 h-6 text-blue-900" />
        <span class="font-bold text-gray-900">ITUKV</span>
        <span class="text-gray-400 text-sm">· Mein Verkaufsprojekt</span>
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

      <!-- Tab: Mein Projekt -->
      <div v-if="tab === 'projekt'">
        <h2 class="text-xl font-bold text-gray-900 mb-6">Mein Projekt</h2>

        <!-- Fortschrittsbalken -->
        <div class="bg-white rounded-xl border border-gray-100 p-6 mb-6">
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-medium text-gray-700">Gesamtfortschritt</span>
            <span class="text-sm font-bold text-blue-900">0 / {{ checkliste.length }} erledigt</span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2">
            <div class="bg-blue-900 h-2 rounded-full" style="width: 0%"></div>
          </div>
        </div>

        <!-- Checkliste -->
        <div class="bg-white rounded-xl border border-gray-100 p-6">
          <h3 class="font-semibold text-gray-800 mb-4">Checkliste</h3>
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

      <!-- Tab: Interessenten -->
      <div v-else-if="tab === 'interessenten'">
        <h2 class="text-xl font-bold text-gray-900 mb-6">Meine Interessenten</h2>
        <div class="bg-white rounded-xl border border-gray-100 p-6">
          <p class="text-sm text-gray-400">Interessenten werden hier angezeigt, sobald NDAs eingegangen sind. (Phase 4)</p>
        </div>
      </div>

      <!-- Tab: Dokumente -->
      <div v-else-if="tab === 'dokumente'">
        <h2 class="text-xl font-bold text-gray-900 mb-6">Meine Dokumente</h2>
        <div class="grid grid-cols-2 gap-4">
          <div v-for="folder in dokumentOrdner" :key="folder" class="bg-white rounded-xl border border-gray-100 p-4 flex items-center gap-3 hover:border-blue-200 cursor-pointer transition-colors">
            <FolderOpen class="w-5 h-5 text-blue-900" />
            <span class="text-sm font-medium text-gray-700">{{ folder }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Building2, LogOut, Briefcase, Users, FolderOpen, Check } from '@lucide/vue'

const props = defineProps({ userName: String })
const emit = defineEmits(['logout'])

const tab = ref('projekt')

const navItems = [
  { tab: 'projekt', label: 'Mein Projekt', icon: Briefcase },
  { tab: 'interessenten', label: 'Interessenten', icon: Users },
  { tab: 'dokumente', label: 'Dokumente', icon: FolderOpen },
]

const checkliste = ref([
  { id: 1, label: 'Unternehmensbewertung', done: false },
  { id: 2, label: 'Fragebogen Unternehmensbewertung ausgefüllt', done: false },
  { id: 3, label: 'Exposé erstellt', done: false },
  { id: 4, label: 'Mandat unterschrieben', done: false },
  { id: 5, label: 'Element-Raum eröffnet', done: false },
  { id: 6, label: 'Target beworben / Ausschreibung aktiv', done: false },
  { id: 7, label: 'Eingehende NDAs geprüft', done: false },
  { id: 8, label: 'Alle Dokumente vollständig', done: false },
])

const dokumentOrdner = [
  'Unterlagen Ausschreibung',
  'Exposé',
  'Protokoll',
  'NDA',
  'Gesprächsnotizen',
  'Datenraum',
  'Beratervertrag',
  'Diverses',
]

function logout() {
  sessionStorage.clear()
  emit('logout')
}
</script>
