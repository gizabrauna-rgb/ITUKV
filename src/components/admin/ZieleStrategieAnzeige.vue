<template>
  <div class="space-y-6">
    <div v-if="!hasAny" class="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
      <FileQuestion class="w-10 h-10 text-gray-300 mx-auto mb-3" />
      <h3 class="font-semibold text-gray-700">Noch keine Eingaben vom Mandanten</h3>
      <p class="text-sm text-gray-500 mt-2">
        Der Mandant hat das Formular „{{ isKaufMandat ? 'Akquisitionsstrategie' : 'Ziele & Motivationen' }}" noch nicht ausgefüllt.
      </p>
    </div>

    <!-- VERKÄUFER: Ziele & Motivationen -->
    <template v-if="!isKaufMandat && ziele">
      <div class="bg-white border border-gray-100 rounded-2xl p-5">
        <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Target class="w-5 h-5 text-[#0088ba]" /> Ziele & Motivationen
        </h3>

        <section v-if="ziele.motivation?.length || ziele.motivationFrei" class="mb-5">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Warum verkauft der Mandant?</h4>
          <div class="flex flex-wrap gap-1.5 mb-2">
            <span v-for="m in (ziele.motivation || [])" :key="m" class="inline-block bg-[#0088ba]/10 text-[#0088ba] text-xs px-2 py-1 rounded-full">{{ m }}</span>
          </div>
          <p v-if="ziele.motivationFrei" class="text-sm text-gray-700 mt-1 italic">„{{ ziele.motivationFrei }}"</p>
        </section>

        <section class="grid grid-cols-2 gap-4 mb-5">
          <div v-if="ziele.zeitrahmen">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Zeitrahmen</h4>
            <p class="text-sm text-gray-800">{{ ziele.zeitrahmen }}</p>
          </div>
          <div v-if="ziele.wunschErloes">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Wunsch-Verkaufserlös</h4>
            <p class="text-sm text-gray-800">{{ ziele.wunschErloes }}</p>
          </div>
        </section>

        <section v-if="ziele.bleibedauer || ziele.wunschrolle || ziele.aufgabenGerne" class="mb-5">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Rolle nach der Transaktion</h4>
          <div class="space-y-2 text-sm text-gray-700">
            <div v-if="ziele.bleibedauer"><strong>Bleibedauer:</strong> {{ ziele.bleibedauer }}</div>
            <div v-if="ziele.wunschrolle"><strong>Wunsch-Rolle:</strong> {{ ziele.wunschrolle }}</div>
            <div v-if="ziele.aufgabenGerne"><strong>Lieblings-Aufgaben:</strong> {{ ziele.aufgabenGerne }}</div>
          </div>
        </section>

        <section v-if="ziele.mitarbeiterWunsch || ziele.standortWunsch" class="grid grid-cols-2 gap-4 mb-5">
          <div v-if="ziele.mitarbeiterWunsch">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Mitarbeiter</h4>
            <p class="text-sm text-gray-800">{{ ziele.mitarbeiterWunsch }}</p>
          </div>
          <div v-if="ziele.standortWunsch">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Standort</h4>
            <p class="text-sm text-gray-800">{{ ziele.standortWunsch }}</p>
          </div>
        </section>

        <section v-if="ziele.earnOut || ziele.verkaeuferdarlehen || ziele.kaeuferTyp" class="mb-5">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Deal-Struktur</h4>
          <div class="grid grid-cols-3 gap-3 text-sm">
            <div v-if="ziele.earnOut"><strong>Earn-Out:</strong><br/>{{ ziele.earnOut }}</div>
            <div v-if="ziele.verkaeuferdarlehen"><strong>Verkäuferdarlehen:</strong><br/>{{ ziele.verkaeuferdarlehen }}</div>
            <div v-if="ziele.kaeuferTyp"><strong>Wunsch-Käufer:</strong><br/>{{ ziele.kaeuferTyp }}</div>
          </div>
        </section>

        <section v-if="ziele.dealBreaker" class="bg-red-50 border border-red-200 rounded-xl p-3">
          <h4 class="text-xs font-semibold text-red-700 uppercase tracking-wide mb-1 flex items-center gap-1">
            <Ban class="w-3 h-3" /> Deal-Breaker
          </h4>
          <p class="text-sm text-red-900 whitespace-pre-wrap">{{ ziele.dealBreaker }}</p>
        </section>
      </div>
    </template>

    <!-- KÄUFER: Akquisitionsstrategie -->
    <template v-if="isKaufMandat && akq">
      <div class="bg-white border border-gray-100 rounded-2xl p-5">
        <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Target class="w-5 h-5 text-[#0088ba]" /> Akquisitionsstrategie & Ziele
        </h3>

        <section v-if="akq.motivation?.length || akq.motivationFrei" class="mb-5">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Warum will der Käufer kaufen?</h4>
          <div class="flex flex-wrap gap-1.5 mb-2">
            <span v-for="m in (akq.motivation || [])" :key="m" class="inline-block bg-[#0088ba]/10 text-[#0088ba] text-xs px-2 py-1 rounded-full">{{ m }}</span>
          </div>
          <p v-if="akq.motivationFrei" class="text-sm text-gray-700 mt-1 italic">„{{ akq.motivationFrei }}"</p>
        </section>

        <section class="grid grid-cols-2 gap-4 mb-5">
          <div v-if="akq.holdPeriod">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Hold-Period</h4>
            <p class="text-sm text-gray-800">{{ akq.holdPeriod }}</p>
          </div>
          <div v-if="akq.maxKaufpreis">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Max. Kaufpreis-Range</h4>
            <p class="text-sm text-gray-800">{{ akq.maxKaufpreis }}</p>
          </div>
        </section>

        <section v-if="akq.eigenkapital || akq.bankFinanzierung || akq.verkaeuferdarlehen" class="mb-5">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Finanzierung</h4>
          <div class="grid grid-cols-3 gap-3 text-sm">
            <div v-if="akq.eigenkapital"><strong>Eigenkapital:</strong><br/>{{ akq.eigenkapital }}</div>
            <div v-if="akq.bankFinanzierung"><strong>Bank:</strong><br/>{{ akq.bankFinanzierung }}</div>
            <div v-if="akq.verkaeuferdarlehen"><strong>VK-Darlehen / Earn-Out:</strong><br/>{{ akq.verkaeuferdarlehen }}</div>
          </div>
        </section>

        <section v-if="akq.branche || akq.region || akq.mitarbeitergroesse || akq.umsatzgroesse" class="mb-5">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Zielunternehmen-Profil</h4>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div v-if="akq.branche"><strong>Branche:</strong> {{ akq.branche }}</div>
            <div v-if="akq.region"><strong>Region:</strong> {{ akq.region }}</div>
            <div v-if="akq.mitarbeitergroesse"><strong>Mitarbeiter:</strong> {{ akq.mitarbeitergroesse }}</div>
            <div v-if="akq.umsatzgroesse"><strong>Umsatz:</strong> {{ akq.umsatzgroesse }}</div>
          </div>
        </section>

        <section v-if="akq.gfVerbleib || akq.synergien" class="grid grid-cols-2 gap-4 mb-5">
          <div v-if="akq.gfVerbleib">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">GF-Verbleib</h4>
            <p class="text-sm text-gray-800">{{ akq.gfVerbleib }}</p>
          </div>
          <div v-if="akq.synergien">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Strategische Synergien</h4>
            <p class="text-sm text-gray-800">{{ akq.synergien }}</p>
          </div>
        </section>

        <section v-if="akq.dealBreaker" class="bg-red-50 border border-red-200 rounded-xl p-3">
          <h4 class="text-xs font-semibold text-red-700 uppercase tracking-wide mb-1 flex items-center gap-1">
            <Ban class="w-3 h-3" /> Deal-Breaker
          </h4>
          <p class="text-sm text-red-900 whitespace-pre-wrap">{{ akq.dealBreaker }}</p>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Target, Ban, FileQuestion } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String })

const ziele = ref(null)
const akq = ref(null)
const isKaufMandat = ref(false)

async function load() {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    isKaufMandat.value = /kauf|investor/i.test(t.projekttyp || '')
    try { ziele.value = JSON.parse(t.zieleMotivationenJson || '{}') } catch { ziele.value = {} }
    try { akq.value = JSON.parse(t.akquisitionsstrategieJson || '{}') } catch { akq.value = {} }
  } catch (e) { console.error(e) }
}
onMounted(load)
watch(() => props.targetId, load)

const hasAny = computed(() => {
  if (isKaufMandat.value) {
    return akq.value && Object.values(akq.value).some(v => Array.isArray(v) ? v.length : !!v)
  }
  return ziele.value && Object.values(ziele.value).some(v => Array.isArray(v) ? v.length : !!v)
})
</script>
