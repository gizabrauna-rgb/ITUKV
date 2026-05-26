<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Kommunikations-Verlauf</h3>
      </div>
      <div class="flex items-center gap-2">
        <button @click="openMail" class="flex items-center gap-2 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8]">
          <Mail class="w-4 h-4" /> E-Mail senden
        </button>
        <button @click="openNew" class="flex items-center gap-2 px-3 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50">
          <Plus class="w-4 h-4" /> Notiz
        </button>
      </div>

      <!-- Mail-Dialog -->
      <div v-if="showMailModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4" @click.self="showMailModal = false">
        <div class="bg-white rounded-2xl w-full max-w-lg p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-gray-900 flex items-center gap-2"><Mail class="w-5 h-5 text-[#0088ba]" /> E-Mail senden</h3>
            <button @click="showMailModal = false"><X class="w-5 h-5 text-gray-400" /></button>
          </div>
          <p class="text-xs text-gray-500 mb-3">Geht direkt an den Empfänger – Antworten erscheinen automatisch hier im Verlauf.</p>
          <div class="space-y-3">
            <div v-if="vorlagen.length">
              <label class="text-xs font-medium text-gray-600 mb-1 block">Vorlage einfügen</label>
              <select @change="onVorlageChange($event)" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30">
                <option value="">— Vorlage wählen —</option>
                <optgroup v-for="kat in vorlagenKategorien" :key="kat" :label="kat">
                  <option v-for="v in vorlagen.filter(x => (x.kategorie || 'Allgemein') === kat)" :key="v.RowKey" :value="v.RowKey">{{ v.name }}</option>
                </optgroup>
              </select>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">An (E-Mail)</label>
              <input v-model="mailForm.empfaengerEmail" placeholder="z.B. kunde@example.de" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Betreff *</label>
              <input v-model="mailForm.betreff" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Nachricht *</label>
              <textarea v-model="mailForm.body" rows="8" placeholder="Hallo …" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 resize-y"></textarea>
            </div>
          </div>
          <div class="flex gap-3 mt-5">
            <button @click="showMailModal = false" class="flex-1 px-4 py-2 border border-gray-200 rounded-xl text-sm">Abbrechen</button>
            <button @click="sendMail" :disabled="!mailForm.betreff || !mailForm.body || mailSending" class="flex-1 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-semibold hover:bg-[#00a0d8] disabled:opacity-50">
              {{ mailSending ? 'Wird gesendet…' : 'E-Mail senden' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Filter -->
    <div class="flex items-center gap-2 mb-4 flex-wrap">
      <button v-for="t in typFilters" :key="t.value"
        @click="filterTyp = filterTyp === t.value ? '' : t.value"
        :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                 filterTyp === t.value ? `${t.activeClass} text-white border-transparent` : 'border-gray-200 text-gray-600 hover:bg-gray-50']">
        <component :is="t.icon" class="w-3.5 h-3.5" />
        {{ t.label }}
        <span :class="['text-[10px] px-1.5 py-0.5 rounded', filterTyp === t.value ? 'bg-white/20' : 'bg-gray-100']">{{ countByTyp(t.value) }}</span>
      </button>
    </div>

    <!-- Timeline -->
    <div v-if="loading" class="text-center text-sm text-gray-400 py-10">Lade Verlauf…</div>
    <div v-else-if="!filtered.length" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">
      <MessageSquare class="w-10 h-10 mx-auto mb-3 text-gray-200" />
      <p>Noch keine Einträge im Verlauf.</p>
      <button @click="openNew" class="text-[#0088ba] hover:underline mt-2 text-sm">Ersten Eintrag erstellen →</button>
    </div>
    <div v-else class="relative">
      <!-- Timeline-Linie -->
      <div class="absolute left-5 top-2 bottom-2 w-px bg-gray-200"></div>

      <div v-for="(entry, idx) in filtered" :key="entry.id" class="relative pl-14 pb-4">
        <!-- Icon-Kreis -->
        <div :class="['absolute left-2 top-2 w-7 h-7 rounded-full flex items-center justify-center', typBg(entry.typ)]">
          <component :is="typIcon(entry.typ)" class="w-3.5 h-3.5 text-white" />
        </div>

        <!-- Karte -->
        <div class="bg-white rounded-xl border border-gray-100 p-4 hover:border-gray-200 transition-colors">
          <div class="flex items-start justify-between mb-1">
            <div class="flex items-center gap-2 flex-wrap">
              <span :class="typBadge(entry.typ)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ typLabel(entry.typ) }}</span>
              <span class="text-xs text-gray-400">{{ formatDateTime(entry.datum) }}</span>
              <span v-if="entry.autor" class="text-xs text-gray-500">· {{ entry.autor }}</span>
            </div>
            <div class="flex gap-1">
              <button @click="openEdit(entry)" class="text-gray-300 hover:text-gray-600 p-1" title="Bearbeiten">
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button @click="deleteEntry(entry)" class="text-gray-300 hover:text-red-500 p-1" title="Löschen">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
          <div v-if="entry.betreff" class="font-semibold text-sm text-gray-900 mb-1">{{ entry.betreff }}</div>
          <p v-if="entry.beschreibung" class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{{ entry.beschreibung }}</p>
          <div v-if="entry.beteiligte" class="flex items-center gap-1.5 mt-2 text-xs text-gray-400">
            <Users class="w-3 h-3" /> {{ entry.beteiligte }}
          </div>
        </div>
      </div>
    </div>

    <!-- Modal: Neuer/Bearbeitener Eintrag -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl w-full max-w-lg p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-900">{{ editing ? 'Eintrag bearbeiten' : 'Neuer Verlauf-Eintrag' }}</h3>
          <button @click="closeModal"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Typ *</label>
              <select v-model="form.typ" class="input">
                <option v-for="t in typFilters" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Datum & Uhrzeit *</label>
              <input v-model="form.datum" type="datetime-local" class="input" />
            </div>
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Autor (wer)</label>
            <input v-model="form.autor" placeholder="z.B. Jenny, Mike, Anna…" class="input" />
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Betreff / Titel</label>
            <input v-model="form.betreff" placeholder="z.B. Telefonat mit Käufer-Kandidat" class="input" />
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Beschreibung / Notiz</label>
            <textarea v-model="form.beschreibung" rows="5" placeholder="Was wurde besprochen? Wichtige Punkte?" class="input resize-none"></textarea>
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Beteiligte Personen</label>
            <input v-model="form.beteiligte" placeholder="z.B. Verkäufer, 2 Interessenten" class="input" />
          </div>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="closeModal" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl hover:bg-gray-50">Abbrechen</button>
          <button @click="saveEntry" class="flex-1 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium">Speichern</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Mail, Phone, Calendar, MessageSquare, FileText, AlertCircle,
  Plus, Pencil, Trash2, X, Users
} from '@lucide/vue'
import { authFetch, verlaufSendMail, verlaufMarkRead, getMailvorlagen } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })

// Vorlagen
const vorlagen = ref([])
const vorlagenKategorien = computed(() => [...new Set(vorlagen.value.map(v => v.kategorie || 'Allgemein'))])
async function loadVorlagen() {
  try { vorlagen.value = await getMailvorlagen() } catch {}
}

function applyVorlage(v) {
  const target = currentTarget.value || {}
  const origin = window.location.origin
  const mbNr = target.mbNr || ''
  const vars = {
    firma: target.firma || target.verkaueferName || '',
    name: target.verkaueferName || '',
    mbNr: mbNr,
    absender: sessionStorage.getItem('userName') || 'mibeca',
    datum: new Date().toLocaleDateString('de-DE'),
    verkaueferName: target.verkaueferName || '',
    anfrageLink: mbNr ? `${origin}/${mbNr}` : '',
  }
  function sub(s) { return (s || '').replace(/\{\{(\w+)\}\}/g, (_, k) => vars[k] || '') }
  mailForm.value.betreff = sub(v.betreff)
  mailForm.value.body = sub(v.body)
}
function onVorlageChange(e) {
  const rk = e.target.value
  if (!rk) return
  const v = vorlagen.value.find(x => x.RowKey === rk)
  if (v) applyVorlage(v)
  e.target.value = ''
}

const currentTarget = ref(null)

// Mail-Dialog
const showMailModal = ref(false)
const mailSending = ref(false)
const mailForm = ref({ empfaengerEmail: '', betreff: '', body: '' })
function openMail() {
  mailForm.value = { empfaengerEmail: '', betreff: '', body: '' }
  showMailModal.value = true
}
async function sendMail() {
  mailSending.value = true
  try {
    const r = await verlaufSendMail({ targetId: props.targetId, ...mailForm.value })
    if (r?.entry) entries.value.unshift(r.entry)
    showMailModal.value = false
  } catch (e) { toast.error('E-Mail-Versand fehlgeschlagen: ' + (e?.response?.data?.error || e.message)) }
  finally { mailSending.value = false }
}

const entries = ref([])
const loading = ref(true)
const showModal = ref(false)
const editing = ref(null)
const filterTyp = ref('')

const form = ref({ typ: 'notiz', datum: '', autor: '', betreff: '', beschreibung: '', beteiligte: '' })

const typFilters = [
  { value: 'mail_in', label: 'E-Mail eingegangen', icon: Mail, activeClass: 'bg-blue-500' },
  { value: 'mail_out', label: 'E-Mail versendet', icon: Mail, activeClass: 'bg-[#0088ba]' },
  { value: 'telefon', label: 'Telefonat', icon: Phone, activeClass: 'bg-purple-500' },
  { value: 'termin', label: 'Termin', icon: Calendar, activeClass: 'bg-amber-500' },
  { value: 'notiz', label: 'Notiz', icon: FileText, activeClass: 'bg-gray-500' },
  { value: 'wichtig', label: 'Wichtig', icon: AlertCircle, activeClass: 'bg-red-500' },
]

const filtered = computed(() => {
  let r = entries.value
  if (filterTyp.value) r = r.filter(e => e.typ === filterTyp.value)
  return [...r].sort((a, b) => (a.datum < b.datum ? 1 : -1))
})

function countByTyp(t) {
  return entries.value.filter(e => e.typ === t).length
}

function typLabel(t) { return typFilters.find(f => f.value === t)?.label || t }
function typIcon(t) {
  const map = { mail_in: Mail, mail_out: Mail, telefon: Phone, termin: Calendar, notiz: FileText, wichtig: AlertCircle }
  return map[t] || FileText
}
function typBg(t) {
  const map = { mail_in: 'bg-blue-500', mail_out: 'bg-[#0088ba]', telefon: 'bg-purple-500', termin: 'bg-amber-500', notiz: 'bg-gray-500', wichtig: 'bg-red-500' }
  return map[t] || 'bg-gray-500'
}
function typBadge(t) {
  const map = {
    mail_in: 'bg-blue-50 text-blue-700',
    mail_out: 'bg-[#0088ba]/10 text-[#0088ba]',
    telefon: 'bg-purple-50 text-purple-700',
    termin: 'bg-amber-50 text-amber-700',
    notiz: 'bg-gray-100 text-gray-600',
    wichtig: 'bg-red-50 text-red-700',
  }
  return map[t] || 'bg-gray-100 text-gray-600'
}

function formatDateTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function loadEntries() {
  if (!props.targetId) return
  loading.value = true
  try {
    const target = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    currentTarget.value = target
    if (target.kommunikationJson) {
      try { entries.value = JSON.parse(target.kommunikationJson) } catch { entries.value = [] }
    } else {
      entries.value = []
    }
    // Markiert als gelesen sobald Verlauf geoeffnet wird
    try { await verlaufMarkRead(props.targetId) } catch {}
  } finally { loading.value = false }
}

onMounted(() => { loadEntries(); loadVorlagen() })

function openNew() {
  editing.value = null
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  form.value = {
    typ: 'notiz',
    datum: now.toISOString().slice(0, 16),
    autor: sessionStorage.getItem('userName') || '',
    betreff: '', beschreibung: '', beteiligte: '',
  }
  showModal.value = true
}

function openEdit(entry) {
  editing.value = entry
  form.value = { ...entry }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editing.value = null
}

async function saveAll() {
  await authFetch('/target-update', { method: 'POST', data: { id: props.targetId,  kommunikationJson: JSON.stringify(entries.value)  } })
}

async function saveEntry() {
  if (editing.value) {
    const idx = entries.value.findIndex(e => e.id === editing.value.id)
    if (idx >= 0) entries.value[idx] = { ...editing.value, ...form.value }
  } else {
    entries.value.push({
      id: 'k' + Date.now(),
      ...form.value,
    })
  }
  await saveAll()
  closeModal()
}

async function deleteEntry(entry) {
  if (!confirm('Eintrag wirklich löschen?')) return
  entries.value = entries.value.filter(e => e.id !== entry.id)
  await saveAll()
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
