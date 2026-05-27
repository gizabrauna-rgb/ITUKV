<template>
  <div>
    <div class="mb-5 flex items-start justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Kandidaten-Match</h2>
        <p class="text-sm text-gray-500 mt-1">Targets, die für diesen Käufer in Frage kommen. Score zeigt, wie gut sie zum Suchprofil passen.</p>
      </div>
      <button @click="refreshList" :disabled="loading"
        class="flex items-center gap-2 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8] disabled:opacity-50">
        <RefreshCw :class="['w-4 h-4', loading ? 'animate-spin' : '']" />
        {{ loading ? 'Lade…' : 'Kandidaten neu suchen' }}
      </button>
    </div>

    <!-- Filter + Manuell hinzufügen -->
    <div class="flex gap-2 mb-3 flex-wrap">
      <button @click="filter = 'long'" :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium', filter === 'long' ? 'bg-[#0088ba] text-white' : 'bg-white border border-gray-200']">
        <Lightbulb class="w-3.5 h-3.5" /> Vorschläge ({{ vorschlagCount }})
      </button>
      <button @click="filter = 'short'" :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium', filter === 'short' ? 'bg-[#0088ba] text-white' : 'bg-white border border-gray-200']">
        <Star class="w-3.5 h-3.5" /> Favoriten ({{ shortListCount }})
      </button>
      <button @click="filter = 'fuerKaeufer'" :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium', filter === 'fuerKaeufer' ? 'bg-purple-600 text-white' : 'bg-white border border-gray-200']">
        <Eye class="w-3.5 h-3.5" /> Für Käufer freigegeben ({{ fuerKaeuferCount }})
      </button>
      <button @click="filter = 'abgesagt'" :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium', filter === 'abgesagt' ? 'bg-[#0088ba] text-white' : 'bg-white border border-gray-200']">
        <Ban class="w-3.5 h-3.5" /> Abgelehnt ({{ abgesagtCount }})
      </button>
      <button @click="showAddModal = true" class="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border-2 border-dashed border-gray-300 text-gray-600 hover:border-[#0088ba] hover:text-[#0088ba]">
        <Plus class="w-3.5 h-3.5" /> Kandidat manuell hinzufügen
      </button>
    </div>

    <!-- Banner: Suchprofil leer -->
    <div v-if="profilLeer && !loading" class="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 mb-3 flex items-start gap-2">
      <AlertCircle class="w-4 h-4 flex-shrink-0 mt-0.5" />
      <div>
        <strong>Kein Suchprofil hinterlegt</strong> – aktuell werden alle CRM-Kontakte angezeigt, nur nach PLZ sortiert. Lege ein Suchprofil im Tab „Suchprofil" an, um nur passende Kandidaten zu sehen.
      </div>
    </div>

    <!-- Hint Box -->
    <div class="bg-blue-50 border border-blue-100 rounded-lg p-3 text-xs text-blue-900 mb-3">
      <strong>Workflow:</strong> Markiere zuerst Favoriten (nur intern sichtbar). Mit <Eye class="w-3 h-3 inline -mt-0.5" /> gibst du den Kandidaten für den Käufer frei. Der Käufer kann dann Feedback geben (Interesse / kein Interesse / Rückfrage).
    </div>

    <!-- Modal: Manuell hinzufügen -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4" @click.self="showAddModal = false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-lg">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-900">Kandidat manuell hinzufügen</h3>
          <button @click="showAddModal = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <p class="text-xs text-gray-500 mb-3">Suche einen Kontakt aus dem CRM oder lege einen neuen Eintrag an.</p>
        <input v-model="addSearch" placeholder="Firma oder Name suchen…" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
        <div class="max-h-80 overflow-y-auto border border-gray-100 rounded-xl">
          <div v-if="!addCandidates.length" class="p-4 text-sm text-gray-400 text-center">
            <span v-if="!addSearch">Bitte Suchbegriff eingeben.</span>
            <span v-else>Keine passenden Kontakte gefunden.</span>
          </div>
          <button v-for="k in addCandidates" :key="k.RowKey" @click="addManuell(k)"
            class="w-full px-3 py-2 hover:bg-gray-50 flex items-start gap-2 text-left border-b border-gray-50 last:border-0">
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-gray-800">{{ k.firma }}</div>
              <div class="text-xs text-gray-500">{{ k.name }} · {{ k.plz }} {{ k.ort }}</div>
            </div>
            <Plus class="w-4 h-4 text-[#0088ba] flex-shrink-0 mt-1" />
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center text-sm text-gray-400 py-10">Lade Kandidaten…</div>
    <div v-else-if="!visibleItems.length" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">
      <Users class="w-10 h-10 mx-auto mb-3 text-gray-200" />
      Keine Kandidaten gefunden.
      <p class="text-xs mt-2">Vergiss nicht: erst Suchprofil ausfüllen, dann Long-List neu berechnen.</p>
    </div>

    <div v-else class="space-y-2">
      <div v-for="k in visibleItems" :key="k.id || k.RowKey"
        :class="['rounded-xl border p-4 flex items-start gap-3',
                 isFreigegeben(k) ? 'bg-purple-50 border-purple-200' :
                 k.istInternesTarget ? 'bg-orange-50 border-orange-200' : 'bg-white border-gray-100']">
        <!-- Score-Kreis -->
        <div :class="['w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0',
                       k.score >= 70 ? 'bg-green-100 text-green-700' : k.score >= 40 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-500']">
          {{ k.score }}%
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-medium text-gray-900">{{ k.firma }}</span>
            <span v-if="k.name" class="text-xs text-gray-500">· {{ k.name }}</span>
            <span v-if="k.istInternesTarget" class="text-[10px] bg-orange-500 text-white px-2 py-0.5 rounded-full font-semibold uppercase tracking-wide">In-House Match</span>
            <span v-if="k.istInternesTarget && k.mbNr" class="text-[10px] font-mono bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded">{{ k.mbNr }}</span>
            <span v-if="k.istKunde && !k.istInternesTarget" class="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full font-semibold">Kunde</span>
            <span v-if="k.istExKunde" class="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded-full font-semibold">Ex-Kunde</span>
          </div>
          <div class="text-xs text-gray-500 mt-0.5">
            {{ k.plz }} {{ k.ort }} · {{ k.mitarbeiter || '?' }} MA · {{ k.umsatz || '?' }} Umsatz
          </div>
          <div v-if="k.matchGruende?.length" class="flex flex-wrap gap-1 mt-2">
            <span v-for="g in cleanGruende(k.matchGruende)" :key="g" class="text-[10px] bg-[#0088ba]/10 text-[#0088ba] px-2 py-0.5 rounded-full">{{ g }}</span>
          </div>
          <div v-if="k.ablehnGruende?.length" class="flex flex-wrap gap-1 mt-1">
            <span v-for="g in k.ablehnGruende" :key="g" class="text-[10px] bg-red-50 text-red-600 px-2 py-0.5 rounded-full">{{ g }}</span>
          </div>
          <!-- Käufer-Feedback (wenn vorhanden) -->
          <div v-if="kaeuferFeedback[k.id]" class="mt-2 p-2 rounded-lg bg-purple-100 text-purple-900 text-xs">
            <strong>Feedback Käufer:</strong>
            <span v-if="kaeuferFeedback[k.id].interesse === 'ja'" class="ml-1 font-medium">Interesse</span>
            <span v-else-if="kaeuferFeedback[k.id].interesse === 'nein'" class="ml-1 font-medium">Kein Interesse</span>
            <span v-else-if="kaeuferFeedback[k.id].interesse === 'rueckfrage'" class="ml-1 font-medium">Rückfrage</span>
            <span v-if="kaeuferFeedback[k.id].kommentar" class="block mt-1 italic">„{{ kaeuferFeedback[k.id].kommentar }}"</span>
          </div>
        </div>
        <div class="flex gap-1 flex-shrink-0">
          <button v-if="decisions[k.id] !== 'short'" @click="setStatus(k, 'short')" title="Zu Favoriten hinzufügen"
            class="p-1.5 hover:bg-green-50 rounded text-green-600"><Check class="w-4 h-4" /></button>
          <button v-if="decisions[k.id] === 'short' && !isFreigegeben(k)" @click="freigeben(k, true)" title="Für Käufer freigeben"
            class="p-1.5 hover:bg-purple-50 rounded text-gray-500"><EyeOff class="w-4 h-4" /></button>
          <button v-if="isFreigegeben(k)" @click="freigeben(k, false)" title="Sichtbar für Käufer – klick zum Zurückziehen"
            class="p-1.5 hover:bg-purple-50 rounded text-purple-600"><Eye class="w-4 h-4" /></button>
          <button v-if="decisions[k.id] !== 'abgesagt'" @click="setStatus(k, 'abgesagt')" title="Ablehnen"
            class="p-1.5 hover:bg-red-50 rounded text-red-600"><X class="w-4 h-4" /></button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Users, RefreshCw, Check, X, Plus, Eye, EyeOff, Lightbulb, Star, Ban, AlertCircle } from '@lucide/vue'
import { authFetch, getKontakte, getTargets } from '../../api.js'

const props = defineProps({ targetId: String })

const items = ref([])
const loading = ref(true)
const filter = ref('long')
const decisions = ref({})  // { kontaktId: 'short' | 'abgesagt' }
const showAddModal = ref(false)
const addSearch = ref('')
const allKontakte = ref([])
const manuellAdded = ref([])
const fuerKaeuferIds = ref([])     // IDs der fuer Kaeufer freigegebenen
const kaeuferFeedback = ref({})    // { kontaktId: { interesse, kommentar } }
const profilLeer = ref(false)

function isFreigegeben(k) { return fuerKaeuferIds.value.includes(k.id) }
function cleanGruende(arr) {
  // entferne emojis am Anfang von Strings
  return (arr || []).map(g => String(g).replace(/^[\p{Emoji_Presentation}\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]\s*/u, '').trim())
}
const fuerKaeuferCount = computed(() => items.value.filter(k => fuerKaeuferIds.value.includes(k.id)).length)
const vorschlagCount = computed(() => items.value.filter(k => !decisions.value[k.id] && !fuerKaeuferIds.value.includes(k.id)).length)

async function freigeben(k, on) {
  if (on) {
    if (!fuerKaeuferIds.value.includes(k.id)) fuerKaeuferIds.value.push(k.id)
  } else {
    fuerKaeuferIds.value = fuerKaeuferIds.value.filter(id => id !== k.id)
  }
  try {
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, fuerKaeuferIdsJson: JSON.stringify(fuerKaeuferIds.value) } })
  } catch (e) { console.error(e) }
}

const addCandidates = computed(() => {
  const q = addSearch.value.trim().toLowerCase()
  if (!q) return []
  const existingIds = new Set(items.value.map(i => i.id))
  return allKontakte.value
    .filter(k => !existingIds.has(k.RowKey || k.id))
    .filter(k =>
      (k.firma || '').toLowerCase().includes(q) ||
      (k.name || '').toLowerCase().includes(q) ||
      (k.email || '').toLowerCase().includes(q)
    )
    .slice(0, 20)
})

function addManuell(k) {
  const id = k.RowKey || k.id
  items.value.unshift({
    ...k, id, score: 50,
    matchGruende: ['Manuell hinzugefügt'],
    ablehnGruende: [],
    _quelle: 'manuell',
  })
  manuellAdded.value.push(id)
  showAddModal.value = false
  addSearch.value = ''
  saveManuell()
}

async function saveManuell() {
  try {
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, longListManuellJson: JSON.stringify(manuellAdded.value) } })
  } catch (e) { console.error(e) }
}

// Counts NUR aus items.value berechnen (nicht aus rohen decisions/fuerKaeuferIds)
// → konsistent mit den tatsächlich sichtbaren Listen
const shortListCount = computed(() => items.value.filter(k => decisions.value[k.id] === 'short').length)
const abgesagtCount = computed(() => items.value.filter(k => decisions.value[k.id] === 'abgesagt').length)
const visibleItems = computed(() => {
  if (filter.value === 'long') return items.value.filter(k => !decisions.value[k.id] && !fuerKaeuferIds.value.includes(k.id))
  if (filter.value === 'short') return items.value.filter(k => decisions.value[k.id] === 'short')
  if (filter.value === 'fuerKaeufer') return items.value.filter(k => fuerKaeuferIds.value.includes(k.id))
  if (filter.value === 'abgesagt') return items.value.filter(k => decisions.value[k.id] === 'abgesagt')
  return items.value
})

function hasSuchprofil(s) {
  if (!s) return false
  return !!(s.maMin || s.maMax || s.umsatzMin || s.umsatzMax ||
            s.ebitMargeMin || s.recurringMin ||
            s.zentralPlz || (s.regionen && s.regionen.trim()) ||
            (s.regionenAusschluss && s.regionenAusschluss.trim()) ||
            (s.itFokus && s.itFokus.length) ||
            (s.itFokusSonstige && s.itFokusSonstige.trim()))
}

// Mapping IT-Fokus -> Kontakt-Flag-Felder (aus dem CRM-Schema)
const FOKUS_FLAG_MAP = {
  'MSP / Managed Services': ['hatMC', 'hatUC', 'hatUCS'],
  'IT-Security': ['hatKIT', 'hatMSQ'],
  'Cloud (Azure/AWS)': ['hatKIwerkOne'],
  'ERP / SAP': [],
  'Software-Entwicklung': [],
  'Telefonanlagen': [],
  'Drucker/Kopierer': [],
  'Netzwerk': [],
  'Beratung / Consulting': ['hatVME', 'hatFKE'],
}

function fokusMatch(kontakt, fokusName) {
  // 1. Flag-Match (CRM-Tags)
  const flags = FOKUS_FLAG_MAP[fokusName] || []
  if (flags.some(f => kontakt[f])) return true
  // 2. Freitext-Match in „bietet", „branche"
  const haystack = `${kontakt.bietet || ''} ${kontakt.branche || ''} ${kontakt.beschreibung || ''}`.toLowerCase()
  const needle = fokusName.toLowerCase().split('/')[0].trim()
  return haystack.includes(needle)
}

function scoreFor(kontakt, suchprofil) {
  // Kein Suchprofil → Basis-Score, Anzeige + Sortierung erfolgen nach PLZ
  if (!hasSuchprofil(suchprofil)) {
    return { score: 50, reasons: ['kein Suchprofil – nach PLZ sortiert'], dislikes: [], ausgeschlossen: false }
  }

  let score = 0
  const reasons = []
  const dislikes = []
  const ist = (n, min, max) => (!min || n >= min) && (!max || n <= max)
  const ma = parseInt(kontakt.mitarbeiter) || 0
  // CRM-Kontakte haben „umsatzTeur" (Zahl), interne Targets haben „umsatz" (Freitext „ca. 2,1 Mio. €")
  const umsatzNum = parseFloat(kontakt.umsatzTeur) ||
                    parseFloat((kontakt.umsatz || '').toString().replace(/[^\d.,]/g, '').replace(',', '.')) || 0
  const ebitMarge = parseFloat(kontakt.ebitMarge) || 0
  const recurring = parseFloat(kontakt.recurringPct || kontakt.recurring) || 0

  // ---- Region & Ausschluss ----
  let ausgeschlossen = false
  if (suchprofil.regionenAusschluss && (kontakt.ort || kontakt.plz)) {
    const aus = suchprofil.regionenAusschluss.toLowerCase().split(/[,;]/).map(s => s.trim()).filter(Boolean)
    const ortLow = (kontakt.ort || '').toLowerCase()
    const plz = (kontakt.plz || '')
    if (aus.some(r => ortLow.includes(r) || (plz && plz.startsWith(r.slice(0, 2))))) {
      ausgeschlossen = true
      dislikes.push('in Ausschluss-Region')
    }
  }

  if (!ausgeschlossen) {
    // PLZ-Mittelpunkt: bis 1. Ziffer Match +5, bis 2. Ziffern +15
    if (suchprofil.zentralPlz && kontakt.plz) {
      if (kontakt.plz.startsWith(suchprofil.zentralPlz.slice(0, 2))) {
        score += 15; reasons.push('PLZ-Region passt')
      } else if (kontakt.plz.startsWith(suchprofil.zentralPlz.slice(0, 1))) {
        score += 5; reasons.push('PLZ-Region grob')
      }
    }
    if (suchprofil.regionen && (kontakt.ort || kontakt.plz)) {
      const regs = suchprofil.regionen.toLowerCase().split(/[,;]/).map(s => s.trim()).filter(Boolean)
      const ortLow = (kontakt.ort || '').toLowerCase()
      const plz = (kontakt.plz || '')
      if (regs.some(r => ortLow.includes(r) || (plz && plz.startsWith(r.slice(0, 2))))) {
        score += 10; reasons.push('Region erlaubt')
      }
    }
  }

  // ---- Mitarbeiter ----
  if (suchprofil.maMin || suchprofil.maMax) {
    if (ma > 0 && ist(ma, suchprofil.maMin, suchprofil.maMax)) {
      score += 20; reasons.push(`${ma} MA passt`)
    } else if (ma > 0) {
      score -= 20
      dislikes.push(`${ma} MA außerhalb ${suchprofil.maMin || '?'}-${suchprofil.maMax || '?'}`)
    }
  }

  // ---- Umsatz (in TEUR) ----
  if (suchprofil.umsatzMin || suchprofil.umsatzMax) {
    if (umsatzNum > 0 && ist(umsatzNum, suchprofil.umsatzMin, suchprofil.umsatzMax)) {
      score += 15; reasons.push(`Umsatz ${umsatzNum} TEUR passt`)
    } else if (umsatzNum > 0) {
      score -= 10
      dislikes.push(`Umsatz ${umsatzNum} außerhalb ${suchprofil.umsatzMin || '?'}-${suchprofil.umsatzMax || '?'}`)
    }
  }

  // ---- EBIT-Marge / Recurring (optional, nur Bonus wenn Daten vorhanden) ----
  if (suchprofil.ebitMargeMin && ebitMarge > 0) {
    if (ebitMarge >= suchprofil.ebitMargeMin) {
      score += 8; reasons.push(`EBIT-Marge ${ebitMarge}% ok`)
    } else {
      score -= 5; dislikes.push(`EBIT-Marge nur ${ebitMarge}%`)
    }
  }
  if (suchprofil.recurringMin && recurring > 0) {
    if (recurring >= suchprofil.recurringMin) {
      score += 8; reasons.push(`Recurring ${recurring}% ok`)
    }
  }

  // ---- IT-Fokus ----
  if (suchprofil.itFokus && suchprofil.itFokus.length) {
    for (const f of suchprofil.itFokus) {
      if (fokusMatch(kontakt, f)) {
        score += 6; reasons.push(`Fokus: ${f}`)
      }
    }
  }
  if (suchprofil.itFokusSonstige) {
    const needles = suchprofil.itFokusSonstige.toLowerCase().split(/[,;]/).map(s => s.trim()).filter(Boolean)
    const haystack = `${kontakt.bietet || ''} ${kontakt.branche || ''} ${kontakt.beschreibung || ''}`.toLowerCase()
    for (const n of needles) {
      if (haystack.includes(n)) { score += 4; reasons.push(`„${n}"`) }
    }
  }

  // ---- Kunde-Bonus ----
  if (kontakt.istKunde) { score += 5; reasons.push('Bestandskunde') }

  score = Math.max(0, Math.min(100, score))
  return { score, reasons, dislikes, ausgeschlossen }
}

async function refreshList() {
  loading.value = true
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    const suchprofil = t.suchprofilJson ? JSON.parse(t.suchprofilJson) : {}
    try { manuellAdded.value = JSON.parse(t.longListManuellJson || '[]') } catch { manuellAdded.value = [] }
    try { fuerKaeuferIds.value = JSON.parse(t.fuerKaeuferIdsJson || '[]') } catch { fuerKaeuferIds.value = [] }
    try { kaeuferFeedback.value = JSON.parse(t.kaeuferFeedbackJson || '{}') } catch { kaeuferFeedback.value = {} }

    // 1. CRM-Kontakte matchen
    const kontakte = await getKontakte()
    allKontakte.value = kontakte || []
    const crmMatches = (kontakte || []).map(k => {
      const { score, reasons, dislikes, ausgeschlossen } = scoreFor(k, suchprofil)
      return { ...k, id: k.RowKey || k.id, score, matchGruende: reasons, ablehnGruende: dislikes, ausgeschlossen, _quelle: 'crm' }
    })

    // 2. Eigene Verkaufs-Mandate (interne Targets) matchen – starke Prioritaet!
    const targets = await getTargets()
    const internalMatches = (targets || [])
      .filter(tt => tt.RowKey !== props.targetId && !/kauf|investor/i.test(tt.projekttyp || ''))
      .map(tt => {
        // Target-Felder auf Kontakt-Schema abbilden
        const asKontakt = {
          firma: tt.verkaueferName || tt.firma || tt.mbNr,
          plz: tt.plz, ort: tt.region || tt.ort,
          mitarbeiter: tt.mitarbeiter, umsatz: tt.umsatz,
          bietet: tt.branche, istKunde: true,  // intern bekanntes Target
        }
        const { score, reasons, dislikes, ausgeschlossen } = scoreFor(asKontakt, suchprofil)
        return {
          id: 'target-' + tt.RowKey,
          firma: asKontakt.firma,
          plz: asKontakt.plz, ort: asKontakt.ort,
          mitarbeiter: asKontakt.mitarbeiter, umsatz: asKontakt.umsatz,
          score: Math.min(100, score + 15),  // Bonus fuer interne Targets, max 100
          matchGruende: ['Interner Target ' + tt.mbNr, ...reasons],
          ablehnGruende: dislikes,
          ausgeschlossen,
          istInternesTarget: true,
          mbNr: tt.mbNr,
          targetRowKey: tt.RowKey,
          _quelle: 'target',
        }
      })

    const manuellSet = new Set(manuellAdded.value)
    const profilLeerVal = !hasSuchprofil(suchprofil)
    profilLeer.value = profilLeerVal
    // Ausschluss-Regionen fliegen IMMER raus (außer manuell hinzugefügt)
    let all = [...internalMatches, ...crmMatches]
      .filter(k => !k.ausgeschlossen || manuellSet.has(k.id))

    if (profilLeerVal) {
      // Kein Suchprofil → einfach nach PLZ aufsteigend sortieren
      all = all.sort((a, b) => (a.plz || '99999').localeCompare(b.plz || '99999'))
    } else {
      // Score-Filter + Sortierung nach Score absteigend
      all = all
        .filter(k => k.score >= 30 || manuellSet.has(k.id))
        .sort((a, b) => b.score - a.score)
    }
    items.value = all
    try { decisions.value = JSON.parse(t.longListDecisionsJson || '{}') } catch { decisions.value = {} }

    // Stale-Cleanup: Markierungen für nicht mehr existierende Kontakte (z.B. aus
    // Dedup-Aktionen) automatisch wegräumen. Sonst zählen die Counter falsch.
    const validIds = new Set(items.value.map(k => k.id))
    const cleanDecisions = {}
    let removedDec = 0
    for (const [id, v] of Object.entries(decisions.value)) {
      if (validIds.has(id)) cleanDecisions[id] = v
      else removedDec++
    }
    const cleanFuerKaeufer = fuerKaeuferIds.value.filter(id => validIds.has(id))
    const removedFK = fuerKaeuferIds.value.length - cleanFuerKaeufer.length
    if (removedDec || removedFK) {
      decisions.value = cleanDecisions
      fuerKaeuferIds.value = cleanFuerKaeufer
      try {
        await authFetch('/target-update', { method: 'POST', data: {
          id: props.targetId,
          longListDecisionsJson: JSON.stringify(cleanDecisions),
          fuerKaeuferIdsJson: JSON.stringify(cleanFuerKaeufer),
        }})
        console.log(`[LongList] Stale-Cleanup: ${removedDec} Entscheidungen, ${removedFK} Freigaben entfernt`)
      } catch (e) { console.error('cleanup failed', e) }
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function setStatus(k, status) {
  const newDecisions = { ...decisions.value, [k.id]: status }
  decisions.value = newDecisions
  try {
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, longListDecisionsJson: JSON.stringify(newDecisions) } })
  } catch (e) { console.error(e) }
}

onMounted(refreshList)
</script>
