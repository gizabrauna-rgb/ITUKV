<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4 py-8 overflow-y-auto">
    <div class="bg-white rounded-2xl p-6 w-full max-w-3xl my-auto">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-xl font-bold text-gray-900">Akquisitionsstrategie & Ziele</h3>
          <p class="text-sm text-gray-500 mt-1">
            Diese Infos helfen Jenny, passende Verkaufs-Kandidaten für dich zu finden und die Verhandlung zu führen.
            Wird automatisch gespeichert.
          </p>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <X class="w-5 h-5" />
        </button>
      </div>

      <div class="space-y-6">
        <!-- Strategische Motivation -->
        <section>
          <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Sparkles class="w-4 h-4 text-[#0088ba]" />
            Warum willst du kaufen?
          </h4>
          <div class="space-y-2">
            <label v-for="m in motivationen" :key="m" class="flex items-start gap-2 p-3 border border-gray-100 rounded-xl hover:bg-gray-50 cursor-pointer">
              <input type="checkbox" :checked="(data.motivation || []).includes(m)" @change="toggleMotivation(m)" class="mt-0.5" />
              <span class="text-sm text-gray-700">{{ m }}</span>
            </label>
          </div>
          <textarea v-model="data.motivationFrei" @blur="save" rows="2" placeholder="Optional: Was treibt dich noch an?"
            class="mt-2 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 resize-none"></textarea>
        </section>

        <!-- Hold-Period + Budget -->
        <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Clock class="w-4 h-4 text-[#0088ba]" /> Geplante Hold-Period
            </h4>
            <select v-model="data.holdPeriod" @change="save" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
              <option value="">— Bitte wählen —</option>
              <option>3–5 Jahre (Finanzinvestor)</option>
              <option>5–10 Jahre (strategisch)</option>
              <option>10+ Jahre (langfristig)</option>
              <option>Buy-and-Build (mehrere Akquisitionen)</option>
              <option>Lebenslang behalten</option>
            </select>
          </div>
          <div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <TrendingUp class="w-4 h-4 text-[#0088ba]" /> Max. Kaufpreis-Range
            </h4>
            <input v-model="data.maxKaufpreis" @blur="save" placeholder="z.B. 500k – 2 Mio. €"
              class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm" />
          </div>
        </section>

        <!-- Finanzierung -->
        <section>
          <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Wallet class="w-4 h-4 text-[#0088ba]" />
            Finanzierung
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label class="text-xs text-gray-600">Eigenkapital verfügbar</label>
              <input v-model="data.eigenkapital" @blur="save" placeholder="z.B. 500.000 €"
                class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm" />
            </div>
            <div>
              <label class="text-xs text-gray-600">Bank-Finanzierung gewünscht</label>
              <select v-model="data.bankFinanzierung" @change="save" class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
                <option value="">—</option>
                <option>Ja, möglichst hoher Anteil</option>
                <option>Ja, anteilig (50%)</option>
                <option>Nur als Backup</option>
                <option>Nein, reine Eigenfinanzierung</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-gray-600">Verkäuferdarlehen / Earn-Out denkbar</label>
              <select v-model="data.verkaeuferdarlehen" @change="save" class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
                <option value="">—</option>
                <option>Ja, wünsche ich</option>
                <option>Bei richtigem Kandidaten</option>
                <option>Lieber nicht</option>
              </select>
            </div>
          </div>
        </section>

        <!-- Zielunternehmen-Profil -->
        <section>
          <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Building2 class="w-4 h-4 text-[#0088ba]" />
            Zielunternehmen-Profil
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-gray-600">Branche(n)</label>
              <input v-model="data.branche" @blur="save" placeholder="z.B. IT-Dienstleister, Maschinenbau"
                class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm" />
            </div>
            <div>
              <label class="text-xs text-gray-600">Region</label>
              <input v-model="data.region" @blur="save" placeholder="z.B. DACH, Bayern, 200km um Hannover"
                class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm" />
            </div>
            <div>
              <label class="text-xs text-gray-600">Mitarbeiter-Größe</label>
              <input v-model="data.mitarbeitergroesse" @blur="save" placeholder="z.B. 10–50 MA"
                class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm" />
            </div>
            <div>
              <label class="text-xs text-gray-600">Umsatz-Größe</label>
              <input v-model="data.umsatzgroesse" @blur="save" placeholder="z.B. 1–5 Mio. € p.a."
                class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm" />
            </div>
          </div>
        </section>

        <!-- GF-Verbleib + Synergien -->
        <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <User class="w-4 h-4 text-[#0088ba]" /> Soll der bisherige GF bleiben?
            </h4>
            <select v-model="data.gfVerbleib" @change="save" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
              <option value="">— Bitte wählen —</option>
              <option>Ja, möglichst lang (3+ Jahre)</option>
              <option>Übergangsphase 6–12 Monate</option>
              <option>Lieber nicht, ich übernehme selbst</option>
              <option>Egal, je nach Person</option>
            </select>
          </div>
          <div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Sparkles class="w-4 h-4 text-[#0088ba]" /> Strategische Synergien
            </h4>
            <input v-model="data.synergien" @blur="save" placeholder="z.B. gleiche Kundenbasis, Cross-Selling"
              class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm" />
          </div>
        </section>

        <!-- Deal-Breaker -->
        <section>
          <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <Ban class="w-4 h-4 text-red-500" />
            Was sind absolute Deal-Breaker für dich?
          </h4>
          <textarea v-model="data.dealBreaker" @blur="save" rows="3"
            placeholder="z.B. Standort muss in DACH bleiben / Keine Insolvenzen in der Vergangenheit / Kein hoher MA-Schwund"
            class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm resize-none"></textarea>
        </section>
      </div>

      <div class="flex gap-3 mt-6 pt-4 border-t border-gray-100">
        <div class="flex-1 text-xs text-gray-500 flex items-center gap-1">
          <Check v-if="lastSaved" class="w-3 h-3 text-green-500" />
          {{ lastSaved ? `Zuletzt gespeichert: ${lastSaved}` : 'Wird automatisch gespeichert' }}
        </div>
        <button @click="$emit('close')" class="px-6 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium">Schließen</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { X, Sparkles, Clock, TrendingUp, Wallet, Building2, User, Ban, Check } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String, initial: Object })
const emit = defineEmits(['close', 'saved'])

const motivationen = [
  'Strategischer Zukauf (Wachstum / Marktanteil)',
  'Diversifikation (neue Branche / Region)',
  'Markteintritt (neuer geografischer Markt)',
  'Buy-and-Build (Konsolidierung)',
  'Nachfolge-Investment (operativ einsteigen)',
  'Finanzinvestment (Rendite, kein operativer Einstieg)',
  'Cross-Selling-Potenziale heben',
  'Technologie / Know-how zukaufen',
]

const data = ref({
  motivation: [], motivationFrei: '',
  holdPeriod: '', maxKaufpreis: '',
  eigenkapital: '', bankFinanzierung: '', verkaeuferdarlehen: '',
  branche: '', region: '', mitarbeitergroesse: '', umsatzgroesse: '',
  gfVerbleib: '', synergien: '',
  dealBreaker: '',
  ...(props.initial || {}),
})

const lastSaved = ref('')
let saveTimer = null

function toggleMotivation(m) {
  const arr = Array.isArray(data.value.motivation) ? [...data.value.motivation] : []
  const idx = arr.indexOf(m)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(m)
  data.value.motivation = arr
  save()
}

async function save() {
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch('/target-update', { method: 'POST', data: {
        id: props.targetId,
        akquisitionsstrategieJson: JSON.stringify(data.value),
      }})
      lastSaved.value = new Date().toLocaleTimeString('de-DE')
      emit('saved', data.value)
    } catch (e) {
      console.error('save failed', e)
    }
  }, 400)
}
</script>
