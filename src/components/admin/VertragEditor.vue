<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Mandatsvertrag</h2>
        <p class="text-sm text-gray-500 mt-1">Beratungs- und Dienstleistungsvertrag mibeca ↔ Verkäufer</p>
      </div>
      <div v-if="target" class="flex items-center gap-2">
        <span :class="statusBadgeClass" class="text-xs font-medium px-3 py-1.5 rounded-full flex items-center gap-1.5">
          <component :is="statusIcon" class="w-3.5 h-3.5" />
          {{ statusLabel }}
        </span>
      </div>
    </div>

    <!-- Mandat Ja/Nein -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <div class="flex items-start gap-4">
        <div class="flex-1">
          <h3 class="font-semibold text-gray-800 text-sm mb-1">Mandat angenommen?</h3>
          <p class="text-xs text-gray-500">Nur wenn das Mandat angenommen wird, wird ein Vertrag erstellt.</p>
        </div>
        <div class="flex gap-2">
          <button @click="setMandat(true)"
            :class="['px-4 py-2 rounded-xl text-sm font-medium transition-colors',
              mandatAngenommen === true ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200']">
            <Check class="w-4 h-4 inline" /> Ja, übernehmen
          </button>
          <button @click="setMandat(false)"
            :class="['px-4 py-2 rounded-xl text-sm font-medium transition-colors',
              mandatAngenommen === false ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200']">
            <X class="w-4 h-4 inline" /> Nein
          </button>
        </div>
      </div>
    </div>

    <div v-if="mandatAngenommen === true">
      <!-- Variante Auswahl -->
      <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
        <h3 class="font-semibold text-gray-800 text-sm mb-3">Vertrags-Variante wählen</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button v-for="v in varianten" :key="v.key" @click="selectVariante(v.key)"
            :class="['p-4 rounded-xl border-2 text-left transition-all',
              variante === v.key ? 'border-[#097e92] bg-[#097e92]/5' : 'border-gray-200 hover:border-gray-300']">
            <div class="font-semibold text-sm text-gray-800 mb-1">{{ v.titel }}</div>
            <div class="text-xs text-gray-500">{{ v.beschreibung }}</div>
            <div class="text-xs text-[#097e92] mt-2 font-semibold">{{ v.preis }}</div>
          </button>
        </div>
      </div>

      <!-- Vertrags-Daten Formular -->
      <div v-if="variante" class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
        <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
          <FileEdit class="w-4 h-4 text-[#097e92]" />
          Vertrags-Daten (alle Felder editierbar)
        </h3>
        <p class="text-xs text-gray-500 mb-4">Die Daten werden automatisch aus den Stammdaten vorbefüllt. Du kannst alles anpassen.</p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label class="field-label">Auftraggeber (Firma)</label>
            <input v-model="form.auftraggeberFirma" class="input" />
          </div>
          <div>
            <label class="field-label">Straße</label>
            <input v-model="form.auftraggeberStrasse" class="input" />
          </div>
          <div>
            <label class="field-label">PLZ / Ort</label>
            <input v-model="form.auftraggeberPlzOrt" class="input" />
          </div>
          <div>
            <label class="field-label">Geschäftsführer Auftraggeber</label>
            <input v-model="form.auftraggeberGf" class="input" />
          </div>
          <div>
            <label class="field-label">Verkaufsobjekt</label>
            <input v-model="form.verkaufsobjekt" class="input" />
          </div>
          <div>
            <label class="field-label">Berater (mibeca-seitig)</label>
            <input v-model="form.berater" class="input" />
          </div>
          <div>
            <label class="field-label">Datum</label>
            <input v-model="form.datum" type="date" class="input" />
          </div>
        </div>

        <h4 class="font-semibold text-gray-700 text-sm mt-6 mb-3">§5 Vergütung</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-if="variante === 'mit_uve'" class="md:col-span-2">
            <label class="field-label">Eröffnungsvergütung Zahlungsmodus</label>
            <select v-model="form.eroeffnungsModus" class="input">
              <option value="einmalig">Einmalig 10.000 € netto</option>
              <option value="raten">6 Monatsraten zu je 1.800 € netto</option>
            </select>
          </div>
          <div>
            <label class="field-label">Eröffnungsvergütung (€)</label>
            <input v-model.number="form.eroeffnungsBetrag" type="number" class="input" />
          </div>
          <div>
            <label class="field-label">Honorar Jenny Kaplan (€/h)</label>
            <input v-model.number="form.honorarJennyStunde" type="number" class="input" />
          </div>
          <div>
            <label class="field-label">Honorar Jenny Kaplan (€/Tag vor Ort)</label>
            <input v-model.number="form.honorarJennyTag" type="number" class="input" />
          </div>
          <div>
            <label class="field-label">Honorar Mike Bergmann (€/h)</label>
            <input v-model.number="form.honorarMikeStunde" type="number" class="input" />
          </div>
          <div>
            <label class="field-label">Honorar Mike Bergmann (€/Tag vor Ort)</label>
            <input v-model.number="form.honorarMikeTag" type="number" class="input" />
          </div>
          <div>
            <label class="field-label">Honorar Team (€/h)</label>
            <input v-model.number="form.honorarTeamStunde" type="number" class="input" />
          </div>
          <div>
            <label class="field-label">Honorar Team (€/Tag vor Ort)</label>
            <input v-model.number="form.honorarTeamTag" type="number" class="input" />
          </div>
          <div>
            <label class="field-label">Erfolgsvergütung (% des Transaktionsvolumens)</label>
            <input v-model.number="form.erfolgsProzent" type="number" step="0.5" class="input" />
          </div>
          <div>
            <label class="field-label">Vertragslaufzeit (Monate)</label>
            <input v-model.number="form.laufzeitMonate" type="number" class="input" />
          </div>
        </div>

        <h4 class="font-semibold text-gray-700 text-sm mt-6 mb-3">Notizen / Zusatzklauseln (optional)</h4>
        <textarea v-model="form.notizen" rows="3" placeholder="Zusätzliche Klauseln, Sondervereinbarungen…" class="input resize-y"></textarea>
      </div>

      <!-- Aktionen -->
      <div v-if="variante" class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
        <div class="flex flex-wrap gap-3">
          <button @click="speichern" :disabled="saving" class="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 flex items-center gap-2 disabled:opacity-50">
            <Save class="w-4 h-4" /> Entwurf speichern
          </button>
          <button @click="openPreview" :disabled="previewLoading" class="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 flex items-center gap-2 disabled:opacity-50">
            <FileText class="w-4 h-4" /> {{ previewLoading ? 'Lade Vorschau…' : 'Vorschau (PDF)' }}
          </button>
          <button v-if="!vertrag?.gegengezeichnetAm" @click="zurSignaturSenden" :disabled="!form.auftraggeberFirma || sending" class="ml-auto px-4 py-2.5 bg-[#097e92] text-white rounded-xl text-sm font-semibold hover:bg-[#0a9aaf] flex items-center gap-2 disabled:opacity-50">
            <Send class="w-4 h-4" />
            {{ sending ? 'Wird gesendet…' : (vertrag?.gesendetAm ? 'Erneut senden (mit aktuellen Daten)' : 'An Target zur Signatur senden') }}
          </button>
        </div>
        <p v-if="vertrag?.signiertAm && !vertrag?.gegengezeichnetAm" class="text-xs text-yellow-700 mt-3 flex items-center gap-1.5">
          <Clock class="w-4 h-4" /> Target hat am {{ formatDate(vertrag.signiertAm) }} unterschrieben ({{ vertrag.signiertVon }}). Wartet auf deine Gegenzeichnung unten.
        </p>
        <p v-if="vertrag?.gegengezeichnetAm" class="text-xs text-green-700 mt-3 flex items-center gap-1.5">
          <CheckCircle2 class="w-4 h-4" /> Final unterschrieben am {{ formatDate(vertrag.gegengezeichnetAm) }} durch {{ vertrag.gegengezeichnetVon }}.
        </p>
      </div>

      <!-- Gegenzeichnungs-Bereich (nur sichtbar wenn Target signiert hat) -->
      <div v-if="vertrag?.signiertAm && !vertrag?.gegengezeichnetAm" class="bg-yellow-50 border border-yellow-200 rounded-xl p-5 mb-4">
        <h3 class="font-semibold text-yellow-900 text-sm mb-2 flex items-center gap-2">
          <PenTool class="w-4 h-4" /> Jetzt gegenzeichnen
        </h3>
        <p class="text-xs text-yellow-800 mb-3">Zeichne hier deine Unterschrift. Sobald du gegenzeichnest, bekommt der Target eine Mail mit dem fertigen Vertrag.</p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Unterschrift (zeichnen)</label>
            <canvas ref="sigCanvas" width="500" height="160"
              @mousedown="startDraw" @mousemove="moveDraw" @mouseup="endDraw" @mouseleave="endDraw"
              @touchstart="startDraw" @touchmove="moveDraw" @touchend="endDraw"
              class="border-2 border-dashed border-yellow-300 rounded-xl bg-white w-full touch-none"
              style="cursor: crosshair"></canvas>
            <button @click="clearCanvas" class="text-xs text-gray-500 underline mt-1">Löschen / neu zeichnen</button>
          </div>
          <div>
            <label class="field-label">Dein Name (für Signatur)</label>
            <input v-model="adminSigName" placeholder="z.B. Jennifer Kaplan" class="input" />
            <p class="text-xs text-gray-500 mt-2">Mit der Gegenzeichnung erklärst du, den Vertrag stellvertretend für mibeca anzunehmen.</p>
            <button @click="countersign" :disabled="countersigning || !adminSigName"
              class="mt-3 w-full px-4 py-2.5 bg-[#097e92] text-white rounded-xl text-sm font-semibold hover:bg-[#0a9aaf] flex items-center justify-center gap-2 disabled:opacity-50">
              <PenTool class="w-4 h-4" />
              {{ countersigning ? 'Wird gegengezeichnet…' : 'Jetzt gegenzeichnen' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Download fuer finalen Vertrag (nach Gegenzeichnung) -->
      <div v-if="vertrag?.gegengezeichnetAm && vertrag?.signToken" class="bg-green-50 border border-green-200 rounded-xl p-5 mb-4 flex items-center gap-3">
        <CheckCircle2 class="w-6 h-6 text-green-600" />
        <div class="flex-1">
          <p class="text-sm font-semibold text-green-900">Vertrag ist final unterschrieben</p>
          <p class="text-xs text-green-700">Der Target kann sein Exemplar aus seinem Dashboard herunterladen.</p>
        </div>
        <a :href="`${apiBase}/sign-pdf?token=${vertrag.signToken}`" target="_blank" rel="noopener" class="px-4 py-2 bg-white border border-green-300 text-green-700 rounded-xl text-sm font-medium hover:bg-green-100 flex items-center gap-2">
          <Download class="w-4 h-4" /> Finalen Vertrag öffnen
        </a>
      </div>
    </div>

    <!-- Mandat abgelehnt -->
    <div v-if="mandatAngenommen === false" class="bg-amber-50 border border-amber-200 rounded-xl p-5">
      <div class="flex items-start gap-3">
        <AlertTriangle class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <h3 class="font-semibold text-amber-900 text-sm mb-1">Mandat nicht übernommen</h3>
          <p class="text-sm text-amber-800">Bitte trage in der Akte vor, warum das Mandat nicht angenommen wurde. Vertrauliche Unterlagen werden vernichtet bzw. zurückgegeben.</p>
          <textarea v-model="form.ablehnungsgrund" rows="3" placeholder="Grund der Ablehnung…" class="input mt-3 bg-white"></textarea>
          <button @click="speichern" class="mt-3 px-4 py-2 bg-amber-600 text-white rounded-xl text-sm font-medium hover:bg-amber-700">
            Speichern
          </button>
        </div>
      </div>
    </div>

    <!-- PDF-Vorschau Modal -->
    <div v-if="previewUrl" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" @click.self="closePreview">
      <div class="bg-white rounded-2xl w-full max-w-4xl h-[90vh] flex flex-col overflow-hidden shadow-2xl">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-100">
          <h3 class="font-bold text-gray-900 flex items-center gap-2">
            <FileText class="w-5 h-5 text-[#097e92]" /> Vertrags-Vorschau
          </h3>
          <div class="flex items-center gap-2">
            <a :href="previewUrl" :download="`Mandatsvertrag_${form.auftraggeberFirma || 'Entwurf'}.pdf`" class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-1.5">
              <Download class="w-3.5 h-3.5" /> Herunterladen
            </a>
            <button @click="closePreview" class="p-1.5 hover:bg-gray-100 rounded-lg">
              <X class="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>
        <iframe :src="previewUrl" class="flex-1 w-full" frameborder="0"></iframe>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Check, X, FileEdit, Save, Download, Send, CheckCircle2, Clock, FileText, AlertTriangle, PenTool } from '@lucide/vue'
import { authFetch } from '../../api.js'

const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

const props = defineProps({ targetId: String })

const target = ref(null)
const vertrag = ref(null)
const mandatAngenommen = ref(null)
const variante = ref(null)
const saving = ref(false)
const sending = ref(false)

const varianten = [
  { key: 'standard', titel: 'Standard', beschreibung: 'Kunde ohne UVE, kommt frisch zu mibeca', preis: 'Eröffnung: 4.950 €' },
  { key: 'mit_uve', titel: 'Mit UVE', beschreibung: 'UVE-Coaching wird im Rahmen des Mandats erstellt', preis: 'Eröffnung: 10.000 € oder 6× 1.800 €' },
  { key: 'vorhandenes_uve', titel: 'Vorhandenes UVE', beschreibung: 'Kunde hat UVE bereits abgeschlossen und bezahlt', preis: 'Eröffnung: 0 € (statt 3.490 €)' },
]

const form = ref({
  auftraggeberFirma: '', auftraggeberStrasse: '', auftraggeberPlzOrt: '', auftraggeberGf: '',
  verkaufsobjekt: '', berater: 'Jennifer Kaplan', datum: new Date().toISOString().slice(0,10),
  eroeffnungsModus: 'einmalig', eroeffnungsBetrag: 4950,
  honorarJennyStunde: 250, honorarJennyTag: 2990,
  honorarMikeStunde: 250, honorarMikeTag: 2990,
  honorarTeamStunde: 150, honorarTeamTag: 1500,
  erfolgsProzent: 5, laufzeitMonate: 12,
  notizen: '', ablehnungsgrund: '',
})

const statusLabel = computed(() => {
  if (!vertrag.value) return 'Entwurf'
  if (vertrag.value.gegengezeichnetAm) return 'Vollständig unterschrieben'
  if (vertrag.value.signiertAm) return 'Target hat unterschrieben'
  if (vertrag.value.gesendetAm) return 'An Target gesendet'
  return 'Entwurf'
})
const statusIcon = computed(() => {
  if (vertrag.value?.gegengezeichnetAm) return CheckCircle2
  if (vertrag.value?.signiertAm) return PenTool
  if (vertrag.value?.gesendetAm) return Clock
  return FileText
})
const statusBadgeClass = computed(() => {
  if (vertrag.value?.gegengezeichnetAm) return 'bg-green-100 text-green-700'
  if (vertrag.value?.signiertAm) return 'bg-yellow-100 text-yellow-700'
  if (vertrag.value?.gesendetAm) return 'bg-blue-100 text-blue-700'
  return 'bg-gray-100 text-gray-500'
})

// Canvas-Signatur fuer Gegenzeichnung
const sigCanvas = ref(null)
const adminSigName = ref('')
const countersigning = ref(false)
let canvasDirty = false
let drawing = false
let lastPos = null

function pos(e) {
  const c = sigCanvas.value
  const r = c.getBoundingClientRect()
  const t = e.touches?.[0] || e
  return { x: (t.clientX - r.left) * (c.width / r.width),
           y: (t.clientY - r.top) * (c.height / r.height) }
}
function startDraw(e) { e.preventDefault(); drawing = true; canvasDirty = true; lastPos = pos(e) }
function moveDraw(e) {
  if (!drawing) return
  e.preventDefault()
  const p = pos(e); const ctx = sigCanvas.value.getContext('2d')
  ctx.strokeStyle = '#0A2F2F'; ctx.lineWidth = 2.2; ctx.lineCap = 'round'
  ctx.beginPath(); ctx.moveTo(lastPos.x, lastPos.y); ctx.lineTo(p.x, p.y); ctx.stroke()
  lastPos = p
}
function endDraw(e) { e?.preventDefault?.(); drawing = false }
function clearCanvas() {
  const c = sigCanvas.value; if (!c) return
  c.getContext('2d').clearRect(0, 0, c.width, c.height); canvasDirty = false
}

async function countersign() {
  if (!canvasDirty) { alert('Bitte zuerst deine Unterschrift zeichnen.'); return }
  if (!vertrag.value?.signId) { alert('Keine offene Signatur gefunden.'); return }
  countersigning.value = true
  try {
    const data = sigCanvas.value.toDataURL('image/png')
    await authFetch('/vertrag-countersign', { method: 'POST', data: {
      signId: vertrag.value.signId,
      signature_image: data,
      signature_name: adminSigName.value.trim(),
    }})
    await load()
    alert('Vertrag erfolgreich gegengezeichnet. Der Target wurde per Mail informiert.')
  } catch (e) { alert('Gegenzeichnung fehlgeschlagen: ' + (e?.response?.data?.error || e.message)) }
  finally { countersigning.value = false }
}

function setMandat(val) {
  mandatAngenommen.value = val
  speichern()
}

function selectVariante(key) {
  variante.value = key
  // Defaults je Variante setzen
  if (key === 'standard') { form.value.eroeffnungsBetrag = 4950; form.value.eroeffnungsModus = 'einmalig' }
  if (key === 'mit_uve') { form.value.eroeffnungsBetrag = 10000; form.value.eroeffnungsModus = 'einmalig'; form.value.honorarMikeStunde = 350; form.value.honorarMikeTag = 3990 }
  if (key === 'vorhandenes_uve') { form.value.eroeffnungsBetrag = 0; form.value.eroeffnungsModus = 'einmalig' }
}

async function load() {
  if (!props.targetId) return
  try {
    target.value = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    // Stammdaten vorbefüllen
    if (target.value) {
      form.value.auftraggeberFirma = form.value.auftraggeberFirma || target.value.verkaueferName || target.value.firma || ''
      form.value.verkaufsobjekt = form.value.verkaufsobjekt || target.value.firma || ''
    }
    if (target.value.vertragJson) {
      const v = JSON.parse(target.value.vertragJson)
      vertrag.value = v
      if (v.form) Object.assign(form.value, v.form)
      mandatAngenommen.value = v.mandatAngenommen ?? null
      variante.value = v.variante ?? null
    }
  } catch (e) { console.error(e) }
}
onMounted(load)

async function speichern() {
  if (!props.targetId) return
  saving.value = true
  try {
    const payload = {
      mandatAngenommen: mandatAngenommen.value,
      variante: variante.value,
      form: form.value,
      gesendetAm: vertrag.value?.gesendetAm || null,
      signiertAm: vertrag.value?.signiertAm || null,
      signiertVon: vertrag.value?.signiertVon || null,
      stand: new Date().toISOString(),
    }
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, vertragJson: JSON.stringify(payload) } })
    vertrag.value = payload
  } catch (e) { console.error(e); alert('Speichern fehlgeschlagen') }
  finally { saving.value = false }
}

function _backendError(e) {
  return e?.response?.data?.error || e?.message || 'Unbekannter Fehler'
}

const previewUrl = ref(null)
const previewLoading = ref(false)
async function openPreview() {
  if (!props.targetId || !variante.value) {
    alert('Bitte zuerst Variante wählen und speichern.')
    return
  }
  previewLoading.value = true
  try {
    const r = await fetch(`${import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'}/vertrag-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (sessionStorage.getItem('customerJwt') || sessionStorage.getItem('msalToken') || '') },
      body: JSON.stringify({ targetId: props.targetId, variante: variante.value, form: form.value })
    })
    if (!r.ok) {
      const d = await r.json().catch(()=>({}))
      throw new Error(d.error || `HTTP ${r.status}`)
    }
    const blob = await r.blob()
    // Alte URL freigeben
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = URL.createObjectURL(blob)
  } catch (e) { alert('PDF-Vorschau fehlgeschlagen: ' + _backendError(e)) }
  finally { previewLoading.value = false }
}
function closePreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = null
}

async function zurSignaturSenden() {
  const isResend = !!vertrag.value?.gesendetAm
  const msg = isResend
    ? 'Vertrag NEU versenden mit den aktuellen Daten? Der alte Sign-Link wird ungültig und der Target bekommt einen frischen Link per Mail.'
    : 'Vertrag jetzt an den Target zur Signatur senden? Der Target erhält eine E-Mail mit einem Signier-Link.'
  if (!confirm(msg)) return
  sending.value = true
  try {
    const r = await authFetch('/vertrag-zur-signatur', { method: 'POST', data: { targetId: props.targetId, variante: variante.value, form: form.value } })
    // Bei Neuversand: alte Unterschriften aufraeumen, neuer Stand = nur 'gesendet'
    vertrag.value = {
      ...vertrag.value,
      gesendetAm: new Date().toISOString(),
      signId: r?.signId,
      signToken: r?.token,
      signiertAm: null,
      signiertVon: null,
      gegengezeichnetAm: null,
      gegengezeichnetVon: null,
    }
    await speichern()
    alert(isResend ? 'Vertrag wurde erneut an den Target gesendet.' : 'Vertrag wurde an den Target gesendet.')
  } catch (e) { alert('Versand fehlgeschlagen: ' + _backendError(e)) }
  finally { sending.value = false }
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]; }
.field-label { @apply block text-xs font-medium text-gray-600 mb-1; }
</style>
