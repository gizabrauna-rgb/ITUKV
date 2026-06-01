<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4 py-8 overflow-y-auto">
    <div class="bg-white rounded-2xl w-full max-w-3xl shadow-2xl flex flex-col max-h-[90vh]">
      <!-- Header -->
      <header class="px-5 py-4 border-b border-gray-100">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <h3 class="font-bold text-gray-900 text-lg truncate">{{ form.name || 'Neue Akquisition' }}</h3>
            <div class="flex items-center gap-2 mt-1 flex-wrap">
              <span class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                Phase {{ phase.id }} · {{ phase.label }}
              </span>
              <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', status.cls]">{{ status.label }}</span>
              <span v-if="form.quelleKandidatId" class="text-[10px] bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full">aus Vorschlag</span>
            </div>
          </div>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 flex-shrink-0">
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Tab-Leiste -->
        <div class="flex gap-1 mt-4 border-b border-gray-100 -mb-4 overflow-x-auto">
          <button v-for="t in tabs" :key="t.key" @click="activeTab = t.key"
            :class="['px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5',
              activeTab === t.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700']">
            <component :is="t.icon" class="w-3.5 h-3.5" />
            {{ t.label }}
            <span v-if="t.count" class="bg-gray-100 text-gray-600 text-[10px] rounded-full px-1.5">{{ t.count }}</span>
          </button>
        </div>
      </header>

      <!-- Body -->
      <main class="flex-1 overflow-y-auto p-5">
        <!-- Tab: Übersicht -->
        <div v-if="activeTab === 'overview'" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
              <label class="block text-xs font-medium text-gray-600 mb-1">Firma *</label>
              <input v-model="form.name" :disabled="readOnly" class="input" />
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Phase</label>
              <select v-model.number="form.phase" :disabled="readOnly" class="input">
                <option v-for="p in AKQ_PHASEN" :key="p.id" :value="p.id">{{ p.id }} · {{ p.label }}</option>
              </select>
              <p class="text-[10px] text-gray-400 mt-1">{{ phase.beschreibung }}</p>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Status</label>
              <select v-model="form.status" class="input">
                <option v-for="s in AKQ_STATUS" :key="s.key" :value="s.key">{{ s.label }}</option>
              </select>
            </div>

            <div v-if="!readOnly" class="col-span-2 bg-gray-50 border border-gray-100 rounded-lg p-3">
              <label class="block text-xs font-medium text-gray-600 mb-1">Mandat-Position <span class="text-gray-400">(intern)</span></label>
              <select v-model="form.mandatPosition" class="input">
                <option value="">— nicht gesetzt —</option>
                <option v-for="m in MANDAT_POSITION" :key="m.key" :value="m.key">{{ m.label }}</option>
              </select>
              <p v-if="mandatPositionInfo" class="text-[10px] text-gray-500 mt-1">{{ mandatPositionInfo.hinweis }}</p>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Branche</label>
              <input v-model="form.branche" :disabled="readOnly" class="input" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Region</label>
              <input v-model="form.region" :disabled="readOnly" class="input" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Mitarbeiter</label>
              <input v-model="form.mitarbeiter" :disabled="readOnly" class="input" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Umsatz</label>
              <input v-model="form.umsatz" :disabled="readOnly" class="input" />
            </div>
            <div class="col-span-2">
              <label class="block text-xs font-medium text-gray-600 mb-1">Max. Kaufpreis</label>
              <input v-model="form.maxKaufpreis" class="input" />
            </div>
          </div>
        </div>

        <!-- Tab: Aufgaben -->
        <div v-else-if="activeTab === 'aufgaben'" class="space-y-3">
          <div v-if="!form.aufgaben?.length" class="text-sm text-gray-400 text-center py-8">
            Noch keine Aufgaben. {{ readOnly ? '' : 'Füg eine hinzu oder wähle eine Phase, dann werden Vorlagen-Aufgaben automatisch angelegt.' }}
          </div>
          <ul class="space-y-1.5">
            <li v-for="(a, i) in form.aufgaben" :key="a.id"
              class="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2">
              <input type="checkbox" v-model="a.erledigt" class="rounded" />
              <div class="flex-1 min-w-0">
                <div :class="['text-sm', a.erledigt ? 'line-through text-gray-400' : 'text-gray-800']">
                  {{ a.titel }}
                </div>
                <div class="text-[10px] text-gray-500 flex gap-2 items-center">
                  <span v-if="a.verantwortlich" :class="a.verantwortlich === 'mibeca' ? 'text-blue-600' : (a.verantwortlich === 'käufer' ? 'text-orange-600' : 'text-gray-500')">
                    {{ a.verantwortlich }}
                  </span>
                  <input v-if="!readOnly || a.verantwortlich === 'käufer'" type="date" v-model="a.faellig"
                    class="text-[10px] border-0 bg-transparent p-0 focus:outline-none" />
                </div>
              </div>
              <button @click="form.aufgaben.splice(i, 1)" class="text-gray-300 hover:text-red-500">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </li>
          </ul>
          <div class="flex gap-2 pt-2">
            <input v-model="neueAufgabe" @keydown.enter="addAufgabe" placeholder="Neue Aufgabe…" class="input flex-1" />
            <button @click="addAufgabe" :disabled="!neueAufgabe.trim()" class="px-3 py-2 bg-blue-600 text-white rounded-xl text-xs font-medium hover:bg-blue-700 disabled:opacity-50">
              <Plus class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Tab: Notizen -->
        <div v-else-if="activeTab === 'notizen'" class="space-y-4">
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Käufer-Notizen <span class="text-gray-400">(sichtbar für mibeca + Käufer)</span></label>
            <textarea v-model="form.notizenKaeufer" rows="5" class="input resize-y" placeholder="Eigene Anmerkungen, Fragen, Erinnerungen …"></textarea>
          </div>
          <div v-if="!readOnly">
            <label class="block text-xs font-medium text-gray-600 mb-1">Interne Notizen <span class="text-gray-400">(nur mibeca)</span></label>
            <textarea v-model="form.notizen" rows="5" class="input resize-y bg-amber-50/40" placeholder="Interne Bewertung, Hintergrund, nicht für Käufer sichtbar …"></textarea>
          </div>
        </div>

        <!-- Tab: Verlauf -->
        <div v-else-if="activeTab === 'verlauf'" class="space-y-3">
          <div v-if="!form.verlauf?.length" class="text-center py-8 text-sm text-gray-400">
            <MessageSquare class="w-8 h-8 mx-auto mb-2 text-gray-200" />
            Noch keine Einträge. Schreib unten eine Notiz oder Frage.
          </div>
          <ul v-else class="space-y-2">
            <li v-for="v in verlaufSortiert" :key="v.id"
              :class="['rounded-xl px-3 py-2 text-sm', v.system ? 'bg-gray-50 border border-gray-100 text-gray-600 italic' : (v.autorRolle === 'admin' ? 'bg-blue-50 border border-blue-100' : 'bg-orange-50 border border-orange-100')]">
              <div class="flex items-center justify-between gap-2 mb-1">
                <span class="text-[10px] font-semibold uppercase tracking-wide">
                  {{ v.system ? 'System' : (v.autor || '—') }}
                </span>
                <span class="text-[10px] text-gray-400">{{ formatDatum(v.datum) }}</span>
              </div>
              <div class="whitespace-pre-wrap">{{ v.text }}</div>
            </li>
          </ul>
          <div class="flex gap-2 pt-2 border-t border-gray-100">
            <textarea v-model="neuerVerlaufText" rows="2" placeholder="Neue Notiz / Nachricht …"
              class="input flex-1 resize-none" @keydown.ctrl.enter="addVerlauf" @keydown.meta.enter="addVerlauf"></textarea>
            <button @click="addVerlauf" :disabled="!neuerVerlaufText.trim()"
              class="px-3 py-2 bg-blue-600 text-white rounded-xl text-xs font-medium hover:bg-blue-700 disabled:opacity-50 self-stretch">
              <Send class="w-4 h-4" />
            </button>
          </div>
          <p class="text-[10px] text-gray-400">Ctrl/Cmd + Enter zum Senden.</p>
        </div>

        <!-- Tab: Termine -->
        <div v-else-if="activeTab === 'termine'" class="text-center py-12 text-sm text-gray-400">
          <Calendar class="w-10 h-10 mx-auto mb-2 text-gray-200" />
          Termin-Verwaltung folgt im nächsten Update.
        </div>

        <!-- Tab: Dokumente -->
        <div v-else-if="activeTab === 'dokumente'" class="text-center py-12 text-sm text-gray-400">
          <FolderOpen class="w-10 h-10 mx-auto mb-2 text-gray-200" />
          Dokumente pro Akquisition folgen im nächsten Update.<br/>
          Bis dahin: gemeinsame Ablage im Dokumente-Tab.
        </div>
      </main>

      <!-- Footer -->
      <footer class="px-5 py-3 border-t border-gray-100 flex items-center justify-end gap-2">
        <button @click="$emit('close')" class="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">Abbrechen</button>
        <button @click="emitSave" :disabled="!form.name?.trim()"
          class="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          Speichern
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { X, Plus, Trash2, FileText, ListTodo, MessageSquare, Calendar, FolderOpen, StickyNote, Send } from '@lucide/vue'
import { AKQ_PHASEN, AKQ_STATUS, MANDAT_POSITION, phaseInfo, statusInfo, defaultAufgabenFuerPhase } from '../../data/akquisitionsPhasen.js'

const props = defineProps({
  modelValue: { type: Object, required: true },
  readOnly: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'save'])

const userName = sessionStorage.getItem('userName') || ''
const userRole = sessionStorage.getItem('userRole') || 'target'
const isAdmin = userRole === 'admin'

// Snapshot der Ausgangswerte fuer Auto-Verlauf-Eintraege beim Speichern
const initialSnapshot = {
  phase: props.modelValue.phase || 1,
  status: props.modelValue.status || 'laufend',
}

const form = ref(initForm(props.modelValue))
const activeTab = ref('overview')
const neueAufgabe = ref('')
const neuerVerlaufText = ref('')

function initForm(akq) {
  return {
    id: akq.id,
    createdAt: akq.createdAt,
    name: akq.name || '',
    phase: akq.phase || 1,
    status: akq.status || 'laufend',
    mandatPosition: akq.mandatPosition || '',
    branche: akq.branche || '',
    region: akq.region || '',
    mitarbeiter: akq.mitarbeiter || '',
    umsatz: akq.umsatz || '',
    maxKaufpreis: akq.maxKaufpreis || '',
    quelleKandidatId: akq.quelleKandidatId || '',
    verkaeuferTargetId: akq.verkaeuferTargetId || '',
    notizenKaeufer: akq.notizenKaeufer || '',
    notizen: akq.notizen || '',
    aufgaben: Array.isArray(akq.aufgaben) ? akq.aufgaben.map(a => ({ ...a })) : [],
    verlauf: Array.isArray(akq.verlauf) ? akq.verlauf.map(v => ({ ...v })) : [],
  }
}

const phase = computed(() => phaseInfo(form.value.phase))
const status = computed(() => statusInfo(form.value.status))
const mandatPositionInfo = computed(() => MANDAT_POSITION.find(m => m.key === form.value.mandatPosition))

const tabs = computed(() => [
  { key: 'overview',  label: 'Übersicht', icon: FileText },
  { key: 'aufgaben',  label: 'Aufgaben',  icon: ListTodo, count: form.value.aufgaben.filter(a => !a.erledigt).length || null },
  { key: 'verlauf',   label: 'Verlauf',   icon: MessageSquare, count: form.value.verlauf.length || null },
  { key: 'termine',   label: 'Termine',   icon: Calendar },
  { key: 'dokumente', label: 'Dokumente', icon: FolderOpen },
  { key: 'notizen',   label: 'Notizen',   icon: StickyNote },
])

const verlaufSortiert = computed(() => {
  return [...form.value.verlauf].sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
})

function formatDatum(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) }
  catch { return iso }
}

function addVerlauf() {
  const text = neuerVerlaufText.value.trim()
  if (!text) return
  form.value.verlauf.push({
    id: 'v' + Date.now(),
    datum: new Date().toISOString(),
    autor: userName || (isAdmin ? 'mibeca' : 'Käufer'),
    autorRolle: isAdmin ? 'admin' : 'kaeufer',
    text,
  })
  neuerVerlaufText.value = ''
}

// Wenn Phase wechselt → Default-Aufgaben automatisch ergänzen (idempotent via templateKey)
let lastPhase = form.value.phase
watch(() => form.value.phase, (neu) => {
  if (neu === lastPhase) return
  const neue = defaultAufgabenFuerPhase(neu, form.value.aufgaben)
  if (neue.length) form.value.aufgaben.push(...neue)
  lastPhase = neu
})

function addAufgabe() {
  const t = neueAufgabe.value.trim()
  if (!t) return
  form.value.aufgaben.push({
    id: 'auf' + Date.now(),
    titel: t,
    verantwortlich: '',
    erledigt: false,
    faellig: '',
    createdAt: new Date().toISOString(),
  })
  neueAufgabe.value = ''
}

function emitSave() {
  // Auto-Verlauf-Eintraege bei Phase-/Status-Wechsel
  const autoEntries = []
  if (form.value.phase !== initialSnapshot.phase) {
    const altInfo = phaseInfo(initialSnapshot.phase)
    const neuInfo = phaseInfo(form.value.phase)
    autoEntries.push({
      id: 'v' + Date.now(),
      datum: new Date().toISOString(),
      autor: userName || (isAdmin ? 'mibeca' : 'Käufer'),
      autorRolle: isAdmin ? 'admin' : 'kaeufer',
      system: true,
      text: `Phase gewechselt: ${altInfo.id} · ${altInfo.label} → ${neuInfo.id} · ${neuInfo.label}`,
    })
  }
  if (form.value.status !== initialSnapshot.status) {
    autoEntries.push({
      id: 'v' + (Date.now() + 1),
      datum: new Date().toISOString(),
      autor: userName || (isAdmin ? 'mibeca' : 'Käufer'),
      autorRolle: isAdmin ? 'admin' : 'kaeufer',
      system: true,
      text: `Status: ${initialSnapshot.status} → ${form.value.status}`,
    })
  }
  if (autoEntries.length) form.value.verlauf.push(...autoEntries)
  emit('save', { ...form.value })
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-gray-50 disabled:text-gray-500; }
</style>
