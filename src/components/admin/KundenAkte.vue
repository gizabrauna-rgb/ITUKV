<template>
  <Teleport to="body">
    <div v-if="kontakt" class="fixed inset-0 z-50 flex" @keydown.esc="$emit('close')">
      <div class="flex-1 bg-black/40" @click="$emit('close')"></div>

      <aside class="w-full max-w-3xl bg-white shadow-2xl flex flex-col h-full overflow-hidden">
        <header class="px-6 py-4 border-b border-gray-100 flex items-start justify-between gap-4">
          <div class="flex-1 min-w-0">
            <h2 class="text-xl font-bold text-gray-900 truncate">{{ kontakt.firma || '—' }}</h2>
            <p class="text-sm text-gray-500 truncate">{{ kontakt.name }}<span v-if="kontakt.ort"> · {{ kontakt.plz }} {{ kontakt.ort }}</span></p>
            <div class="flex flex-wrap gap-1 mt-2">
              <span v-if="kontakt.istKunde" class="text-[11px] px-2 py-0.5 rounded-full font-medium bg-blue-100 text-blue-700">Kunde</span>
              <span v-if="kontakt.istExKunde" class="text-[11px] px-2 py-0.5 rounded-full font-medium bg-slate-200 text-slate-700">Ex-Kunde</span>
              <span v-if="kontakt.istInvestor" class="text-[11px] px-2 py-0.5 rounded-full font-medium bg-green-100 text-green-700">
                Investor<span v-if="kontakt.investorTyp"> · {{ kontakt.investorTyp }}</span>
              </span>
              <span v-if="kontakt.istTarget" class="text-[11px] px-2 py-0.5 rounded-full font-medium bg-orange-100 text-orange-700">Target</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="showAnreichern = true" class="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700">
              <Sparkles class="w-3.5 h-3.5" /> Mit Assistent anreichern
            </button>
            <button @click="$emit('edit', kontakt)" class="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">
              <Pencil class="w-3.5 h-3.5" /> Bearbeiten
            </button>
            <button @click="$emit('close')" class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
              <X class="w-5 h-5" />
            </button>
          </div>
        </header>

        <nav class="px-6 border-b border-gray-100 flex gap-6 text-sm">
          <button v-for="t in tabs" :key="t.key" @click="tab = t.key"
            :class="['py-3 border-b-2 -mb-px flex items-center gap-2 font-medium transition-colors',
                     tab === t.key ? 'border-[#0088ba] text-[#0088ba]' : 'border-transparent text-gray-500 hover:text-gray-700']">
            <component :is="t.icon" class="w-4 h-4" />
            {{ t.label }}
            <span v-if="t.count != null" class="text-[11px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">{{ t.count }}</span>
          </button>
        </nav>

        <div class="flex-1 overflow-y-auto p-6">
          <!-- Übersicht -->
          <section v-if="tab === 'uebersicht'" class="space-y-5">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Firma</div>
                <div class="text-sm text-gray-800">{{ kontakt.firma || '—' }}</div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Geschäftsführer</div>
                <div class="text-sm text-gray-800">{{ kontakt.geschaeftsfuehrer || '—' }}</div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Ansprechpartner</div>
                <div class="text-sm text-gray-800">{{ kontakt.name || '—' }}</div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">E-Mail</div>
                <div class="text-sm space-y-0.5">
                  <a v-if="kontakt.email" :href="`mailto:${kontakt.email}`" class="text-[#0088ba] hover:underline block">{{ kontakt.email }}</a>
                  <a v-for="e in weitereEmails" :key="e.wert" :href="`mailto:${e.wert}`" class="text-[#0088ba] hover:underline block">
                    {{ e.wert }} <span v-if="e.label" class="text-[10px] text-gray-400">· {{ e.label }}</span>
                  </a>
                  <span v-if="!kontakt.email && !weitereEmails.length" class="text-gray-400">—</span>
                </div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Telefon</div>
                <div class="text-sm space-y-0.5">
                  <a v-if="kontakt.telefon" :href="`tel:${kontakt.telefon}`" class="text-[#0088ba] hover:underline block">{{ kontakt.telefon }}</a>
                  <a v-for="p in weiterePhones" :key="p.wert" :href="`tel:${p.wert}`" class="text-[#0088ba] hover:underline block">
                    {{ p.wert }} <span v-if="p.label" class="text-[10px] text-gray-400">· {{ p.label }}</span>
                  </a>
                  <span v-if="!kontakt.telefon && !weiterePhones.length" class="text-gray-400">—</span>
                </div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">PLZ / Ort</div>
                <div class="text-sm text-gray-800">{{ `${kontakt.plz || ''} ${kontakt.ort || ''}`.trim() || '—' }}</div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Branche</div>
                <div class="text-sm text-gray-800">{{ kontakt.branche || '—' }}</div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Mitarbeiter</div>
                <div class="text-sm text-gray-800">{{ kontakt.mitarbeiter || '—' }}</div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Umsatz (TEUR)</div>
                <div class="text-sm text-gray-800">{{ kontakt.umsatzTeur || '—' }}</div>
              </div>
              <div v-if="kontakt.ebitMarge">
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">EBIT-Marge</div>
                <div class="text-sm text-gray-800">{{ kontakt.ebitMarge }} %</div>
              </div>
              <div v-if="kontakt.recurringPct">
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Wiederkehrende Umsätze</div>
                <div class="text-sm text-gray-800">{{ kontakt.recurringPct }} %</div>
              </div>
              <div class="col-span-2" v-if="kontakt.sucht">
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Sucht</div>
                <div class="text-sm text-gray-800">{{ kontakt.sucht }}</div>
              </div>
              <div class="col-span-2" v-if="kontakt.bietet">
                <div class="text-[11px] uppercase tracking-wide text-gray-400 font-semibold mb-0.5">Bietet</div>
                <div class="text-sm text-gray-800">{{ kontakt.bietet }}</div>
              </div>
            </div>
            <div v-if="weitereAnsprechpartner.length" class="border border-gray-100 rounded-xl p-4">
              <div class="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3">Weitere Ansprechpartner</div>
              <ul class="space-y-2">
                <li v-for="(a, i) in weitereAnsprechpartner" :key="i" class="flex items-start gap-3 text-sm">
                  <div class="w-8 h-8 rounded-full bg-[#0088ba]/10 text-[#0088ba] flex items-center justify-center text-xs font-semibold flex-shrink-0">
                    {{ (a.name || '?').slice(0, 1).toUpperCase() }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-gray-800">{{ a.name || '—' }}<span v-if="a.position" class="text-xs text-gray-500 font-normal"> · {{ a.position }}</span></div>
                    <div class="text-xs text-gray-500 flex flex-wrap gap-x-3">
                      <a v-if="a.email" :href="`mailto:${a.email}`" class="text-[#0088ba] hover:underline">{{ a.email }}</a>
                      <a v-if="a.telefon" :href="`tel:${a.telefon}`" class="text-[#0088ba] hover:underline">{{ a.telefon }}</a>
                    </div>
                  </div>
                </li>
              </ul>
            </div>

            <div v-if="kontakt.kommentar" class="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm">
              <div class="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">Notiz</div>
              <p class="text-amber-900 whitespace-pre-line">{{ kontakt.kommentar }}</p>
            </div>
          </section>

          <!-- Produkte -->
          <section v-else-if="tab === 'produkte'" class="space-y-4">
            <p class="text-xs text-gray-500">Welche mibeca-Produkte dieser Kontakt bereits gekauft hat.</p>
            <div class="grid grid-cols-2 gap-3">
              <div v-for="p in produktListe" :key="p.key"
                :class="['flex items-center gap-3 p-3 rounded-xl border',
                         kontakt[p.key] ? 'border-emerald-200 bg-emerald-50' : 'border-gray-100 bg-gray-50']">
                <div :class="['w-9 h-9 rounded-lg flex items-center justify-center font-bold text-white text-xs flex-shrink-0', p.color]">
                  {{ p.label }}
                </div>
                <div class="flex-1 min-w-0">
                  <div :class="['text-sm font-medium', kontakt[p.key] ? 'text-emerald-900' : 'text-gray-500']">
                    {{ p.full }}
                  </div>
                  <div class="text-xs" :class="kontakt[p.key] ? 'text-emerald-700' : 'text-gray-400'">
                    {{ kontakt[p.key] ? 'Gekauft' : 'Nicht gekauft' }}
                  </div>
                </div>
                <CheckCircle2 v-if="kontakt[p.key]" class="w-5 h-5 text-emerald-600 flex-shrink-0" />
              </div>
            </div>
            <div class="text-xs text-gray-400 pt-2 border-t border-gray-100">
              {{ produkteGekauft }} von {{ produktListe.length }} Produkten gekauft
            </div>
          </section>

          <!-- Verknüpfte Projekte -->
          <section v-else-if="tab === 'projekte'">
            <div v-if="verknuepfteProjekte.length === 0" class="text-center py-12 text-gray-400 text-sm">
              <Briefcase class="w-10 h-10 mx-auto mb-2 text-gray-300" />
              Keine Projekte verknüpft.
              <div class="text-xs mt-1">Projekte werden über Firma oder E-Mail-Adresse zugeordnet.</div>
            </div>
            <ul v-else class="space-y-2">
              <li v-for="p in verknuepfteProjekte" :key="p.RowKey"
                @click="$emit('open-projekt', p)"
                class="flex items-center gap-3 p-3 rounded-xl border border-gray-100 hover:border-[#0088ba]/40 hover:bg-[#0088ba]/5 cursor-pointer transition-colors">
                <span class="font-mono text-xs bg-blue-50 text-blue-800 px-2 py-0.5 rounded">{{ p.mbNr }}</span>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-gray-800 truncate">{{ p.firma || p.verkaueferName }}</div>
                  <div class="text-xs text-gray-500 truncate">{{ p.projekttyp }}<span v-if="p.region"> · {{ p.region }}</span></div>
                </div>
                <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', statusBadge(p.status)]">{{ statusLabel(p.status) }}</span>
              </li>
            </ul>
          </section>

          <!-- Verlauf (alle Projekte zusammen) -->
          <section v-else-if="tab === 'verlauf'">
            <!-- Neuer Eintrag -->
            <div v-if="verknuepfteProjekte.length" class="border border-gray-100 rounded-xl p-4 mb-5 bg-gray-50">
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-xs font-semibold text-gray-700 uppercase tracking-wide">Neuer Verlauf-Eintrag</h4>
                <select v-if="verknuepfteProjekte.length > 1" v-model="verlaufTargetId"
                  class="text-xs border border-gray-200 rounded-lg px-2 py-1">
                  <option v-for="p in verknuepfteProjekte" :key="p.RowKey" :value="p.RowKey">
                    {{ p.mbNr || '—' }} · {{ p.firma || p.verkaueferName }}
                  </option>
                </select>
                <span v-else-if="verknuepfteProjekte[0]" class="text-[11px] text-gray-500">
                  zu {{ verknuepfteProjekte[0].mbNr }}
                </span>
              </div>
              <input v-model="verlaufBetreff" placeholder="Betreff (optional)"
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 mb-2" />
              <textarea v-model="verlaufBody" rows="3" placeholder="Notiz oder Nachricht…"
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 resize-none mb-2"></textarea>
              <div class="flex items-center justify-between">
                <label class="flex items-center gap-1.5 text-[11px] text-gray-600 cursor-pointer">
                  <input type="checkbox" v-model="verlaufNotifyMandant" />
                  <span>Mandant per Mail informieren</span>
                </label>
                <button @click="addVerlauf" :disabled="!verlaufBody.trim() || savingVerlauf"
                  class="px-4 py-1.5 bg-[#0088ba] text-white rounded-lg text-xs font-medium hover:bg-[#00a0d8] disabled:opacity-50">
                  {{ savingVerlauf ? 'Speichere…' : 'Hinzufügen' }}
                </button>
              </div>
            </div>

            <!-- Filter-Buttons (wie im Target-Verlauf) -->
            <div class="flex flex-wrap gap-1.5 mb-4">
              <button @click="verlaufFilterTyp = ''"
                :class="['text-xs px-3 py-1.5 rounded-lg border', !verlaufFilterTyp ? 'bg-gray-700 text-white border-gray-700' : 'bg-white border-gray-200 hover:bg-gray-50']">
                Alle <span class="ml-1 opacity-70">{{ verlaufAlle.length }}</span>
              </button>
              <button v-for="f in verlaufFilters" :key="f.value"
                @click="verlaufFilterTyp = verlaufFilterTyp === f.value ? '' : f.value"
                :class="['text-xs px-3 py-1.5 rounded-lg border flex items-center gap-1.5', verlaufFilterTyp === f.value ? 'bg-[#0088ba] text-white border-[#0088ba]' : 'bg-white border-gray-200 hover:bg-gray-50']">
                {{ f.label }}
                <span :class="['text-[10px] px-1 rounded', verlaufFilterTyp === f.value ? 'bg-white/20' : 'bg-gray-100']">{{ countVerlaufTyp(f.value) }}</span>
              </button>
            </div>

            <div v-if="verlaufItems.length === 0" class="text-center py-12 text-gray-400 text-sm">
              <Mail class="w-10 h-10 mx-auto mb-2 text-gray-300" />
              <span v-if="verlaufFilterTyp">Keine Einträge in dieser Kategorie.</span>
              <span v-else>Kein Kommunikations-Verlauf.</span>
            </div>
            <ol v-else class="relative border-l-2 border-gray-100 ml-2 space-y-4">
              <li v-for="(e, i) in verlaufItems" :key="i" class="pl-4 relative">
                <span :class="['absolute -left-[7px] top-1.5 w-3 h-3 rounded-full border-2 border-white', verlaufDotColor(e.typ)]"></span>
                <div class="flex items-center gap-2 text-xs text-gray-500 flex-wrap">
                  <span :class="['px-2 py-0.5 rounded-full font-medium', verlaufBadge(e.typ)]">{{ verlaufLabel(e.typ) }}</span>
                  <span v-if="e._mbNr" class="font-mono text-[10px] bg-blue-50 text-blue-800 px-1.5 py-0.5 rounded">{{ e._mbNr }}</span>
                  <span v-else-if="e.kontextMbNr" class="font-mono text-[10px] bg-blue-50 text-blue-800 px-1.5 py-0.5 rounded">{{ e.kontextMbNr }}</span>
                  <span>·</span>
                  <span>{{ formatDate(e.datum) }}</span>
                  <span v-if="e.autor">· {{ e.autor }}</span>
                </div>
                <div v-if="e.betreff" class="font-semibold text-sm text-gray-900 mt-1">{{ e.betreff }}</div>
                <p v-if="e.beschreibung" class="text-sm text-gray-700 mt-1 whitespace-pre-line line-clamp-6">{{ e.beschreibung }}</p>
              </li>
            </ol>
          </section>

          <!-- Dokumente (aller verknuepften Projekte) -->
          <section v-else-if="tab === 'dokumente'">
            <div v-if="dokumenteLoading" class="text-center py-12 text-gray-400 text-sm">Lade Dokumente…</div>
            <div v-else-if="dokumenteGruppen.length === 0" class="text-center py-12 text-gray-400 text-sm">
              <FileText class="w-10 h-10 mx-auto mb-2 text-gray-300" />
              Keine Dokumente in verknüpften Projekten.
            </div>
            <div v-else class="space-y-5">
              <div v-for="g in dokumenteGruppen" :key="g.target.RowKey">
                <div class="flex items-center gap-2 mb-2">
                  <span class="font-mono text-xs bg-blue-50 text-blue-800 px-2 py-0.5 rounded">{{ g.target.mbNr }}</span>
                  <span class="text-sm font-medium text-gray-700">{{ g.target.firma || g.target.verkaueferName }}</span>
                  <span class="text-xs text-gray-400">· {{ g.dateien.length }} Datei{{ g.dateien.length === 1 ? '' : 'en' }}</span>
                </div>
                <ul class="space-y-1.5">
                  <li v-for="d in g.dateien" :key="d.RowKey"
                    class="flex items-center gap-2 p-2 rounded-lg border border-gray-100 hover:border-[#0088ba]/40 hover:bg-[#0088ba]/5 text-sm">
                    <FileText class="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <span class="flex-1 truncate">{{ d.name }}</span>
                    <span class="text-[11px] text-gray-400 capitalize">{{ d.ordner }}</span>
                    <span class="text-[11px] text-gray-400">{{ formatDate(d.uploadedAt) }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          <!-- Notizen-Timeline -->
          <section v-else-if="tab === 'notizen'" class="space-y-4">
            <div class="flex gap-2">
              <textarea v-model="newNote" rows="2" placeholder="Neue Notiz hinzufügen…"
                class="flex-1 px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 resize-none"></textarea>
              <button @click="addNote" :disabled="!newNote.trim() || savingNote"
                class="px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8] disabled:opacity-50 self-start">
                {{ savingNote ? '…' : 'Speichern' }}
              </button>
            </div>

            <div v-if="notizen.length === 0" class="text-center py-8 text-gray-400 text-sm">
              <StickyNote class="w-10 h-10 mx-auto mb-2 text-gray-300" />
              Noch keine Notizen.
            </div>
            <ol v-else class="relative border-l-2 border-gray-100 ml-2 space-y-4">
              <li v-for="(n, i) in notizen" :key="i" class="pl-4 relative">
                <span class="absolute -left-[7px] top-1.5 w-3 h-3 rounded-full bg-[#0088ba] border-2 border-white"></span>
                <div class="flex items-center gap-2 text-xs text-gray-500">
                  <span class="font-medium text-gray-700">{{ n.autor || 'mibeca' }}</span>
                  <span>·</span>
                  <span>{{ formatDate(n.datum) }}</span>
                </div>
                <p class="text-sm text-gray-800 mt-1 whitespace-pre-line">{{ n.text }}</p>
              </li>
            </ol>
          </section>
        </div>
      </aside>
    </div>
    <KontaktAnreichernModal v-if="showAnreichern && kontakt" :kontakt="kontakt"
      @close="showAnreichern = false" @updated="onAnreicherungUebernommen" />
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { X, Pencil, CheckCircle2, Briefcase, StickyNote, FileText, Package, ScrollText, Mail, History, Sparkles } from '@lucide/vue'
import { updateKontakt } from '../../api.js'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'
import KontaktAnreichernModal from './KontaktAnreichernModal.vue'

const props = defineProps({
  kontakt: { type: Object, default: null },
  targets: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'edit', 'open-projekt', 'updated'])

const tab = ref('uebersicht')
const newNote = ref('')
const savingNote = ref(false)
const showAnreichern = ref(false)
function onAnreicherungUebernommen(payload) {
  // Lokale Kontakt-Daten patchen, damit sofort sichtbar
  if (props.kontakt) {
    for (const k of Object.keys(payload || {})) {
      props.kontakt[k] = payload[k]
    }
  }
  toast.success('Kontakt aktualisiert')
  emit('updated', props.kontakt)
}
// Neuer Verlauf-Eintrag
const verlaufTargetId = ref('')
const verlaufBetreff = ref('')
const verlaufBody = ref('')
const verlaufNotifyMandant = ref(true)
const savingVerlauf = ref(false)

const dokumenteLoading = ref(false)
const dokumenteGruppen = ref([])

watch(() => props.kontakt?.RowKey, () => { tab.value = 'uebersicht'; newNote.value = ''; dokumenteGruppen.value = [] })

watch(tab, async (t) => {
  if (t === 'dokumente' && dokumenteGruppen.value.length === 0 && verknuepfteProjekte.value.length > 0) {
    dokumenteLoading.value = true
    try {
      const results = []
      for (const p of verknuepfteProjekte.value) {
        try {
          const list = await authFetch('/dokument-list', { method: 'POST', data: { targetId: p.RowKey } })
          const arr = Array.isArray(list) ? list : (list?.items || [])
          if (arr.length) results.push({ target: p, dateien: arr })
        } catch (e) { console.error('dokument-list', p.mbNr, e) }
      }
      dokumenteGruppen.value = results
    } finally { dokumenteLoading.value = false }
  }
})

const produktListe = [
  { key: 'hatUC', label: 'UC', full: 'Unternehmer-Coaching', color: 'bg-red-500' },
  { key: 'hatUCS', label: 'UCS', full: 'UC für Senior-Berater', color: 'bg-purple-500' },
  { key: 'hatMC', label: 'MC', full: 'Mitarbeiter-Coaching', color: 'bg-yellow-500' },
  { key: 'hatFKE', label: 'FKE', full: 'Führungskräfte-Entwicklung', color: 'bg-amber-600' },
  { key: 'hatUVE', label: 'UVE', full: 'Unternehmensverkaufs-Expertise', color: 'bg-pink-500' },
  { key: 'hatVME', label: 'VME', full: 'Verkaufs-Marketing-Expertise', color: 'bg-stone-600' },
  { key: 'hatKIwerkOne', label: 'KIwerk', full: 'KIwerk.one', color: 'bg-emerald-500' },
  { key: 'hatMSQ', label: 'MSQ', full: 'Mitarbeiter-Status-Quo', color: 'bg-indigo-500' },
  { key: 'hatKMQ', label: 'KMQ', full: 'Kunden-Mitarbeiter-Quote', color: 'bg-cyan-600' },
  { key: 'hatKIT', label: 'KIT', full: 'KI-Tool', color: 'bg-fuchsia-500' },
]

const produkteGekauft = computed(() => produktListe.filter(p => props.kontakt?.[p.key]).length)

const weitereEmails = computed(() => {
  try {
    const a = JSON.parse(props.kontakt?.weitereEmailsJson || '[]')
    return Array.isArray(a) ? a.filter(x => x && x.wert) : []
  } catch { return [] }
})
const weiterePhones = computed(() => {
  try {
    const a = JSON.parse(props.kontakt?.weiterePhonesJson || '[]')
    return Array.isArray(a) ? a.filter(x => x && x.wert) : []
  } catch { return [] }
})

const weitereAnsprechpartner = computed(() => {
  try {
    const a = JSON.parse(props.kontakt?.ansprechpartnerJson || '[]')
    return Array.isArray(a) ? a.filter(x => x.name || x.email || x.telefon) : []
  } catch { return [] }
})

const verknuepfteProjekte = computed(() => {
  if (!props.kontakt) return []
  const email = (props.kontakt.email || '').toLowerCase().trim()
  const firma = (props.kontakt.firma || '').toLowerCase().trim()
  return (props.targets || []).filter(t => {
    const tEmail = (t.verkaueferEmail || '').toLowerCase().trim()
    const tFirma = (t.firma || '').toLowerCase().trim()
    return (email && tEmail === email) || (firma && tFirma === firma)
  })
})

const notizen = computed(() => {
  try {
    const raw = props.kontakt?.notizenJson
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? [...arr].sort((a, b) => (b.datum || '').localeCompare(a.datum || '')) : []
  } catch { return [] }
})

const verlaufAlle = computed(() => {
  const all = []
  // 1) Kontakt-eigener Verlauf (Mass-Mails, Inbound-Antworten, manuelle Eintraege)
  if (props.kontakt?.verlaufJson) {
    try {
      const arr = JSON.parse(props.kontakt.verlaufJson)
      if (Array.isArray(arr)) arr.forEach(e => all.push({ ...e, _quelle: 'kontakt' }))
    } catch {}
  }
  // 2) Eintraege aus verknuepften Projekt-Mandaten
  for (const p of verknuepfteProjekte.value) {
    if (!p.kommunikationJson) continue
    try {
      const arr = JSON.parse(p.kommunikationJson)
      if (Array.isArray(arr)) arr.forEach(e => all.push({ ...e, _mbNr: p.mbNr, _quelle: 'mandat' }))
    } catch {}
  }
  return all.sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
})

const verlaufFilterTyp = ref('')
const verlaufItems = computed(() => {
  if (!verlaufFilterTyp.value) return verlaufAlle.value
  return verlaufAlle.value.filter(e => e.typ === verlaufFilterTyp.value)
})

const verlaufFilters = [
  { value: 'mail_in',    label: 'E-Mail eingegangen' },
  { value: 'mail_out',   label: 'E-Mail versendet' },
  { value: 'chat_in',    label: 'Chat eingegangen' },
  { value: 'chat_out',   label: 'Chat gesendet' },
  { value: 'telefon',    label: 'Telefonat' },
  { value: 'termin',     label: 'Termin' },
  { value: 'notiz',      label: 'Notiz' },
  { value: 'ki_analyse', label: 'Assistent' },
  { value: 'wichtig',    label: 'Wichtig' },
]
function countVerlaufTyp(t) {
  return verlaufAlle.value.filter(e => e.typ === t).length
}

const tabs = computed(() => [
  { key: 'uebersicht', label: 'Übersicht', icon: FileText },
  { key: 'produkte', label: 'Produkte', icon: Package, count: produkteGekauft.value },
  { key: 'projekte', label: 'Projekte', icon: Briefcase, count: verknuepfteProjekte.value.length },
  { key: 'verlauf', label: 'Verlauf', icon: History, count: verlaufItems.value.length },
  { key: 'dokumente', label: 'Dokumente', icon: FileText },
  { key: 'notizen', label: 'Notizen', icon: ScrollText, count: notizen.value.length },
])

function verlaufLabel(t) {
  const map = {
    mail: 'E-Mail', mail_in: 'E-Mail eingegangen', mail_out: 'E-Mail versendet',
    chat_in: 'Chat eingegangen', chat_out: 'Chat gesendet',
    telefon: 'Telefonat', telefonat: 'Telefonat',
    termin: 'Termin', notiz: 'Notiz',
    ki_analyse: 'Assistent', wichtig: 'Wichtig',
  }
  return map[t] || (t || 'Eintrag')
}
// outgoing (mibeca) = blau, incoming (Kontakt) = orange/rot
function verlaufBadge(t) {
  if (t === 'mail_out' || t === 'chat_out') return 'bg-blue-100 text-blue-700'
  if (t === 'mail_in' || t === 'chat_in') return 'bg-orange-100 text-orange-700'
  if (t === 'telefon' || t === 'telefonat') return 'bg-green-100 text-green-700'
  if (t === 'termin') return 'bg-purple-100 text-purple-700'
  if (t === 'ki_analyse') return 'bg-purple-100 text-purple-700'
  if (t === 'wichtig') return 'bg-red-100 text-red-700'
  if (t === 'notiz') return 'bg-amber-100 text-amber-800'
  return 'bg-gray-100 text-gray-600'
}
function verlaufDotColor(t) {
  if (t === 'mail_out' || t === 'chat_out') return 'bg-blue-500'
  if (t === 'mail_in' || t === 'chat_in') return 'bg-orange-500'
  if (t === 'telefon' || t === 'telefonat') return 'bg-green-500'
  if (t === 'termin') return 'bg-purple-500'
  if (t === 'ki_analyse') return 'bg-purple-500'
  if (t === 'wichtig') return 'bg-red-500'
  if (t === 'notiz') return 'bg-amber-500'
  return 'bg-gray-400'
}

async function addVerlauf() {
  if (!verlaufBody.value.trim() || !verknuepfteProjekte.value.length) return
  const targetId = verlaufTargetId.value || verknuepfteProjekte.value[0].RowKey
  savingVerlauf.value = true
  try {
    const endpoint = verlaufNotifyMandant.value ? '/verlauf-send-mail' : '/verlauf-add'
    await authFetch(endpoint, { method: 'POST', data: {
      targetId,
      betreff: verlaufBetreff.value.trim() || 'Notiz',
      body: verlaufBody.value.trim(),
      typ: 'notiz',
    }})
    // Verlauf lokal nachladen: das Target neu holen
    try {
      const refreshed = await authFetch('/target-get', { method: 'POST', data: { id: targetId } })
      const idx = (props.targets || []).findIndex(t => t.RowKey === targetId)
      if (idx >= 0 && refreshed) {
        props.targets[idx].kommunikationJson = refreshed.kommunikationJson
      }
    } catch {}
    verlaufBetreff.value = ''
    verlaufBody.value = ''
    toast.success('Verlauf-Eintrag gespeichert')
    emit('updated', props.kontakt)
  } catch (e) {
    toast.error('Speichern fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally { savingVerlauf.value = false }
}

async function addNote() {
  if (!newNote.value.trim() || !props.kontakt) return
  savingNote.value = true
  try {
    const list = [...notizen.value]
    list.unshift({ datum: new Date().toISOString(), autor: sessionStorage.getItem('userName') || 'mibeca', text: newNote.value.trim() })
    const json = JSON.stringify(list)
    await updateKontakt(props.kontakt.RowKey, { notizenJson: json })
    props.kontakt.notizenJson = json
    newNote.value = ''
    toast.success('Notiz gespeichert')
    emit('updated', props.kontakt)
  } catch (e) {
    toast.error('Speichern fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally { savingNote.value = false }
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function statusBadge(s) {
  if (s === 'verfuegbar') return 'bg-green-100 text-green-700'
  if (s === 'in_verhandlung') return 'bg-yellow-100 text-yellow-700'
  if (s === 'verkauft') return 'bg-blue-100 text-blue-700'
  if (s === 'abgebrochen') return 'bg-gray-100 text-gray-500'
  return 'bg-gray-100 text-gray-500'
}
function statusLabel(s) {
  if (s === 'verfuegbar') return 'Verfügbar'
  if (s === 'in_verhandlung') return 'In Verhandlung'
  if (s === 'verkauft') return 'Verkauft'
  if (s === 'abgebrochen') return 'Beendet'
  return s || '—'
}
</script>
