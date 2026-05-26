<template>
  <div>
    <div class="mb-5">
      <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
        <Trophy class="w-6 h-6 text-amber-500" /> Erfolgsmeldung & Presse
      </h2>
      <p class="text-sm text-gray-500 mt-1">Pressemitteilung nach erfolgreicher Transaktion. Erstellung via KI, Versand an Fachmedien.</p>
    </div>

    <!-- Freigabe-Checkliste -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
        <CheckCircle2 class="w-4 h-4 text-[#0088ba]" /> Voraussetzungen vor Presseversand
      </h3>
      <div class="space-y-2">
        <label class="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" v-model="freigabe.dealAbgeschlossen" @change="save" class="rounded text-[#0088ba]" />
          <span class="text-sm">Deal vertraglich abgeschlossen</span>
        </label>
        <label class="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" v-model="freigabe.maInformiert" @change="save" class="rounded text-[#0088ba]" />
          <span class="text-sm">Mitarbeiter wurden über den Verkauf informiert</span>
        </label>
        <label class="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" v-model="freigabe.kaeuferFreigabe" @change="save" class="rounded text-[#0088ba]" />
          <span class="text-sm">Käufer hat Pressemitteilung freigegeben</span>
        </label>
        <label class="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" v-model="freigabe.verkaeuferFreigabe" @change="save" class="rounded text-[#0088ba]" />
          <span class="text-sm">Verkäufer hat O-Töne freigegeben</span>
        </label>
      </div>
    </div>

    <!-- Deal-Daten -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
        <FileText class="w-4 h-4 text-[#0088ba]" /> Deal-Daten für KI-Generierung
      </h3>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-xs text-gray-600 mb-1 block">mibeca begleitete...</label>
          <select v-model="deal.seite" @change="save" class="input">
            <option>Verkäuferseite</option>
            <option>Käuferseite</option>
            <option>Beide Seiten</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-gray-600 mb-1 block">Branche / Schwerpunkt</label>
          <input v-model="deal.schwerpunkt" @blur="save" placeholder="z.B. IT-Systemhaus / MSP" class="input" />
        </div>
        <div>
          <label class="text-xs text-gray-600 mb-1 block">Käufer-Firma</label>
          <input v-model="deal.kaeuferFirma" @blur="save" class="input" />
        </div>
        <div>
          <label class="text-xs text-gray-600 mb-1 block">Käufer-Ort</label>
          <input v-model="deal.kaeuferOrt" @blur="save" class="input" />
        </div>
        <div>
          <label class="text-xs text-gray-600 mb-1 block">Verkäufer-Firma</label>
          <input v-model="deal.verkaeuferFirma" @blur="save" class="input" />
        </div>
        <div>
          <label class="text-xs text-gray-600 mb-1 block">Verkäufer-Ort</label>
          <input v-model="deal.verkaeuferOrt" @blur="save" class="input" />
        </div>
        <div class="col-span-2">
          <label class="text-xs text-gray-600 mb-1 block">Besonderheiten der Transaktion</label>
          <textarea v-model="deal.besonderheiten" @blur="save" rows="2" placeholder="z.B. Rekordzeit von 11 Tagen, langjährige Geschäftsbeziehung, ..." class="input resize-y"></textarea>
        </div>
        <div class="col-span-2">
          <label class="text-xs text-gray-600 mb-1 block">Synergien nach Transaktion</label>
          <textarea v-model="deal.synergien" @blur="save" rows="2" placeholder="z.B. Standort-Erweiterung Hamburg, Tech-Know-how, Cross-Selling-Potenzial, ..." class="input resize-y"></textarea>
        </div>
      </div>
      <button @click="generieren" :disabled="generating" class="mt-4 w-full px-4 py-2.5 bg-amber-500 text-white rounded-xl text-sm font-semibold hover:bg-amber-600 flex items-center justify-center gap-2 disabled:opacity-50">
        <Sparkles class="w-4 h-4" />
        {{ generating ? 'KI generiert Pressetext...' : (text ? 'Pressetext neu generieren' : 'Pressetext per KI generieren') }}
      </button>
    </div>

    <!-- Pressetext -->
    <div v-if="text" class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
        <FileText class="w-4 h-4 text-[#0088ba]" /> Pressetext (editierbar)
      </h3>
      <textarea v-model="text" @blur="save" rows="20" class="input font-mono text-sm resize-y"></textarea>
      <p class="text-xs text-gray-400 mt-2">Wörter: {{ text.split(/\s+/).filter(Boolean).length }} (Ziel: max. 450)</p>
    </div>

    <!-- Kunden-Freigabe -->
    <div v-if="text" class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
        <UserCheck class="w-4 h-4 text-[#0088ba]" /> Kunden-Freigabe (optional)
      </h3>
      <p class="text-xs text-gray-500 mb-3">Schicke den Pressetext erst zum Kunden zur Freigabe / Kommentar. <strong>Du kannst aber auch direkt versenden, falls keine Freigabe nötig ist.</strong></p>
      <!-- Status-Banner -->
      <div v-if="freigabeStatus === 'pending'" class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-800 mb-3 flex items-center gap-2">
        <Clock class="w-4 h-4" /> Wartet auf Antwort des Kunden seit {{ formatDate(freigabeAngefragtAm) }}
      </div>
      <div v-else-if="freigabeStatus === 'freigegeben'" class="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800 mb-3 flex items-center gap-2">
        <CheckCircle2 class="w-4 h-4" /> Kunde hat freigegeben am {{ formatDate(freigabeAm) }}
      </div>
      <div v-else-if="freigabeStatus === 'aenderung_gewuenscht'" class="bg-orange-50 border border-orange-200 rounded-lg p-3 text-sm text-orange-800 mb-3">
        <div class="flex items-center gap-2 font-medium mb-1"><AlertCircle class="w-4 h-4" /> Kunde wünscht Änderungen ({{ formatDate(freigabeAm) }})</div>
        <p v-if="freigabeKommentar" class="text-xs ml-6 mt-1 italic">„{{ freigabeKommentar }}"</p>
      </div>
      <button @click="zurFreigabeSenden" :disabled="freigabeSending" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 flex items-center gap-2 disabled:opacity-50">
        <Send class="w-3.5 h-3.5" />
        {{ freigabeSending ? 'Wird gesendet…' : (freigabeStatus ? 'Erneut zur Freigabe senden' : 'An Kunde zur Freigabe senden') }}
      </button>
    </div>

    <!-- Empfänger -->
    <div v-if="text" class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
        <Users class="w-4 h-4 text-[#0088ba]" /> Empfänger Fachmedien
        <button @click="toggleAlle" class="ml-auto text-xs text-[#0088ba] hover:underline">{{ alleAusgewaehlt ? 'Alle abwählen' : 'Alle auswählen' }}</button>
      </h3>
      <div class="space-y-2 max-h-72 overflow-y-auto">
        <label v-for="k in kontakte" :key="k.id" class="flex items-center gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer">
          <input type="checkbox" :checked="ausgewaehlt.includes(k.email)" @change="toggleEmpfaenger(k.email)" class="rounded text-[#0088ba]" />
          <div class="flex-1">
            <div class="text-sm text-gray-800">{{ k.name }} <span class="text-xs text-gray-400">— {{ k.rolle }}</span></div>
            <div class="text-xs text-gray-500">{{ k.medium }} · {{ k.email }}</div>
          </div>
        </label>
      </div>
    </div>

    <!-- Versand -->
    <div v-if="text" class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <label class="text-xs text-gray-600 mb-1 block">Betreff</label>
      <input v-model="betreff" class="input mb-3" />
      <button @click="versenden" :disabled="!canVersenden || sending" class="w-full px-4 py-3 bg-[#0088ba] text-white rounded-xl font-semibold hover:bg-[#00a0d8] disabled:opacity-50 flex items-center justify-center gap-2">
        <Send class="w-4 h-4" />
        {{ sending ? 'Versende...' : `An ${ausgewaehlt.length} Pressekontakt(e) senden` }}
      </button>
      <p v-if="!canVersenden" class="text-xs text-amber-600 mt-2 text-center">⚠️ Bitte alle 4 Freigabe-Checkboxen oben ankreuzen, bevor versendet wird.</p>
    </div>

    <!-- Status -->
    <div v-if="versendetAm" class="bg-green-50 border border-green-200 rounded-xl p-5 mb-4">
      <h3 class="font-semibold text-green-900 text-sm mb-3 flex items-center gap-2">
        <CheckCircle2 class="w-5 h-5 text-green-600" /> Versendet!
      </h3>
      <p class="text-sm text-green-800">Am {{ formatDate(versendetAm) }} an {{ versendetEmpfaenger?.length || 0 }} Pressekontakte verschickt.</p>
      <details class="mt-2">
        <summary class="text-xs text-green-700 cursor-pointer">Empfänger anzeigen</summary>
        <ul class="text-xs text-green-700 mt-2 ml-4 list-disc">
          <li v-for="e in versendetEmpfaenger" :key="e">{{ e }}</li>
        </ul>
      </details>
    </div>

    <!-- Veröffentlichungs-Links -->
    <div v-if="versendetAm" class="bg-white rounded-xl border border-gray-100 p-5">
      <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
        <LinkIcon class="w-4 h-4 text-[#0088ba]" /> Veröffentlichungs-Links
      </h3>
      <p class="text-xs text-gray-500 mb-3">Sobald die Artikel online sind, hier die Links eintragen.</p>
      <div class="space-y-2">
        <div v-for="(link, idx) in veroeffentlichungen" :key="idx" class="flex gap-2">
          <input v-model="veroeffentlichungen[idx].medium" placeholder="Medium" class="input flex-shrink-0 w-40" @blur="save" />
          <input v-model="veroeffentlichungen[idx].url" placeholder="https://..." class="input flex-1" @blur="save" />
          <button @click="veroeffentlichungen.splice(idx, 1); save()" class="px-2 text-red-500"><X class="w-4 h-4" /></button>
        </div>
        <button @click="veroeffentlichungen.push({ medium: '', url: '' })" class="text-sm text-[#0088ba] hover:underline">+ Veröffentlichung hinzufügen</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Trophy, CheckCircle2, FileText, Users, Sparkles, Send, Link as LinkIcon, X, UserCheck, Clock, AlertCircle } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })

const freigabe = ref({ dealAbgeschlossen: false, maInformiert: false, kaeuferFreigabe: false, verkaeuferFreigabe: false })
const deal = ref({ seite: 'Verkäuferseite', schwerpunkt: 'IT-Systemhaus', kaeuferFirma: '', kaeuferOrt: '', verkaeuferFirma: '', verkaeuferOrt: '', besonderheiten: '', synergien: '' })
const text = ref('')
const betreff = ref('Pressemitteilung – Unternehmensverkauf')
const kontakte = ref([])
const ausgewaehlt = ref([])
const generating = ref(false)
const sending = ref(false)
const versendetAm = ref('')
const versendetEmpfaenger = ref([])
const veroeffentlichungen = ref([])
const freigabeStatus = ref('')  // '' | 'pending' | 'freigegeben' | 'aenderung_gewuenscht'
const freigabeAngefragtAm = ref('')
const freigabeAm = ref('')
const freigabeKommentar = ref('')
const freigabeSending = ref(false)

async function zurFreigabeSenden() {
  if (!text.value) return
  freigabeSending.value = true
  try {
    await authFetch('/pr-zur-freigabe', { method: 'POST', data: { targetId: props.targetId, text: text.value } })
    freigabeStatus.value = 'pending'
    freigabeAngefragtAm.value = new Date().toISOString()
    toast.success('Pressetext zur Freigabe an Kunde gesendet. Du bekommst Bescheid sobald geantwortet wurde.')
  } catch (e) { toast.error('Fehler: ' + (e?.response?.data?.error || e.message)) }
  finally { freigabeSending.value = false }
}

const alleAusgewaehlt = computed(() => kontakte.value.length > 0 && ausgewaehlt.value.length === kontakte.value.length)
const canVersenden = computed(() =>
  freigabe.value.dealAbgeschlossen && freigabe.value.maInformiert &&
  freigabe.value.kaeuferFreigabe && freigabe.value.verkaeuferFreigabe &&
  ausgewaehlt.value.length > 0 && text.value
)

function toggleAlle() {
  ausgewaehlt.value = alleAusgewaehlt.value ? [] : kontakte.value.map(k => k.email)
}
function toggleEmpfaenger(email) {
  const i = ausgewaehlt.value.indexOf(email)
  if (i >= 0) ausgewaehlt.value.splice(i, 1)
  else ausgewaehlt.value.push(email)
}

async function generieren() {
  generating.value = true
  try {
    const r = await authFetch('/pr-erstellen', { method: 'POST', data: { targetId: props.targetId, ...deal.value } })
    text.value = r.text
    save()
  } catch (e) { toast.error('KI-Generierung fehlgeschlagen: ' + (e?.response?.data?.error || e.message)) }
  finally { generating.value = false }
}

async function versenden() {
  if (!confirm(`Pressemitteilung jetzt an ${ausgewaehlt.value.length} Empfänger senden?`)) return
  sending.value = true
  try {
    const r = await authFetch('/pr-versand', { method: 'POST', data: {
      targetId: props.targetId, betreff: betreff.value, text: text.value, empfaengerEmails: ausgewaehlt.value
    }})
    versendetAm.value = new Date().toISOString()
    versendetEmpfaenger.value = r.gesendet
    save()
    toast.success(`Pressemitteilung an ${r.count} Empfänger gesendet ✅`)
  } catch (e) { toast.error('Versand fehlgeschlagen: ' + (e?.response?.data?.error || e.message)) }
  finally { sending.value = false }
}

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    const data = {
      freigabe: freigabe.value,
      deal: deal.value,
      text: text.value,
      betreff: betreff.value,
      ausgewaehlt: ausgewaehlt.value,
      versendetAm: versendetAm.value,
      versendetEmpfaenger: versendetEmpfaenger.value,
      veroeffentlichungen: veroeffentlichungen.value,
    }
    try { await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, presseJson: JSON.stringify(data) } }) }
    catch (e) { console.error(e) }
  }, 500)
}

function formatDate(iso) { return iso ? new Date(iso).toLocaleString('de-DE') : '' }

onMounted(async () => {
  try { kontakte.value = await authFetch('/presse-kontakte') } catch (e) { console.error(e) }
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (t.presseJson) {
      try {
        const d = JSON.parse(t.presseJson)
        if (d.freigabe) Object.assign(freigabe.value, d.freigabe)
        if (d.deal) Object.assign(deal.value, d.deal)
        text.value = d.text || ''
        betreff.value = d.betreff || betreff.value
        ausgewaehlt.value = d.ausgewaehlt || []
        versendetAm.value = d.versendetAm || ''
        versendetEmpfaenger.value = d.versendetEmpfaenger || []
        veroeffentlichungen.value = d.veroeffentlichungen || []
        freigabeStatus.value = d.freigabeStatus || ''
        freigabeAngefragtAm.value = d.freigabeAngefragtAm || ''
        freigabeAm.value = d.freigabeAm || ''
        freigabeKommentar.value = d.freigabeKommentar || ''
      } catch {}
    }
    // Vorbefüllen aus Target-Stammdaten falls leer
    if (!deal.value.verkaeuferFirma) deal.value.verkaeuferFirma = t.verkaueferName || t.firma || ''
    if (!deal.value.verkaeuferOrt) deal.value.verkaeuferOrt = t.region || t.ort || ''
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
