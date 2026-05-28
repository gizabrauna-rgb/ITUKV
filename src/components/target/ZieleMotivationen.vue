<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4 py-8 overflow-y-auto">
    <div class="bg-white rounded-2xl p-6 w-full max-w-3xl my-auto">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-xl font-bold text-gray-900">Ziele & Motivationen für deinen Verkauf</h3>
          <p class="text-sm text-gray-500 mt-1">
            Diese Infos helfen Jenny, die passende Deal-Struktur und den richtigen Käufer für dich zu finden.
            Wird automatisch gespeichert.
          </p>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <X class="w-5 h-5" />
        </button>
      </div>

      <div class="space-y-6">
        <!-- Persönliche Motivation -->
        <section>
          <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Sparkles class="w-4 h-4 text-[#0088ba]" />
            Warum willst du verkaufen?
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

        <!-- Zeitrahmen + Verkaufserlös -->
        <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Clock class="w-4 h-4 text-[#0088ba]" /> Zeitrahmen
            </h4>
            <select v-model="data.zeitrahmen" @change="save" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
              <option value="">— Bitte wählen —</option>
              <option>So schnell wie möglich</option>
              <option>6–12 Monate</option>
              <option>1–2 Jahre</option>
              <option>2+ Jahre</option>
              <option>Noch unklar</option>
            </select>
          </div>
          <div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <TrendingUp class="w-4 h-4 text-[#0088ba]" /> Wunsch-Verkaufserlös
            </h4>
            <input v-model="data.wunschErloes" @blur="save" placeholder="z.B. 2 Mio. € oder Spanne 1,5 – 2,5 Mio. €"
              class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm" />
          </div>
        </section>

        <!-- Rolle nach Verkauf -->
        <section>
          <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <User class="w-4 h-4 text-[#0088ba]" />
            Deine Rolle nach der Transaktion
          </h4>
          <div class="space-y-3">
            <div>
              <label class="text-xs text-gray-600">Wie lange möchtest du noch an Bord bleiben?</label>
              <select v-model="data.bleibedauer" @change="save" class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
                <option value="">— Bitte wählen —</option>
                <option>Übergabe 3–6 Monate, dann raus</option>
                <option>1 Jahr Übergangsphase</option>
                <option>2–3 Jahre als angestellter GF</option>
                <option>5+ Jahre, langfristig dabei</option>
                <option>Noch flexibel / je nach Käufer</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-gray-600">Was wäre deine Wunsch-Rolle?</label>
              <textarea v-model="data.wunschrolle" @blur="save" rows="2"
                placeholder="z.B. Strategischer Berater, Vertriebsverantwortlicher, ganz raus, neue Rolle in einer Gruppe …"
                class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm resize-none"></textarea>
            </div>
            <div>
              <label class="text-xs text-gray-600">Was machst du aktuell gerne im Unternehmen – was würdest du gerne weiter machen?</label>
              <textarea v-model="data.aufgabenGerne" @blur="save" rows="2"
                class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm resize-none"></textarea>
            </div>
          </div>
        </section>

        <!-- Mitarbeiter + Standort -->
        <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Users class="w-4 h-4 text-[#0088ba]" /> Mitarbeiter
            </h4>
            <select v-model="data.mitarbeiterWunsch" @change="save" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
              <option value="">— Bitte wählen —</option>
              <option>Alle Mitarbeiter sollen behalten werden</option>
              <option>Schlüsselpersonal sichern</option>
              <option>Keine besondere Vorgabe</option>
            </select>
          </div>
          <div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Building2 class="w-4 h-4 text-[#0088ba]" /> Standort
            </h4>
            <select v-model="data.standortWunsch" @change="save" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
              <option value="">— Bitte wählen —</option>
              <option>Standort muss erhalten bleiben</option>
              <option>Verlegung okay, falls Mitarbeiter mitziehen</option>
              <option>Keine besondere Vorgabe</option>
            </select>
          </div>
        </section>

        <!-- Deal-Struktur Präferenzen -->
        <section>
          <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <FileText class="w-4 h-4 text-[#0088ba]" />
            Deal-Struktur
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label class="text-xs text-gray-600">Earn-Out denkbar?</label>
              <select v-model="data.earnOut" @change="save" class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
                <option value="">—</option><option>Ja</option><option>Nur teilweise</option><option>Nein</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-gray-600">Verkäuferdarlehen?</label>
              <select v-model="data.verkaeuferdarlehen" @change="save" class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
                <option value="">—</option><option>Ja</option><option>Vielleicht</option><option>Nein</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-gray-600">Wunsch-Käufer-Typ</label>
              <select v-model="data.kaeuferTyp" @change="save" class="mt-1 w-full px-3 py-2 border border-gray-200 rounded-xl text-sm">
                <option value="">—</option>
                <option>Strategischer Investor</option>
                <option>Finanzinvestor / PE</option>
                <option>Nachfolger aus Branche</option>
                <option>Mitarbeiter / MBI</option>
                <option>Egal, Hauptsache passend</option>
              </select>
            </div>
          </div>
        </section>

        <!-- Deal-Breaker -->
        <section>
          <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <Ban class="w-4 h-4 text-red-500" />
            Was sind absolute Deal-Breaker für dich?
          </h4>
          <textarea v-model="data.dealBreaker" @blur="save" rows="3"
            placeholder="z.B. „Standort darf nicht verlagert werden", „Kein Verkauf an Konkurrent X", „Marke muss erhalten bleiben"…"
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
import { ref, onMounted } from 'vue'
import { X, Sparkles, Clock, TrendingUp, User, Users, Building2, FileText, Ban, Check } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String, initial: Object })
const emit = defineEmits(['close', 'saved'])

const motivationen = [
  'Ruhestand / Altersgründe',
  'Neue berufliche Projekte starten',
  'Gesundheitliche Gründe',
  'Strategischer Wechsel (Branche/Region)',
  'Finanzieller Exit / Liquidität',
  'Nachfolge in der Familie nicht möglich',
  'Wachstum braucht stärkeren Partner',
  'Unternehmen passt nicht mehr zur Lebenssituation',
]

const data = ref({
  motivation: [], motivationFrei: '',
  zeitrahmen: '', wunschErloes: '',
  bleibedauer: '', wunschrolle: '', aufgabenGerne: '',
  mitarbeiterWunsch: '', standortWunsch: '',
  earnOut: '', verkaeuferdarlehen: '', kaeuferTyp: '',
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
        zieleMotivationenJson: JSON.stringify(data.value),
      }})
      lastSaved.value = new Date().toLocaleTimeString('de-DE')
      emit('saved', data.value)
    } catch (e) {
      console.error('save failed', e)
    }
  }, 400)
}
</script>
