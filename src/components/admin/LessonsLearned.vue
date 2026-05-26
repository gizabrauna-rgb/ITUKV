<template>
  <div>
    <div class="mb-5">
      <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
        <BookOpen class="w-6 h-6 text-[#0088ba]" /> Lessons Learned
      </h2>
      <p class="text-sm text-gray-500 mt-1">Retrospektive nach Deal-Abschluss. Diese Erkenntnisse fließen in die Wissensdatenbank im Controlling.</p>
    </div>

    <div class="bg-white rounded-xl border border-gray-100 p-5 space-y-4">
      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block flex items-center gap-1.5">
          <span class="text-green-600">✅</span> Was lief gut? (Pro)
        </label>
        <textarea v-model="data.pro" @blur="save" rows="3"
          placeholder="z.B. Käufer und Verkäufer kulturell gut zusammengepasst – kurze Verhandlungsphase"
          class="input resize-y"></textarea>
      </div>

      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block flex items-center gap-1.5">
          <span class="text-red-600">❌</span> Was war schwierig? (Contra)
        </label>
        <textarea v-model="data.contra" @blur="save" rows="3"
          placeholder="z.B. Due Diligence über IT-Infrastruktur zog sich, weil Tools-Liste fehlte"
          class="input resize-y"></textarea>
      </div>

      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block flex items-center gap-1.5">
          <span class="text-purple-600">💡</span> Was würden wir anders machen?
        </label>
        <textarea v-model="data.anders" @blur="save" rows="3"
          placeholder="z.B. Frühzeitig in Phase 6 schon die komplette IT-Bestandsliste anfordern"
          class="input resize-y"></textarea>
      </div>

      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block flex items-center gap-1.5">
          <span class="text-amber-600">🎯</span> Schlüssel-Erkenntnis (1-2 Sätze)
        </label>
        <input v-model="data.keyLearning" @blur="save"
          placeholder="z.B. Buy-and-Build-Deals brauchen Cultural Fit, nicht nur Zahlen"
          class="input" />
      </div>

      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block">Tags (kommagetrennt)</label>
        <input :value="(data.tags || []).join(', ')" @blur="setTags($event.target.value)"
          placeholder="z.B. DueDiligence, Kultur, MSP, schneller-Deal"
          class="input" />
        <div v-if="data.tags?.length" class="flex flex-wrap gap-1 mt-2">
          <span v-for="t in data.tags" :key="t" class="text-xs bg-[#0088ba]/10 text-[#0088ba] px-2 py-0.5 rounded-full">#{{ t }}</span>
        </div>
      </div>

      <p v-if="lastSaved" class="text-xs text-gray-400">Zuletzt gespeichert: {{ lastSavedHuman }}</p>
    </div>

    <div class="mt-4 bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-900">
      <strong>Tipp:</strong> Diese Lessons Learned werden in der <strong>Controlling-Übersicht</strong> als
      Wissensdatenbank über alle Deals aggregiert – perfekt für Webinare und interne Schulungen.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { BookOpen } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String })
const data = ref({ pro: '', contra: '', anders: '', keyLearning: '', tags: [] })
const lastSaved = ref(null)

function setTags(s) {
  data.value.tags = s.split(/[,;]/).map(t => t.trim()).filter(Boolean)
  save()
}

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, lessonsLearnedJson: JSON.stringify(data.value) } })
      lastSaved.value = new Date().toISOString()
    } catch (e) { console.error(e) }
  }, 500)
}

const lastSavedHuman = computed(() => lastSaved.value ? new Date(lastSaved.value).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) : '')

onMounted(async () => {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (t.lessonsLearnedJson) {
      try { Object.assign(data.value, JSON.parse(t.lessonsLearnedJson)) } catch {}
    }
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
