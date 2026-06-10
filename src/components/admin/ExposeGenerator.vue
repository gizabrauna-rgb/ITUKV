<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Unternehmensexposé</h3>
        <p class="text-xs text-gray-500">Anonymisiertes Exposé · strukturiert in Sektionen · PDF-Export</p>
      </div>
      <div class="flex gap-2">
        <button @click="generierenAusFragebogen" :disabled="!hasFragebogen" class="flex items-center gap-2 px-3 py-2 bg-amber-500 text-white rounded-xl text-sm font-medium hover:bg-amber-600 disabled:opacity-50">
          <Sparkles class="w-4 h-4" /> Aus Fragebogen vorbefüllen
        </button>
        <button @click="openPreview" :disabled="previewLoading" class="flex items-center gap-2 px-3 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8] disabled:opacity-50">
          <FileText class="w-4 h-4" /> {{ previewLoading ? 'Lade…' : 'Vorschau (PDF)' }}
        </button>
      </div>
    </div>

    <!-- Status-Workflow -->
    <div class="bg-white rounded-xl border border-gray-100 p-4 mb-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div :class="['w-3 h-3 rounded-full', statusColor]"></div>
        <span class="font-medium text-sm">Status: {{ statusLabel }}</span>
      </div>
      <div class="flex gap-2">
        <button v-if="exposeStatus !== 'in_review'" @click="setStatus('in_review')" class="text-xs px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50">Intern prüfen</button>
        <button v-if="exposeStatus !== 'awaiting_approval'" @click="setStatus('awaiting_approval')" class="text-xs px-3 py-1.5 border border-amber-200 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100">An Kunde zur Freigabe</button>
        <button v-if="exposeStatus !== 'approved'" @click="setStatus('approved')" class="text-xs px-3 py-1.5 border border-green-200 bg-green-50 text-green-700 rounded-lg hover:bg-green-100">Freigegeben</button>
      </div>
    </div>

    <!-- Header-Bereich -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <h4 class="font-semibold text-gray-800 text-sm mb-3">Kopfbereich</h4>
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label class="lbl">Projektnummer</label>
          <input v-model="data.mbNr" readonly class="input bg-gray-50 font-mono" />
        </div>
        <div>
          <label class="lbl">Stand (Datum)</label>
          <input v-model="data.stand" @blur="save" type="date" class="input" />
        </div>
      </div>
      <div class="mb-3">
        <label class="lbl">Headline</label>
        <input v-model="data.headline" @blur="save" placeholder="z.B. IT-Dienstleister Systemhaus & Privatkunden bietet Übernahme..." class="input" />
      </div>
      <div>
        <label class="lbl">Sub-Headline</label>
        <input v-model="data.subheadline" @blur="save" placeholder="z.B. PLZ 91… · 15 Mitarbeiter · gegen Gebot" class="input" />
      </div>
    </div>

    <!-- Sektionen -->
    <div v-for="(sec, idx) in data.sektionen" :key="idx" class="bg-white rounded-xl border border-gray-100 p-5 mb-3">
      <div class="flex items-center justify-between mb-2">
        <h4 class="font-semibold text-gray-800 text-sm">{{ sec.label }}</h4>
      </div>
      <textarea v-model="sec.body" @blur="save" rows="6" :placeholder="placeholderFor(sec.label)" class="input resize-y"></textarea>
    </div>

    <!-- Finanzen (optional) -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-3">
      <h4 class="font-semibold text-gray-800 text-sm mb-3">Umsätze, Erträge, finanzielle Situation</h4>
      <textarea v-model="data.finanzen.einleitung" @blur="save" rows="3" placeholder="Einleitung zur Finanzsituation (frei)" class="input resize-y mb-3"></textarea>
      <p class="text-xs text-gray-500 mb-2">Optionale Finanz-Tabelle (z.B. mehrere Jahre):</p>
      <div class="flex gap-2 mb-2">
        <input v-model="data.finanzen.jahreInput" @blur="parseJahre" placeholder="Jahre (Komma-getrennt), z.B. 2023, 2024, 2025, Plan 2026" class="input flex-1 text-sm" />
        <button @click="addRow" class="px-3 py-2 bg-gray-100 rounded-lg text-xs whitespace-nowrap">+ Zeile</button>
      </div>
      <table v-if="data.finanzen.jahre?.length" class="w-full text-xs">
        <thead><tr>
          <th class="text-left py-1.5 w-48">Position</th>
          <th v-for="j in data.finanzen.jahre" :key="j" class="text-right py-1.5">{{ j }}</th>
          <th class="w-8"></th>
        </tr></thead>
        <tbody>
          <tr v-for="(row, ri) in data.finanzen.rows" :key="ri" class="border-t border-gray-100">
            <td class="py-1"><input v-model="row.label" @blur="save" placeholder="z.B. Umsatz" class="w-full px-1.5 py-1 border border-gray-200 rounded text-xs" /></td>
            <td v-for="(_, ji) in data.finanzen.jahre" :key="ji" class="py-1">
              <input v-model="row.werte[ji]" @blur="save" placeholder="0" class="w-full px-1.5 py-1 border border-gray-200 rounded text-xs text-right" />
            </td>
            <td><button @click="data.finanzen.rows.splice(ri, 1); save()" class="text-red-400 hover:text-red-600 p-1"><X class="w-3 h-3" /></button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Aufteilung der Geschäftsbereiche (Querformat-Anhang) -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-3">
      <div class="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h4 class="font-semibold text-gray-800 text-sm">Aufteilung der Geschäftsbereiche <span class="text-xs font-normal text-gray-500">(Querformat-Anhang, optional)</span></h4>
        <div class="flex gap-2 flex-wrap">
          <button @click="showPasteModal = true" class="px-3 py-1.5 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg text-xs whitespace-nowrap hover:bg-blue-100">
            📋 Aus Excel einfügen
          </button>
          <label class="px-3 py-1.5 bg-purple-50 text-purple-700 border border-purple-200 rounded-lg text-xs whitespace-nowrap hover:bg-purple-100 cursor-pointer">
            <span v-if="!pdfUploading">🤖 PDF hochladen (KI)</span>
            <span v-else>Liest PDF …</span>
            <input ref="pdfFileInput" type="file" accept="application/pdf" class="hidden" @change="onPdfUpload" />
          </label>
          <button @click="addAufteilungRow" class="px-3 py-1.5 bg-gray-100 rounded-lg text-xs whitespace-nowrap">+ Zeile</button>
        </div>
      </div>
      <div class="flex gap-2 mb-3">
        <input v-model="data.aufteilung.istLabel" @blur="save" placeholder="Spalten-Label IST (z.B. 2025)" class="input flex-1 text-sm" />
        <input v-model="data.aufteilung.planLabel" @blur="save" placeholder="Spalten-Label Plan (z.B. Plan 2026)" class="input flex-1 text-sm" />
      </div>
      <table v-if="data.aufteilung.rows?.length" class="w-full text-[11px]">
        <thead>
          <tr class="text-gray-500">
            <th class="text-left py-1 w-40">Position</th>
            <th class="text-center py-1" colspan="5">IST</th>
            <th class="text-center py-1" colspan="5">Plan</th>
            <th class="w-6"></th>
          </tr>
          <tr class="text-gray-400 text-[10px]">
            <th></th>
            <th class="py-1">Gesamt</th><th class="py-1">Anteil SH</th><th class="py-1">%</th><th class="py-1">Anteil PK</th><th class="py-1">%</th>
            <th class="py-1">Gesamt</th><th class="py-1">SH GmbH</th><th class="py-1">%</th><th class="py-1">PK GmbH</th><th class="py-1">%</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, ri) in data.aufteilung.rows" :key="ri" class="border-t border-gray-100">
            <td class="py-1">
              <input v-model="row.label" @blur="save" placeholder="Zeilenname" class="w-full px-1.5 py-1 border border-gray-200 rounded text-[11px]" />
              <div class="flex gap-1 mt-0.5">
                <label class="flex items-center gap-0.5 text-[9px] text-gray-400 cursor-pointer">
                  <input type="checkbox" v-model="row.istKategorie" @change="save" class="scale-75" />Kat.
                </label>
                <label class="flex items-center gap-0.5 text-[9px] text-gray-400 cursor-pointer">
                  <input type="checkbox" v-model="row.istSumme" @change="save" class="scale-75" />Summe
                </label>
              </div>
            </td>
            <td v-for="ji in 5" :key="'i'+ji" class="py-1">
              <input v-model="row.ist[ji-1]" @blur="save" placeholder="0" class="w-full px-1 py-0.5 border border-gray-200 rounded text-[11px] text-right" />
            </td>
            <td v-for="ji in 5" :key="'p'+ji" class="py-1">
              <input v-model="row.plan[ji-1]" @blur="save" placeholder="0" class="w-full px-1 py-0.5 border border-gray-200 rounded text-[11px] text-right" />
            </td>
            <td><button @click="data.aufteilung.rows.splice(ri, 1); save()" class="text-red-400 hover:text-red-600 p-0.5"><X class="w-3 h-3" /></button></td>
          </tr>
        </tbody>
      </table>
      <div class="mt-3">
        <label class="text-xs text-gray-500">Fußnoten (eine pro Zeile)</label>
        <textarea v-model="aufteilungFussnotenText" @blur="syncFussnoten" rows="2" placeholder="z.B. 1) Für 2026: Eigenes Büro für Systemhausteam …" class="input resize-y text-xs"></textarea>
      </div>
    </div>

    <!-- Excel-Paste Modal -->
    <div v-if="showPasteModal" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" @click.self="showPasteModal = false">
      <div class="bg-white rounded-2xl w-full max-w-2xl flex flex-col overflow-hidden shadow-2xl">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-100">
          <h3 class="font-bold text-gray-900">Aus Excel einfügen</h3>
          <button @click="showPasteModal = false" class="p-1.5 hover:bg-gray-100 rounded-lg"><X class="w-5 h-5 text-gray-500" /></button>
        </div>
        <div class="p-5">
          <p class="text-xs text-gray-600 mb-2">
            Markiere in Excel die Tabelle (Spalte „Position" + 10 Zahlen-Spalten) und kopiere mit <kbd class="px-1 bg-gray-100 rounded">Cmd+C</kbd>. Hier einfügen:
          </p>
          <textarea v-model="pasteText" rows="10" placeholder="Position	2025 Gesamt	Anteil SH	%	Anteil PK	%	Plan Gesamt	SH GmbH	%	PK GmbH	%
Umsatz Handel	1.540.729 €	197.772 €	13%	1.342.957 €	87%	955.007 €	171.042 €	18%	783.965 €	82%
..." class="w-full p-3 border-2 border-gray-200 rounded-lg text-xs font-mono"></textarea>
          <p class="text-[11px] text-gray-500 mt-2">
            💡 Tipp: Zeilen mit Text in der ersten Spalte und KEINEN Zahlen werden automatisch als <strong>Kategorie-Header</strong> erkannt. Zeilen mit „Summe", „Gesamt" oder „EBIT" im Label als <strong>Summen-Zeile</strong>.
          </p>
        </div>
        <div class="flex justify-end gap-2 px-5 py-3 border-t border-gray-100 bg-gray-50">
          <button @click="showPasteModal = false" class="px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
          <button @click="applyPaste" :disabled="!pasteText.trim()" class="px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium disabled:opacity-50">
            Übernehmen
          </button>
        </div>
      </div>
    </div>

    <p class="text-xs text-gray-400 text-center mt-4">Auto-Speichern beim Verlassen jedes Feldes.</p>

    <!-- PDF-Vorschau Modal -->
    <div v-if="previewUrl" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" @click.self="closePreview">
      <div class="bg-white rounded-2xl w-full max-w-4xl h-[90vh] flex flex-col overflow-hidden shadow-2xl">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-100">
          <h3 class="font-bold text-gray-900 flex items-center gap-2"><FileText class="w-5 h-5 text-[#0088ba]" /> Exposé-Vorschau</h3>
          <div class="flex items-center gap-2">
            <a :href="previewUrl" :download="`Expose_${data.mbNr || 'Entwurf'}.pdf`" class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">Herunterladen</a>
            <button @click="closePreview" class="p-1.5 hover:bg-gray-100 rounded-lg"><X class="w-5 h-5 text-gray-500" /></button>
          </div>
        </div>
        <iframe :src="previewUrl" class="flex-1 w-full" frameborder="0"></iframe>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Sparkles, FileText, X } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })
const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

const DEFAULT_SEKTIONEN = [
  { label: 'Unternehmen / Historie', body: '' },
  { label: 'Geschäftsfelder', body: '' },
  { label: 'Mitarbeiter & Management', body: '' },
  { label: 'Kunden und Kundenstruktur', body: '' },
  { label: 'Lieferanten und Kooperationspartner', body: '' },
  { label: 'Wettbewerber & Marketing', body: '' },
  { label: 'Transaktionsvorhaben und Verkaufsmotiv', body: '' },
]

const target = ref(null)
const data = ref({
  mbNr: '',
  stand: new Date().toISOString().slice(0, 10),
  headline: '',
  subheadline: '',
  sektionen: JSON.parse(JSON.stringify(DEFAULT_SEKTIONEN)),
  finanzen: { einleitung: '', jahreInput: '', jahre: [], rows: [] },
  aufteilung: { istLabel: '2025', planLabel: 'Plan 2026', rows: [], fussnoten: [] },
})
const aufteilungFussnotenText = ref('')
const exposeStatus = ref('draft')

const hasFragebogen = computed(() => !!target.value?.fragebogenJson)

const statusLabel = computed(() => ({ draft: 'Entwurf', in_review: 'Intern in Prüfung', awaiting_approval: 'Wartet auf Kundenfreigabe', approved: 'Freigegeben' }[exposeStatus.value] || 'Entwurf'))
const statusColor = computed(() => ({ draft: 'bg-gray-400', in_review: 'bg-blue-500', awaiting_approval: 'bg-amber-500', approved: 'bg-green-500' }[exposeStatus.value]))

function placeholderFor(label) {
  const m = {
    'Unternehmen / Historie': 'z.B. Sitz, Gründungsjahr, Mitarbeiterzahl, Geschäftsmodell-Highlights',
    'Geschäftsfelder': 'z.B. Systemhaus + Privatkundengeschäft, jeweils mit Umsatzanteilen',
    'Mitarbeiter & Management': 'z.B. Team-Aufteilung, Management-Zeitanteile, Eigenverantwortung, Wissens-Transfer',
    'Kunden und Kundenstruktur': 'z.B. Anzahl Bestandskunden, Vertragsverteilung, Klumpenrisiko',
    'Lieferanten und Kooperationspartner': 'z.B. Hauptlieferanten, technologische Schwerpunkte',
    'Wettbewerber & Marketing': 'z.B. Marktposition, Marketing-Mix',
    'Transaktionsvorhaben und Verkaufsmotiv': 'z.B. Vollverkauf vs. Teilverkauf, Nachfolge-Hintergrund',
  }
  return m[label] || ''
}

function addRow() {
  data.value.finanzen.rows.push({ label: '', werte: (data.value.finanzen.jahre || []).map(() => '') })
}

function addAufteilungRow() {
  if (!data.value.aufteilung) data.value.aufteilung = { istLabel: '2025', planLabel: 'Plan 2026', rows: [], fussnoten: [] }
  data.value.aufteilung.rows.push({ label: '', istKategorie: false, istSumme: false, ist: ['','','','',''], plan: ['','','','',''] })
  save()
}
function syncFussnoten() {
  if (!data.value.aufteilung) data.value.aufteilung = { istLabel: '2025', planLabel: 'Plan 2026', rows: [], fussnoten: [] }
  data.value.aufteilung.fussnoten = (aufteilungFussnotenText.value || '').split('\n').map(s => s.trim()).filter(Boolean)
  save()
}

// ===== Excel-Paste =====
const showPasteModal = ref(false)
const pasteText = ref('')
function cleanNum(s) {
  if (s == null) return ''
  // Entferne: Tausenderpunkte, Euro-Zeichen, Leerzeichen, Prozentzeichen. Komma → Punkt.
  return String(s).trim().replace(/ /g, ' ').replace(/[€\s]/g, '').replace(/\.(?=\d{3}(\D|$))/g, '').replace(/,/g, '.').replace(/%/g, '')
}
function isNumericCell(s) {
  if (!s || !s.trim()) return false
  const cleaned = cleanNum(s)
  return /^-?\d+(\.\d+)?$/.test(cleaned)
}
function applyPaste() {
  const txt = pasteText.value || ''
  const lines = txt.split(/\r?\n/).map(l => l.trim()).filter(Boolean)
  if (!lines.length) { showPasteModal.value = false; return }
  if (!data.value.aufteilung) data.value.aufteilung = { istLabel: '2025', planLabel: 'Plan 2026', rows: [], fussnoten: [] }
  const newRows = []
  for (const line of lines) {
    const cells = line.split('\t').map(c => c.trim())
    if (!cells.length) continue
    const label = cells[0] || ''
    // Header-Zeilen ueberspringen (z.B. "Position 2025 Anteil ...")
    if (/^position$/i.test(label) && cells.slice(1).every(c => !isNumericCell(c))) continue
    // Numbers: nimm naechste 10 Zellen
    const nums = cells.slice(1, 11)
    const allEmpty = nums.every(c => !c)
    const ist = []; const plan = []
    for (let i = 0; i < 5; i++) ist.push(cleanNum(nums[i] || ''))
    for (let i = 0; i < 5; i++) plan.push(cleanNum(nums[5 + i] || ''))
    const lower = label.toLowerCase()
    const istSumme = /^(jahresumsatz|summe|gesamt|ebit|total)/i.test(label) || lower.includes('gesamt')
    const istKategorie = allEmpty || (!ist.some(Boolean) && !plan.some(Boolean) && !istSumme)
    newRows.push({ label, istKategorie, istSumme: istSumme && !istKategorie, ist, plan })
  }
  if (newRows.length) {
    if (confirm(`${newRows.length} Zeilen erkannt. Bestehende Zeilen ersetzen?`)) {
      data.value.aufteilung.rows = newRows
    } else {
      data.value.aufteilung.rows.push(...newRows)
    }
    save()
  }
  pasteText.value = ''
  showPasteModal.value = false
}

// ===== PDF-Upload mit KI =====
const pdfUploading = ref(false)
const pdfFileInput = ref(null)
async function onPdfUpload(ev) {
  const file = ev.target.files?.[0]
  if (!file) return
  pdfUploading.value = true
  try {
    // Datei als Base64 senden (umgeht Multipart-Komplikationen)
    const buf = await file.arrayBuffer()
    const b64 = btoa(new Uint8Array(buf).reduce((s, b) => s + String.fromCharCode(b), ''))
    const r = await authFetch('/aufteilung-parse-pdf', { method: 'POST', data: { fileBase64: b64 } })
    if (!r.rows?.length) { toast.warn('Keine Tabelle erkannt im PDF.'); return }
    if (!data.value.aufteilung) data.value.aufteilung = { istLabel: '2025', planLabel: 'Plan 2026', rows: [], fussnoten: [] }
    const replace = data.value.aufteilung.rows.length === 0 || confirm(`KI hat ${r.rows.length} Zeilen erkannt. Bestehende ersetzen?`)
    if (replace) {
      data.value.aufteilung.rows = r.rows
      if (r.istLabel) data.value.aufteilung.istLabel = r.istLabel
      if (r.planLabel) data.value.aufteilung.planLabel = r.planLabel
      if (r.fussnoten?.length) {
        data.value.aufteilung.fussnoten = r.fussnoten
        aufteilungFussnotenText.value = r.fussnoten.join('\n')
      }
    } else {
      data.value.aufteilung.rows.push(...r.rows)
    }
    save()
    toast.success(`${r.rows.length} Zeilen aus PDF übernommen.`)
  } catch (e) {
    toast.error('PDF-Auswertung fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally {
    pdfUploading.value = false
    if (pdfFileInput.value) pdfFileInput.value.value = ''
  }
}

function parseJahre() {
  const arr = (data.value.finanzen.jahreInput || '').split(/[,;]/).map(s => s.trim()).filter(Boolean)
  data.value.finanzen.jahre = arr
  for (const r of data.value.finanzen.rows) {
    while (r.werte.length < arr.length) r.werte.push('')
    r.werte.length = arr.length
  }
  save()
}

async function generierenAusFragebogen() {
  if (!hasFragebogen.value) return
  try {
    const fb = JSON.parse(target.value.fragebogenJson)
    const t = target.value
    const ma = ['technikVollzeit','vertriebVollzeit','innendienstVollzeit'].reduce((s, k) => s + (parseInt(fb.personal?.[k]) || 0), 0)
    data.value.headline = data.value.headline || `${fb.branchenschwerpunkte || 'IT-Systemhaus'} bietet Übernahme · ${t.region || ''}`
    data.value.subheadline = data.value.subheadline || `PLZ ${(t.plz || '').slice(0,2)}… · ${ma || '?'} Mitarbeiter · gegen Gebot`
    data.value.sektionen[0].body ||= `Sitz: PLZ-Region ${(t.plz || '').slice(0,2)}xxx. Gründungsjahr: ${fb.gruendungsjahr || 'n.a.'}. Rechtsform: ${fb.gesellschaftsform || 'n.a.'}. Aktuelles Team: ${ma || '?'} Mitarbeiter.`
    data.value.sektionen[1].body ||= `Schwerpunkt-Lösungen: ${Object.keys(fb.loesungen || {}).join(', ') || fb.branchenschwerpunkte || 'n.a.'}`
    data.value.sektionen[2].body ||= `Technik: ${fb.personal?.technikVollzeit || 0} Vollzeit + ${fb.personal?.technikAzubis || 0} Azubis. Vertrieb: ${fb.personal?.vertriebVollzeit || 0} Vollzeit. Innendienst: ${fb.personal?.innendienstVollzeit || 0} Vollzeit.`
    data.value.sektionen[3].body ||= `${fb.aktiveGeschaeftskunden || '?'} aktive Geschäftskunden. ${fb.privatkundenAnteil ? 'Privatkundenanteil: ' + fb.privatkundenAnteil + '%.' : ''} Branchen: ${fb.branchenschwerpunkte || 'gemischt'}.`
    data.value.sektionen[5].body ||= `Wachstumspotenzial: ${fb.wachstumspotenzial || ''}. Wettbewerb: ${fb.wettbewerbssituation || ''}`
    const gruende = Object.keys(fb.verkaufsgruende || {}).filter(k => fb.verkaufsgruende[k])
    data.value.sektionen[6].body ||= `Verkaufsgründe: ${gruende.join('; ') || 'siehe Mandat-Daten'}. Verfügbarkeit nach Übergabe: ${fb.uebergabeVerfuegbarkeit || 'n.a.'}.`
    save()
  } catch (e) { toast.error('Aus Fragebogen vorbefüllen fehlgeschlagen: ' + e.message) }
}

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, exposeJson: JSON.stringify({ ...data.value, status: exposeStatus.value }) } })
    } catch (e) { console.error(e) }
  }, 400)
}

async function setStatus(s) {
  const prev = exposeStatus.value
  exposeStatus.value = s
  await save()
  // Workflow-Notifizierung im Verlauf festhalten
  try {
    const targetData = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    const existing = targetData.kommunikationJson ? JSON.parse(targetData.kommunikationJson) : []
    let betreff = '', beschreibung = '', typ = 'notiz'
    if (s === 'awaiting_approval') {
      betreff = 'Exposé an Kunde zur Freigabe gesendet'
      beschreibung = 'Das Exposé wurde an den Verkäufer zur Freigabe gesendet. Er sieht es jetzt in seinem Portal unter „Mein Exposé".'
      typ = 'wichtig'
    } else if (s === 'in_review') {
      betreff = 'Exposé in interne Prüfung gesetzt'
      beschreibung = 'Das Exposé wird intern noch geprüft.'
    } else if (s === 'approved') {
      betreff = 'Exposé freigegeben (manuell durch mibeca)'
      beschreibung = 'Status wurde manuell auf freigegeben gesetzt.'
      typ = 'wichtig'
    }
    if (betreff) {
      existing.unshift({
        id: 'k' + Date.now(), typ, datum: new Date().toISOString(),
        autor: sessionStorage.getItem('userName') || 'mibeca',
        betreff, beschreibung, beteiligte: 'mibeca → Verkäufer',
      })
      await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, kommunikationJson: JSON.stringify(existing) } })
    }
    toast.success(`Status: ${statusLabel.value}`)
  } catch (e) { console.error(e) }
}

// Preview
const previewUrl = ref(null)
const previewLoading = ref(false)
async function openPreview() {
  previewLoading.value = true
  try {
    const token = sessionStorage.getItem('customerJwt') || sessionStorage.getItem('msalToken') || ''
    const r = await fetch(`${apiBase}/expose-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      body: JSON.stringify(data.value),
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    const ab = await r.arrayBuffer()
    previewUrl.value = URL.createObjectURL(new Blob([ab], { type: 'application/pdf' }))
  } catch (e) { toast.error('Vorschau fehlgeschlagen: ' + e.message) }
  finally { previewLoading.value = false }
}
function closePreview() { if (previewUrl.value) URL.revokeObjectURL(previewUrl.value); previewUrl.value = null }

onMounted(async () => {
  if (!props.targetId) return
  try {
    target.value = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (target.value?.mbNr) data.value.mbNr = target.value.mbNr
    if (target.value?.exposeJson) {
      try {
        const e = JSON.parse(target.value.exposeJson)
        // Merge: behalte default-sektionen wenn nicht vorhanden
        if (e.headline !== undefined) data.value.headline = e.headline
        if (e.subheadline !== undefined) data.value.subheadline = e.subheadline
        if (e.stand) data.value.stand = e.stand
        if (Array.isArray(e.sektionen) && e.sektionen.length) data.value.sektionen = e.sektionen
        if (e.finanzen) Object.assign(data.value.finanzen, e.finanzen)
        if (e.aufteilung) {
          data.value.aufteilung = {
            istLabel: e.aufteilung.istLabel || '2025',
            planLabel: e.aufteilung.planLabel || 'Plan 2026',
            rows: Array.isArray(e.aufteilung.rows) ? e.aufteilung.rows : [],
            fussnoten: Array.isArray(e.aufteilung.fussnoten) ? e.aufteilung.fussnoten : [],
          }
          aufteilungFussnotenText.value = (data.value.aufteilung.fussnoten || []).join('\n')
        }
        if (e.status) exposeStatus.value = e.status
      } catch {}
    }
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border-2 border-gray-200 bg-white rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
.lbl { @apply block text-xs font-medium text-gray-600 mb-1; }
</style>
