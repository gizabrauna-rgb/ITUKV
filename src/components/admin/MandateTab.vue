<template>
  <div>
    <!-- Toggle-Leiste: Cockpit vs. Liste -->
    <div class="flex items-center gap-2 mb-4">
      <div class="bg-white border border-gray-200 rounded-xl p-1 inline-flex">
        <button @click="view = 'cockpit'"
          :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                   view === 'cockpit' ? 'bg-[#0088ba] text-white' : 'text-gray-600 hover:bg-gray-50']">
          <Workflow class="w-4 h-4" /> Cockpit
        </button>
        <button @click="view = 'liste'"
          :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                   view === 'liste' ? 'bg-[#0088ba] text-white' : 'text-gray-600 hover:bg-gray-50']">
          <List class="w-4 h-4" /> Listen-Ansicht
        </button>
      </div>
    </div>

    <MandateCockpit v-if="view === 'cockpit'" @open-akte="id => $emit('open-detail', { RowKey: id })" />
    <TargetsTab v-else @open-detail="t => $emit('open-detail', t)" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Workflow, List } from '@lucide/vue'
import MandateCockpit from './MandateCockpit.vue'
import TargetsTab from './TargetsTab.vue'

defineEmits(['open-detail'])

const view = ref(localStorage.getItem('mandate.view') || 'cockpit')
// View-Wahl merken
import { watch } from 'vue'
watch(view, v => localStorage.setItem('mandate.view', v))
</script>
