<template>
  <div class="flex gap-6 h-full">
    <!-- Linke Spalte: Target auswählen -->
    <div class="w-64 flex-shrink-0 flex flex-col" style="max-height: calc(100vh - 140px)">
      <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Target wählen</h3>
      <div class="relative mb-2">
        <input v-model="search" placeholder="Suche mb-Nr, Name, Firma…"
          class="w-full pl-8 pr-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
        <Search class="w-4 h-4 text-gray-400 absolute left-2.5 top-2.5" />
      </div>
      <div class="text-xs text-gray-400 mb-2">{{ filteredTargets.length }} / {{ targets.length }}</div>
      <div class="space-y-1 overflow-y-auto pr-1 flex-1">
        <button
          v-for="t in filteredTargets" :key="t.RowKey"
          @click="selectedTarget = t"
          :class="['w-full text-left px-3 py-2 rounded-xl text-sm transition-colors', selectedTarget?.RowKey === t.RowKey ? 'bg-[#0088ba] text-white' : 'hover:bg-gray-100 text-gray-700']"
        >
          <div class="font-mono text-xs opacity-70">{{ t.mbNr }}</div>
          <div class="truncate">{{ t.verkaueferName }}</div>
          <div v-if="t.firma" class="truncate text-xs opacity-60">{{ t.firma }}</div>
        </button>
      </div>
    </div>

    <!-- Rechte Spalte: dieselbe DokumenteAkte-Komponente wie in der Projekt-Akte -->
    <div class="flex-1">
      <div v-if="!selectedTarget" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">
        <FolderOpen class="w-10 h-10 mx-auto mb-3 text-gray-200" />
        Bitte links ein Target auswählen.
      </div>
      <DokumenteAkte v-else :key="selectedTarget.RowKey" :target-id="selectedTarget.RowKey" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { FolderOpen, Search } from '@lucide/vue'
import { getTargets } from '../../api.js'
import DokumenteAkte from './DokumenteAkte.vue'

const targets = ref([])
const search = ref('')
const selectedTarget = ref(null)

const filteredTargets = computed(() => {
  if (!search.value) return targets.value
  const q = search.value.toLowerCase()
  return targets.value.filter(t =>
    (t.mbNr || '').toLowerCase().includes(q) ||
    (t.verkaueferName || '').toLowerCase().includes(q) ||
    (t.firma || '').toLowerCase().includes(q)
  )
})

onMounted(async () => {
  try {
    targets.value = (await getTargets()).sort((a, b) => {
      const na = parseInt((a.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
      const nb = parseInt((b.mbNr || '').replace(/[^\d]/g, ''), 10) || 0
      return na - nb
    })
  } catch {}
})
</script>
