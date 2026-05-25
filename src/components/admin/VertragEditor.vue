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
          <button @click="downloadDocx" class="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 flex items-center gap-2">
            <Download class="w-4 h-4" /> Vorschau (PDF)
          </button>
          <button @click="zurSignaturSenden" :disabled="!form.auftraggeberFirma || sending" class="ml-auto px-4 py-2.5 bg-[#097e92] text-white rounded-xl text-sm font-semibold hover:bg-[#0a9aaf] flex items-center gap-2 disabled:opacity-50">
            <Send class="w-4 h-4" />
            {{ sending ? 'Wird gesendet…' : 'An Target zur Signatur senden' }}
          </button>
        </div>
        <p v-if="vertrag?.signiertAm" class="text-xs text-green-700 mt-3 flex items-center gap-1.5">
          <CheckCircle2 class="w-4 h-4" /> Signiert am {{ formatDate(vertrag.signiertAm) }} durch {{ vertrag.signiertVon }}
        </p>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Check, X, FileEdit, Save, Download, Send, CheckCircle2, Clock, FileText, AlertTriangle } from '@lucide/vue'
import { authFetch } from '../../api.js'

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
  if (vertrag.value.signiertAm) return 'Signiert'
  if (vertrag.value.gesendetAm) return 'An Target gesendet'
  return 'Entwurf'
})
const statusIcon = computed(() => {
  if (vertrag.value?.signiertAm) return CheckCircle2
  if (vertrag.value?.gesendetAm) return Clock
  return FileText
})
const statusBadgeClass = computed(() => {
  if (vertrag.value?.signiertAm) return 'bg-green-100 text-green-700'
  if (vertrag.value?.gesendetAm) return 'bg-yellow-100 text-yellow-700'
  return 'bg-gray-100 text-gray-500'
})

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

async function downloadDocx() {
  if (!props.targetId || !variante.value) return
  try {
    const r = await fetch(`${import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'}/vertrag-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (sessionStorage.getItem('msalToken') || sessionStorage.getItem('partnerJwt') || '') },
      body: JSON.stringify({ targetId: props.targetId, variante: variante.value, form: form.value })
    })
    if (!r.ok) throw new Error('PDF-Erstellung fehlgeschlagen')
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `Mandatsvertrag_${form.value.auftraggeberFirma}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) { alert('Vorschau noch nicht verfügbar – Backend-Endpoint folgt im nächsten Schritt.') }
}

async function zurSignaturSenden() {
  if (!confirm('Vertrag jetzt an den Target zur Signatur senden? Der Target erhält eine E-Mail mit einem Signier-Link.')) return
  sending.value = true
  try {
    await authFetch('/vertrag-zur-signatur', { method: 'POST', data: { targetId: props.targetId, variante: variante.value, form: form.value } })
    vertrag.value = { ...vertrag.value, gesendetAm: new Date().toISOString() }
    await speichern()
    alert('Vertrag wurde an den Target gesendet.')
  } catch (e) { alert('Versand noch nicht verfügbar – Signatur-Endpoint folgt im nächsten Schritt.') }
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
