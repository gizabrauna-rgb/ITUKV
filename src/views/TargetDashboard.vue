<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Topbar -->
    <header class="bg-[#161e2a] text-white px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <img src="/Logo_mibeca_Start.png" alt="mibeca" class="h-10 w-auto" />
        <div>
          <span class="font-bold text-sm">ITUKV Dashboard</span>
          <span class="text-gray-400 text-xs ml-2">Verkäufer-Portal</span>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <button @click="tab = 'verlauf'" class="relative flex items-center gap-1.5 text-xs text-gray-300 hover:text-white" :title="`${unreadTotal} ungelesene Nachrichten`">
          <Bell class="w-4 h-4" />
          <span v-if="unreadTotal > 0" class="absolute -top-1 -right-2 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[16px] h-4 px-1 flex items-center justify-center">
            {{ unreadTotal > 99 ? '99+' : unreadTotal }}
          </span>
        </button>
        <span class="text-sm text-gray-300">{{ userName }}</span>
        <button @click="$emit('logout')" class="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white">
          <LogOut class="w-4 h-4" /> Abmelden
        </button>
      </div>
    </header>

    <div class="max-w-7xl mx-auto px-6 py-8">
      <!-- Projekttyp-Label -->
      <div v-if="projekttyp" class="mb-3">
        <span class="inline-flex items-center gap-1.5 text-xs font-semibold bg-[#097e92]/10 text-[#097e92] px-2.5 py-1 rounded-full">
          <Briefcase class="w-3 h-3" />
          {{ projekttyp }}
        </span>
      </div>

      <!-- Tab Nav -->
      <div class="flex gap-1 mb-6 bg-white rounded-xl border border-gray-100 p-1 w-fit">
        <button v-for="item in visibleNavItems" :key="item.tab" @click="tab = item.tab"
          :class="['flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors', tab === item.tab ? 'bg-[#097e92] text-white' : 'text-gray-600 hover:bg-gray-50']">
          <component :is="item.icon" class="w-4 h-4" />
          {{ item.label }}
        </button>
      </div>

      <!-- Tab: Mein Projekt -->
      <div v-if="tab === 'projekt'">
        <h2 class="text-xl font-bold text-gray-900 mb-5">Mein Verkaufsprojekt</h2>

        <!-- Mandatsvertrag-Status -->
        <div v-if="vertragInfo" class="mb-4">
          <div v-if="vertragInfo.gegengezeichnetAm" class="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3">
            <CheckCircle class="w-6 h-6 text-green-600 flex-shrink-0" />
            <div class="flex-1">
              <p class="font-semibold text-green-900 text-sm">Mandatsvertrag vollständig unterschrieben</p>
              <p class="text-xs text-green-700">Gegengezeichnet am {{ formatDate(vertragInfo.gegengezeichnetAm) }} durch {{ vertragInfo.gegengezeichnetVon }}.</p>
            </div>
            <a v-if="vertragInfo.signToken" :href="`${apiBaseUrl}/sign-pdf?token=${vertragInfo.signToken}`" target="_blank" rel="noopener" class="px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf] flex items-center gap-2">
              <Download class="w-4 h-4" /> Mein Exemplar herunterladen
            </a>
          </div>
          <div v-else-if="vertragInfo.signiertAm" class="bg-yellow-50 border border-yellow-200 rounded-xl p-4 flex items-center gap-3">
            <Clock class="w-6 h-6 text-yellow-600 flex-shrink-0" />
            <div>
              <p class="font-semibold text-yellow-900 text-sm">Vertrag unterschrieben – wartet auf Gegenzeichnung durch mibeca</p>
              <p class="text-xs text-yellow-700">Sobald mibeca gegenzeichnet, bekommst du dein finales Exemplar.</p>
            </div>
          </div>
        </div>

        <!-- Master-Prozess: Aktuelle Phase -->
        <div v-if="phasen.length" class="bg-gradient-to-br from-[#097e92] to-[#0a9aaf] rounded-xl p-5 mb-4 text-white">
          <div class="text-xs uppercase tracking-wide opacity-80 mb-1">Aktuelle Phase</div>
          <div class="text-xl font-bold mb-3">Phase {{ currentPhase }} von {{ phasen.length }}: {{ currentPhaseTitle }}</div>
          <div class="w-full bg-white/20 rounded-full h-2 mb-1">
            <div class="bg-white h-2 rounded-full transition-all" :style="`width: ${phasenProgress}%`"></div>
          </div>
          <div class="text-xs opacity-90">{{ donePhasen }} von {{ phasen.length }} Phasen abgeschlossen</div>
          <button @click="showAllPhasen = !showAllPhasen" class="text-xs underline opacity-90 hover:opacity-100 mt-3">
            {{ showAllPhasen ? 'Phasen-Übersicht ausblenden' : 'Alle Phasen anzeigen →' }}
          </button>
        </div>

        <!-- Phasen-Liste (passive Sicht) -->
        <div v-if="phasen.length && showAllPhasen" class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Alle Phasen</h3>
          <ul class="space-y-2">
            <li v-for="(p, idx) in phasen" :key="p.id" class="flex items-center gap-3 text-sm">
              <div :class="['w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0', phasenStatus(p) === 'done' ? 'bg-green-100 text-green-700' : phasenStatus(p) === 'current' ? 'bg-[#097e92] text-white' : 'bg-gray-100 text-gray-400']">
                <Check v-if="phasenStatus(p) === 'done'" class="w-3.5 h-3.5" />
                <span v-else>{{ idx + 1 }}</span>
              </div>
              <span :class="phasenStatus(p) === 'done' ? 'text-gray-400 line-through' : phasenStatus(p) === 'current' ? 'font-semibold text-gray-900' : 'text-gray-500'">{{ p.titel.replace(/^\d+\.\s*/, '') }}</span>
            </li>
          </ul>
          <p class="text-xs text-gray-400 mt-4">Die Phasen werden von deinem M&A-Berater bei mibeca aktualisiert.</p>
        </div>

        <!-- Fortschritt -->
        <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-gray-700">Gesamtfortschritt</span>
            <span class="text-sm font-bold text-[#097e92]">{{ doneCount }} / {{ checkliste.length }} erledigt</span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2">
            <div class="bg-[#097e92] h-2 rounded-full transition-all" :style="`width: ${progress}%`"></div>
          </div>
          <div class="text-xs text-gray-400 mt-1">{{ progress }}% abgeschlossen</div>
        </div>

        <!-- Checkliste -->
        <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div class="px-5 py-3 border-b border-gray-50">
            <h3 class="text-sm font-semibold text-gray-700">Aufgaben-Checkliste</h3>
          </div>
          <div v-if="loadingCheck" class="p-6 text-center text-gray-400 text-sm">Lade Checkliste…</div>
          <ul v-else class="divide-y divide-gray-50">
            <li v-for="item in checkliste" :key="item.id"
              class="flex items-center gap-4 px-5 py-3 hover:bg-gray-50 cursor-pointer"
              @click="toggleItem(item)">
              <div :class="['w-5 h-5 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors', item.done ? 'bg-[#097e92] border-[#097e92]' : 'border-gray-300 hover:border-[#097e92]']">
                <Check v-if="item.done" class="w-3 h-3 text-white" />
              </div>
              <span :class="['text-sm', item.done ? 'line-through text-gray-400' : 'text-gray-700']">{{ item.label }}</span>
              <CheckCircle v-if="item.done" class="w-4 h-4 text-green-500 ml-auto" />
              <Circle v-else class="w-4 h-4 text-gray-200 ml-auto" />
            </li>
          </ul>
        </div>
      </div>

      <!-- Tab: Fragebogen Unternehmensbewertung -->
      <div v-else-if="tab === 'fragebogen'">
        <Fragebogen :target-id="targetId" />
      </div>

      <!-- Tab: Bewertung (Scoring auf Basis 33 Fragen) -->
      <div v-else-if="tab === 'bewertung'">
        <Unternehmensbewertung :target-id="targetId" :read-only="impersonating" />
      </div>

      <!-- Tab: Meine Daten (Mandat-Vorlage) -->
      <div v-else-if="tab === 'mandat'">
        <MandatDaten :target-id="targetId" :read-only="impersonating" />
      </div>

      <!-- Tab: Mein Exposé (Freigabe) -->
      <div v-else-if="tab === 'expose'">
        <ExposeFreigabe :target-id="targetId" />
      </div>

      <!-- Tab: Verlauf -->
      <div v-else-if="tab === 'verlauf'">
        <Verlauf :target-id="targetId" />
      </div>

      <!-- Tab: Interessenten -->
      <div v-else-if="tab === 'interessenten'">
        <h2 class="text-xl font-bold text-gray-900 mb-5">Meine Interessenten</h2>
        <div v-if="loadingInt" class="text-center text-gray-400 text-sm py-10">Lade Interessenten…</div>
        <div v-else-if="!interessenten.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400 text-sm">
          <Users class="w-10 h-10 mx-auto mb-3 text-gray-200" />
          Noch keine Interessenten. Sobald jemand ein NDA unterzeichnet, erscheint er hier.
        </div>
        <div v-else class="space-y-3">
          <div v-for="i in interessenten" :key="i.RowKey" class="bg-white rounded-xl border border-gray-100 p-5">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-medium text-gray-800">{{ i.firma || i.name }}</span>
                  <span :class="ndaClass(i.ndaStatus)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ ndaLabel(i.ndaStatus) }}</span>
                  <span v-if="i.veto" class="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-medium">VETO</span>
                </div>
                <div class="text-xs text-gray-400 mt-0.5">{{ i.plz }} {{ i.ort }}</div>
              </div>
              <!-- Rating -->
              <div class="flex items-center gap-0.5">
                <button v-for="n in 5" :key="n" @click="setRating(i, n)" class="p-0.5">
                  <Star :class="n <= i.rating ? 'text-[#c8b274] fill-[#c8b274]' : 'text-gray-200'" class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Aktionen -->
            <div class="flex gap-2 mt-3">
              <!-- Freigabe-Toggle -->
              <button @click="toggleFreigabe(i)"
                :class="['flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors', i.freigegebenFuerKontakt ? 'bg-green-50 text-green-700 border-green-200' : 'text-gray-500 border-gray-200 hover:bg-gray-50']">
                <UserCheck class="w-3.5 h-3.5" />
                {{ i.freigegebenFuerKontakt ? 'Freigegeben' : 'Freigabe geben' }}
              </button>

              <!-- VETO -->
              <button v-if="!i.veto" @click="openVeto(i)"
                class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors">
                <Ban class="w-3.5 h-3.5" /> VETO setzen
              </button>
              <button v-else @click="removeVeto(i)"
                class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-600 border border-red-200">
                <Ban class="w-3.5 h-3.5" /> VETO entfernen
              </button>
            </div>

            <!-- VETO Begründung -->
            <div v-if="i.veto && i.vetoBegruendung" class="mt-2 text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">
              Begründung: {{ i.vetoBegruendung }}
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Links -->
      <div v-else-if="tab === 'links'">
        <div class="flex items-center justify-between mb-5">
          <h2 class="text-xl font-bold text-gray-900">Wichtige Links</h2>
          <button @click="showLinkModal = true" class="flex items-center gap-2 px-3 py-2 bg-[#097e92] text-white rounded-xl text-sm hover:bg-[#0a9aaf]">
            <Plus class="w-4 h-4" /> Link hinzufügen
          </button>
        </div>
        <div v-if="!links.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400 text-sm">
          <LinkIcon class="w-10 h-10 mx-auto mb-3 text-gray-200" />
          Noch keine Links hinterlegt.
        </div>
        <div v-else class="space-y-3">
          <div v-for="l in links" :key="l.RowKey || l.id" class="bg-white rounded-xl border border-gray-100 p-4 flex items-start gap-3">
            <div class="w-10 h-10 bg-[#097e92]/10 rounded-lg flex items-center justify-center flex-shrink-0">
              <LinkIcon class="w-5 h-5 text-[#097e92]" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <a :href="l.url" target="_blank" rel="noopener" class="font-medium text-gray-900 hover:text-[#097e92] truncate">{{ l.titel }}</a>
                <span v-if="l.kategorie" class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{{ l.kategorie }}</span>
                <span v-if="l.system" class="text-[10px] uppercase tracking-wide bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-semibold">System</span>
              </div>
              <div class="text-xs text-gray-400 mt-0.5 truncate">{{ l.url }}</div>
              <div v-if="l.beschreibung" class="text-sm text-gray-600 mt-1">{{ l.beschreibung }}</div>
            </div>
            <button v-if="!l.system" @click="deleteLink(l)" class="text-gray-300 hover:text-red-500"><Trash2 class="w-4 h-4" /></button>
          </div>
        </div>
      </div>

      <!-- Link Modal -->
      <div v-if="showLinkModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
        <div class="bg-white rounded-2xl p-6 w-full max-w-md">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-gray-900">Link hinzufügen</h3>
            <button @click="showLinkModal = false"><X class="w-5 h-5 text-gray-400" /></button>
          </div>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Titel *</label>
              <input v-model="linkForm.titel" placeholder="z.B. Datenraum" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">URL *</label>
              <input v-model="linkForm.url" placeholder="https://…" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Kategorie</label>
              <select v-model="linkForm.kategorie" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none">
                <option>Allgemein</option><option>Datenraum</option><option>Element-Raum</option><option>Tools</option><option>Externe Dokumente</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Beschreibung</label>
              <textarea v-model="linkForm.beschreibung" rows="2" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 resize-none"></textarea>
            </div>
          </div>
          <div class="flex gap-3 mt-5">
            <button @click="showLinkModal = false" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
            <button @click="createLink" class="flex-1 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium">Speichern</button>
          </div>
        </div>
      </div>

      <!-- Tab: Dokumente -->
      <div v-else-if="tab === 'dokumente'">
        <h2 class="text-xl font-bold text-gray-900 mb-5">Meine Dokumente</h2>

        <div v-if="!selectedOrdner" class="grid grid-cols-2 gap-3">
          <button v-for="ordner in ordnerListe" :key="ordner"
            @click="openOrdner(ordner)"
            class="bg-white rounded-xl border border-gray-100 p-4 text-left hover:border-[#097e92]/40 hover:shadow-sm transition-all flex items-center gap-3">
            <Folder class="w-6 h-6 text-[#097e92]" />
            <div>
              <div class="text-sm font-medium text-gray-700">{{ ordner }}</div>
              <div class="text-xs text-gray-400">{{ countInOrdner(ordner) }} Dateien</div>
            </div>
          </button>
        </div>

        <div v-else>
          <button @click="selectedOrdner = null" class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
            <ChevronLeft class="w-4 h-4" /> Zurück
          </button>
          <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <div class="px-4 py-3 border-b border-gray-50 flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700">{{ selectedOrdner }}</span>
              <label class="flex items-center gap-2 px-3 py-1.5 bg-[#097e92] text-white rounded-lg text-xs cursor-pointer hover:bg-[#0a9aaf]">
                <Upload class="w-3.5 h-3.5" /> Hochladen
                <input type="file" class="hidden" @change="uploadFile" />
              </label>
            </div>
            <div v-if="!filteredDok.length" class="p-6 text-center text-gray-400 text-sm">Keine Dateien in diesem Ordner.</div>
            <div v-for="dok in filteredDok" :key="dok.RowKey"
              class="flex items-center justify-between px-4 py-3 border-b border-gray-50 last:border-0">
              <div class="flex items-center gap-3">
                <FileText class="w-4 h-4 text-gray-400" />
                <div>
                  <div class="text-sm font-medium text-gray-700">{{ dok.dateiname }}</div>
                  <div class="text-xs text-gray-400">{{ formatDate(dok.hochgeladenAm) }}</div>
                </div>
              </div>
              <button @click="downloadDok(dok)" class="flex items-center gap-1 text-xs text-[#097e92] hover:text-[#0a9aaf]">
                <Download class="w-3.5 h-3.5" /> Download
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- VETO Modal -->
    <div v-if="vetoTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm">
        <h3 class="font-bold text-gray-900 mb-2">VETO setzen</h3>
        <p class="text-sm text-gray-500 mb-3">Bitte gib eine kurze Begründung an:</p>
        <textarea v-model="vetoText" rows="3" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-200 resize-none" placeholder="Begründung…"></textarea>
        <div class="flex gap-3 mt-4">
          <button @click="vetoTarget = null; vetoText = ''" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
          <button @click="confirmVeto" class="flex-1 px-4 py-2 bg-red-500 text-white rounded-xl text-sm font-medium">VETO bestätigen</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  Building2, LogOut, Briefcase, Users, FolderOpen, Check, CheckCircle, Circle,
  Star, UserCheck, Ban, Folder, ChevronLeft, Upload, FileText, Download,
  Link as LinkIcon, Plus, Trash2, X, ClipboardList, FileEdit, MessageSquare, TrendingUp, Clock, Bell
} from '@lucide/vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'
import MandatDaten from '../components/target/MandatDaten.vue'
import Fragebogen from '../components/target/Fragebogen.vue'
import Unternehmensbewertung from '../components/target/Unternehmensbewertung.vue'
import ExposeFreigabe from '../components/target/ExposeFreigabe.vue'
import Verlauf from '../components/admin/Verlauf.vue'
import { authFetch, getInteressenten, updateInteressent, getDokumente, verlaufUnreadCount } from '../api.js'

const props = defineProps({ userName: String, projekttyp: String, impersonating: Boolean })
const emit = defineEmits(['logout'])
const targetId = sessionStorage.getItem('targetId') || ''

const tab = ref('projekt')
const checkliste = ref([])
const interessenten = ref([])
const dokumente = ref([])
const links = ref([])
const target = ref(null)
const vertragInfo = computed(() => {
  try { return target.value?.vertragJson ? JSON.parse(target.value.vertragJson) : null } catch { return null }
})
function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
const showAllPhasen = ref(false)
const loadingCheck = ref(true)
const loadingInt = ref(true)
const selectedOrdner = ref(null)
const vetoTarget = ref(null)
const vetoText = ref('')
const showLinkModal = ref(false)
const linkForm = ref({ titel: '', url: '', beschreibung: '', kategorie: 'Allgemein' })

// Projekttypen mit Links-Tab
const TYPES_WITH_LINKS = ['UVE Target', 'MC Target', 'MC Investoren']

const navItems = computed(() => {
  const base = [
    { tab: 'projekt', label: 'Mein Projekt', icon: Briefcase },
    { tab: 'mandat', label: 'Meine Daten', icon: ClipboardList },
    { tab: 'fragebogen', label: 'Fragebogen', icon: FileEdit },
    { tab: 'bewertung', label: 'Bewertung', icon: TrendingUp },
    { tab: 'expose', label: 'Mein Exposé', icon: FileText },
    { tab: 'interessenten', label: 'Interessenten', icon: Users },
    { tab: 'dokumente', label: 'Dokumente', icon: FolderOpen },
  ]
  if (TYPES_WITH_LINKS.includes(props.projekttyp)) {
    base.push({ tab: 'links', label: 'Links', icon: LinkIcon })
  }
  base.push({ tab: 'verlauf', label: 'Verlauf', icon: MessageSquare })
  return base
})
const visibleNavItems = computed(() => navItems.value)

const ordnerListe = ['Unterlagen Ausschreibung', 'Exposé', 'Protokoll', 'NDA', 'Gesprächsnotizen', 'Datenraum', 'Beratervertrag', 'Diverses']

const doneCount = computed(() => checkliste.value.filter(i => i.done).length)
const progress = computed(() => !checkliste.value.length ? 0 : Math.round(doneCount.value / checkliste.value.length * 100))

// --- Master-Prozess (Phasen-Sicht für Kunden) ---
const phasen = computed(() => {
  try { return JSON.parse(target.value?.phasenJson || '[]') } catch { return [] }
})
function isPhaseDone(p) { return p.aufgaben && p.aufgaben.length && p.aufgaben.every(t => t.done) }
const currentPhase = computed(() => {
  for (let i = 0; i < phasen.value.length; i++) {
    if (!isPhaseDone(phasen.value[i])) return i + 1
  }
  return phasen.value.length || 1
})
const currentPhaseTitle = computed(() => {
  const p = phasen.value[currentPhase.value - 1]
  return p ? p.titel.replace(/^\d+\.\s*/, '') : '—'
})
const donePhasen = computed(() => phasen.value.filter(isPhaseDone).length)
const phasenProgress = computed(() => !phasen.value.length ? 0 : Math.round(donePhasen.value / phasen.value.length * 100))
function phasenStatus(p) {
  if (isPhaseDone(p)) return 'done'
  if (phasen.value[currentPhase.value - 1]?.id === p.id) return 'current'
  return 'pending'
}
const filteredDok = computed(() => dokumente.value.filter(d => d.ordner === selectedOrdner.value))

function countInOrdner(o) { return dokumente.value.filter(d => d.ordner === o).length }

async function loadAllData() {
  if (targetId) {
    try {
      target.value = await authFetch('/target-get', { method: 'POST', data: { id: targetId } })
      checkliste.value = JSON.parse(target.value.checklisteJson || '[]')
    } catch {} finally { loadingCheck.value = false }
    try { interessenten.value = await getInteressenten(targetId) } catch {} finally { loadingInt.value = false }
    try { dokumente.value = await getDokumente(targetId) } catch {}
  } else if (props.impersonating && props.projekttyp) {
    // Admin testet eine Ansicht – zeige Beispiel-Checkliste je Projekttyp
    try {
      checkliste.value = await authFetch(`/checkliste-vorlage/${encodeURIComponent(props.projekttyp)}`)
    } catch {}
    loadingCheck.value = false; loadingInt.value = false
  } else {
    loadingCheck.value = false; loadingInt.value = false
  }
  // Links IMMER neu setzen – System-Links bei UVE auch im Impersonation-Mode
  try {
    const isUve = (target.value?.projekttyp || props.projekttyp || '').toLowerCase().includes('uve')
    const systemLinks = isUve ? [
      { id: 'sys-uve-kurs', system: true, kategorie: 'Kajabi Videokurse', titel: 'UVE Videokurse', url: 'https://www.mike-bergmann-akademie.de/products/mb058-uv-expressweg', beschreibung: 'Unternehmensverkauf-Expressweg – Videokurse von Mike Bergmann.' },
      { id: 'sys-uve-livecall', system: true, kategorie: 'Live-Calls', titel: 'UVE Live Call (Zoom)', url: 'https://us02web.zoom.us/j/85389200945?pwd=btDgPrB3awzuJNtxh8nrU8zX1cQSIb.1', beschreibung: 'Wiederkehrender Live Call zum UVE.' },
    ] : []
    const custom = target.value?.linksJson ? JSON.parse(target.value.linksJson) : []
    links.value = [...systemLinks, ...custom.filter(l => !systemLinks.some(s => s.id === l.id))]
  } catch { links.value = [] }
}

const unreadTotal = ref(0)
async function pollUnread() {
  try { const r = await verlaufUnreadCount(); unreadTotal.value = r?.total || 0 } catch {}
}
let unreadTimer = null
onMounted(() => {
  loadAllData()
  pollUnread()
  unreadTimer = setInterval(pollUnread, 30000)
})
import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => { if (unreadTimer) clearInterval(unreadTimer) })
watch(() => props.projekttyp, loadAllData)

async function createLink() {
  if (!linkForm.value.titel || !linkForm.value.url) return
  const tid = targetId || 'demo'
  const created = await authFetch(`/targets/${tid}/links`, { method: 'POST', data: linkForm.value })
  links.value.push(created)
  showLinkModal.value = false
  linkForm.value = { titel: '', url: '', beschreibung: '', kategorie: 'Allgemein' }
}

async function deleteLink(l) {
  if (!confirm('Link löschen?')) return
  await authFetch(`/targets/${l.targetId}/links/${l.RowKey}`, { method: 'DELETE' })
  links.value = links.value.filter(x => x.RowKey !== l.RowKey)
}

async function toggleItem(item) {
  item.done = !item.done
  await authFetch(`/targets/${targetId}/checkliste`, { method: 'PATCH', data: { id: item.id, done: item.done } })
}

async function setRating(i, n) {
  i.rating = n
  try { await updateInteressent(i.RowKey, { rating: n }) } catch (e) { console.error(e) }
}

async function toggleFreigabe(i) {
  i.freigegebenFuerKontakt = !i.freigegebenFuerKontakt
  try { await updateInteressent(i.RowKey, { freigegebenFuerKontakt: i.freigegebenFuerKontakt }) } catch (e) { console.error(e) }
}

function openVeto(i) { vetoTarget.value = i }
async function confirmVeto() {
  vetoTarget.value.veto = true
  vetoTarget.value.vetoBegruendung = vetoText.value
  try { await updateInteressent(vetoTarget.value.RowKey, { veto: true, vetoBegruendung: vetoText.value }) } catch (e) { console.error(e) }
  vetoTarget.value = null; vetoText.value = ''
}
async function removeVeto(i) {
  i.veto = false; i.vetoBegruendung = ''
  try { await updateInteressent(i.RowKey, { veto: false, vetoBegruendung: '' }) } catch (e) { console.error(e) }
}

function ndaClass(s) {
  if (s === 'unterzeichnet') return 'bg-green-100 text-green-700'
  if (s === 'gesendet') return 'bg-yellow-100 text-yellow-700'
  if (s === 'abgelehnt') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-500'
}
function ndaLabel(s) {
  return { unterzeichnet:'NDA unterzeichnet', gesendet:'NDA gesendet', abgelehnt:'NDA abgelehnt' }[s] || 'NDA ausstehend'
}

async function openOrdner(o) { selectedOrdner.value = o }
async function uploadFile(e) {
  const file = e.target.files[0]; if (!file) return
  await authFetch(`/targets/${targetId}/dokumente/upload?ordner=${encodeURIComponent(selectedOrdner.value)}&dateiname=${encodeURIComponent(file.name)}`, { method: 'POST', data: file, headers: { 'Content-Type': file.type } })
  dokumente.value = await getDokumente(targetId)
  e.target.value = ''
}
async function downloadDok(dok) {
  const r = await authFetch(`/targets/${targetId}/dokumente/${dok.RowKey}/download`)
  window.open(r.url, '_blank')
}
</script>
