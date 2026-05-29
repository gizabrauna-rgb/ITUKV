<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Meine Akquisitionen</h2>
        <p class="text-sm text-gray-500 mt-1">
          Hier verwaltest du die Firmen, die du aktiv verfolgst. Pro Akquisition siehst du den aktuellen Stand, Aufgaben und Notizen.
        </p>
      </div>
      <button @click="openNew" class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700">
        <Plus class="w-4 h-4" /> Neue Akquisition
      </button>
    </div>

    <div v-if="!akquisitionen.length" class="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-10 text-center">
      <Target class="w-10 h-10 text-gray-300 mx-auto mb-3" />
      <h3 class="font-semibold text-gray-700">Noch keine Akquisition angelegt</h3>
      <p class="text-sm text-gray-500 mt-1">Sobald du im Tab „Target-Vorschläge" auf „Interesse" klickst, entsteht hier automatisch eine Akquisition. Oder lege manuell eine an.</p>
      <button @click="openNew" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700">
        Erste Akquisition anlegen
      </button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <button v-for="akq in akquisitionen" :key="akq.id"
        @click="openEdit(akq)"
        class="text-left bg-white rounded-2xl border border-gray-100 p-4 hover:border-blue-200 transition-colors">
        <div class="flex items-start justify-between gap-2 mb-2">
          <h3 class="font-bold text-gray-900 truncate flex-1">{{ akq.name }}</h3>
          <span :class="['text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase whitespace-nowrap', statusInfo(akq.status || 'laufend').cls]">
            {{ akq.status || 'laufend' }}
          </span>
        </div>
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
            Phase {{ akq.phase || 1 }} · {{ phaseInfo(akq.phase || 1).label }}
          </span>
          <span v-if="akq.quelleKandidatId" class="text-[10px] text-purple-600">aus Vorschlag</span>
        </div>
        <div class="flex items-center gap-3 text-xs text-gray-500">
          <span v-if="offeneAufgaben(akq)" class="flex items-center gap-1">
            <ListTodo class="w-3 h-3" /> {{ offeneAufgaben(akq) }} offen
          </span>
          <span v-if="akq.branche" class="truncate">{{ akq.branche }}</span>
          <span v-if="akq.region">{{ akq.region }}</span>
        </div>
      </button>
    </div>

    <AkquisitionDetailModal
      v-if="editing"
      :model-value="editing"
      @close="editing = null"
      @save="onSave"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Target, ListTodo } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { phaseInfo, statusInfo } from '../../data/akquisitionsPhasen.js'
import AkquisitionDetailModal from './AkquisitionDetailModal.vue'

const props = defineProps({ targetId: { type: String, required: true } })

const akquisitionen = ref([])
const editing = ref(null)

async function load() {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    try { akquisitionen.value = JSON.parse(t.akquisitionenJson || '[]') } catch { akquisitionen.value = [] }
    if (!Array.isArray(akquisitionen.value)) akquisitionen.value = []
  } catch {}
}
onMounted(load)

function openNew() {
  editing.value = {
    id: 'akq' + Date.now(),
    createdAt: new Date().toISOString(),
    name: '',
    phase: 1,
    status: 'laufend',
  }
}
function openEdit(akq) {
  editing.value = { ...akq }
}

async function onSave(updated) {
  const list = [...akquisitionen.value]
  const i = list.findIndex(a => a.id === updated.id)
  if (i >= 0) list[i] = updated
  else list.push(updated)
  await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, akquisitionenJson: JSON.stringify(list) } })
  akquisitionen.value = list
  editing.value = null
}

function offeneAufgaben(akq) {
  return (akq.aufgaben || []).filter(a => !a.erledigt).length
}
</script>
