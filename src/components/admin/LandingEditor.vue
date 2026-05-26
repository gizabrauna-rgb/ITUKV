<template>
  <div v-if="!loaded" class="text-center py-12 text-gray-400 text-sm">Lade…</div>

  <div v-else>
    <div class="flex items-start justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Landing-Page</h3>
        <p class="text-xs text-gray-500">Öffentliche Anonymisierungs-Seite unter <code class="bg-gray-100 px-1 rounded">{{ liveUrl }}</code></p>
      </div>
      <div class="flex gap-2">
        <button @click="vorbefuellen" class="flex items-center gap-2 px-3 py-2 bg-amber-500 text-white rounded-xl text-sm font-medium hover:bg-amber-600">
          <Sparkles class="w-4 h-4" /> Aus Exposé vorbefüllen
        </button>
        <a :href="liveUrl" target="_blank" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
          <ExternalLink class="w-4 h-4" /> Live-Vorschau
        </a>
      </div>
    </div>

    <!-- Status-Box -->
    <div class="bg-white rounded-xl border border-gray-100 p-4 mb-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div :class="['w-3 h-3 rounded-full', landing.status === 'published' ? 'bg-green-500' : 'bg-gray-400']"></div>
        <div>
          <div class="font-medium text-sm">Status: {{ landing.status === 'published' ? 'Veröffentlicht (öffentlich erreichbar)' : 'Entwurf (noch nicht öffentlich)' }}</div>
          <div v-if="landing.status === 'published'" class="text-xs text-gray-500">Live unter <a :href="liveUrl" target="_blank" class="text-[#0088ba] hover:underline">{{ liveUrl }}</a></div>
        </div>
      </div>
      <div class="flex gap-2">
        <button v-if="landing.status !== 'published'" @click="publish" :disabled="saving" class="px-4 py-2 bg-green-600 text-white rounded-xl text-sm font-semibold hover:bg-green-700 disabled:opacity-50">
          Veröffentlichen
        </button>
        <button v-else @click="unpublish" :disabled="saving" class="px-4 py-2 border border-red-200 text-red-700 bg-red-50 rounded-xl text-sm hover:bg-red-100 disabled:opacity-50">
          Zurückziehen
        </button>
      </div>
    </div>

    <!-- Hero -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-3">
      <h4 class="font-semibold text-gray-800 text-sm mb-3">Hero-Bereich (oberster Block)</h4>
      <div class="mb-3">
        <label class="lbl">Headline · 1 Satz, prägnant</label>
        <input v-model="landing.headline" @blur="save" placeholder="z.B. Etabliertes IT-Systemhaus im Großraum Nürnberg sucht Nachfolger" class="input" />
      </div>
      <div>
        <label class="lbl">Sub-Headline · 3-5 Stichworte mit · getrennt</label>
        <input v-model="landing.subheadline" @blur="save" placeholder="z.B. 15 Mitarbeiter · Starke Marktposition · Hoher Anteil wiederkehrender Umsätze" class="input" />
      </div>
    </div>

    <!-- Teaser-Text -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-3">
      <h4 class="font-semibold text-gray-800 text-sm mb-3">Teaser-Text</h4>
      <div class="mb-3">
        <label class="lbl">Kurzbeschreibung (1-2 Sätze, fett oben)</label>
        <textarea v-model="landing.teaserShort" @blur="save" rows="2" placeholder="z.B. Profitables IT-Systemhaus mit über 30 Jahren Marktpräsenz, stabiler Kundenbasis und attraktiven Wachstumspotenzialen – Übernahme aller Geschäftsanteile gegen Gebot." class="input resize-none"></textarea>
      </div>
      <div>
        <label class="lbl">Hauptbeschreibung (mehrere Sätze, anonymisiert)</label>
        <textarea v-model="landing.description" @blur="save" rows="6" placeholder="Zum Verkauf steht ein regional führendes IT-Systemhaus im PLZ-Gebiet 91… (Großraum Nürnberg), das seit mehr als drei Jahrzehnten erfolgreich am Markt agiert..." class="input resize-y"></textarea>
      </div>
    </div>

    <!-- Key Facts -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-3">
      <div class="flex items-center justify-between mb-3">
        <h4 class="font-semibold text-gray-800 text-sm">Key Facts (Kacheln)</h4>
        <button @click="addFact" class="flex items-center gap-1 text-xs text-[#0088ba] hover:text-[#00a0d8]">
          <Plus class="w-3 h-3" /> Kachel hinzufügen
        </button>
      </div>
      <div v-if="!landing.keyFacts?.length" class="text-xs text-gray-400 italic">Noch keine Kacheln. Klick „Kachel hinzufügen".</div>
      <div v-else class="space-y-2">
        <div v-for="(f, i) in landing.keyFacts" :key="i" class="grid grid-cols-12 gap-2 p-3 bg-gray-50 rounded-lg">
          <input v-model="f.wert" @blur="save" placeholder='Wert (z.B. „15 Mitarbeiter")' class="input col-span-3 text-sm" />
          <input v-model="f.label" @blur="save" placeholder="Untertitel (kann leer sein)" class="input col-span-4 text-sm" />
          <input v-model="f.beschreib" @blur="save" placeholder='Beschreibung (z.B. „erfahren, eingespielt")' class="input col-span-4 text-sm" />
          <button @click="removeFact(i)" class="text-gray-400 hover:text-red-500 col-span-1 flex justify-center">
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Käufer-Bereich (Token-Page) -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-3">
      <h4 class="font-semibold text-gray-800 text-sm mb-1">Käufer-Bereich (nach Anmeldung)</h4>
      <p class="text-xs text-gray-500 mb-3">Diese Felder gelten für die Seite, die der Interessent nach Anmeldung per Token-Link sieht (Exposé- und NDA-Downloads + Termin-Buchung).</p>
      <div class="grid grid-cols-1 gap-3">
        <div>
          <label class="lbl">Exposé-PDF (URL)</label>
          <input v-model="landing.exposeUrl" @blur="save" placeholder="https://...exposé.pdf — Link zum vollen Exposé-PDF" class="input text-sm" />
        </div>
        <div>
          <label class="lbl">NDA-Vorlage (URL)</label>
          <input v-model="landing.ndaTemplateUrl" @blur="save" placeholder="https://...nda.pdf — Link zur leeren NDA-Vorlage zum Unterschreiben" class="input text-sm" />
        </div>
        <div>
          <label class="lbl">Termin-Buchung (Outlook-Bookings-URL)</label>
          <input v-model="landing.terminBookingUrl" @blur="save" placeholder="https://outlook.office.com/.../bookings/s/... (leer lassen = Default-Jenny-Link)" class="input text-sm" />
          <p class="text-[11px] text-gray-400 mt-1">Wenn leer, wird automatisch der Default-Link von Jennifer Kaplan verwendet.</p>
        </div>
      </div>
    </div>

    <p class="text-xs text-gray-400 text-center mt-4">Auto-Speichern beim Verlassen jedes Feldes.</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, X, Sparkles, ExternalLink } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })

const LANDING_BASE = 'https://targets.itukv.de'  // muss mit Backend LANDING_BASE übereinstimmen
const target = ref(null)
const loaded = ref(false)
const saving = ref(false)
const landing = ref({
  status: 'draft',
  headline: '',
  subheadline: '',
  teaserShort: '',
  description: '',
  keyFacts: [],
  exposeUrl: '',
  ndaTemplateUrl: '',
  terminBookingUrl: '',
})

const liveUrl = computed(() => `${LANDING_BASE}/${(target.value?.mbNr || 'mb-xxx').toLowerCase()}`)

onMounted(async () => {
  if (!props.targetId) { loaded.value = true; return }
  try {
    target.value = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (target.value?.landingJson) {
      try {
        const e = JSON.parse(target.value.landingJson)
        landing.value = { ...landing.value, ...e, keyFacts: Array.isArray(e.keyFacts) ? e.keyFacts : [] }
      } catch {}
    }
  } catch (e) { console.error(e) }
  finally { loaded.value = true }
})

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    saving.value = true
    try {
      await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, landingJson: JSON.stringify(landing.value) } })
    } catch (e) { console.error(e) }
    finally { saving.value = false }
  }, 400)
}

async function publish() {
  if (!landing.value.headline || !landing.value.subheadline) {
    toast.warn('Bitte mindestens Headline und Sub-Headline ausfüllen.')
    return
  }
  landing.value.status = 'published'
  await saveImmediate()
  toast.success('Landing-Page ist jetzt öffentlich.')
}

async function unpublish() {
  if (!confirm('Landing-Page zurückziehen? Sie ist dann nicht mehr öffentlich erreichbar.')) return
  landing.value.status = 'draft'
  await saveImmediate()
  toast.info('Landing-Page zurückgezogen.')
}

async function saveImmediate() {
  saving.value = true
  try {
    await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, landingJson: JSON.stringify(landing.value) } })
  } finally { saving.value = false }
}

function addFact() {
  landing.value.keyFacts.push({ wert: '', label: '', beschreib: '' })
}
function removeFact(i) {
  landing.value.keyFacts.splice(i, 1)
  save()
}

async function vorbefuellen() {
  if (!confirm('Vorhandene Inhalte werden ergänzt (leere Felder vorbefüllt). Fortfahren?')) return
  try {
    const t = target.value
    let expose = {}, fragebogen = {}
    try { expose = JSON.parse(t.exposeJson || '{}') } catch {}
    try { fragebogen = JSON.parse(t.fragebogenJson || '{}') } catch {}

    if (!landing.value.headline) landing.value.headline = expose.headline || `IT-Unternehmen in ${t.region || 'attraktiver Region'} sucht Nachfolger`
    if (!landing.value.subheadline) landing.value.subheadline = expose.subheadline || ''
    if (!landing.value.teaserShort) {
      const sec0 = (expose.sektionen || []).find(s => /unternehmen|historie/i.test(s.label))
      landing.value.teaserShort = sec0?.body?.slice(0, 250) || ''
    }
    if (!landing.value.description) {
      const sec1 = (expose.sektionen || []).find(s => /geschäftsfeld|gesch.ftsfeld/i.test(s.label))
      landing.value.description = sec1?.body || ''
    }
    if (!landing.value.keyFacts?.length) {
      const facts = []
      const ma = ['technikVollzeit','vertriebVollzeit','innendienstVollzeit'].reduce((s, k) => s + (parseInt(fragebogen.personal?.[k]) || 0), 0)
      if (ma) facts.push({ wert: `${ma} Mitarbeiter`, label: '', beschreib: 'erfahrenes, eingespieltes Team' })
      if (fragebogen.aktiveGeschaeftskunden) facts.push({ wert: `${fragebogen.aktiveGeschaeftskunden}+ Geschäftskunden`, label: '', beschreib: 'planbare, laufende Verträge' })
      if (fragebogen.aktivePrivatkunden) facts.push({ wert: `${fragebogen.aktivePrivatkunden}+ Privatkunden`, label: '', beschreib: 'gewachsene, loyale Kundenbasis' })
      if (fragebogen.wiederkehrendeUmsaetzeProzent) facts.push({ wert: `Bis zu ${fragebogen.wiederkehrendeUmsaetzeProzent}% wiederkehrende Erlöse`, label: '', beschreib: 'Managed Services & Cloud-Lösungen' })
      if (fragebogen.branchenschwerpunkte) facts.push({ wert: 'Breit diversifizierte Umsätze', label: '', beschreib: fragebogen.branchenschwerpunkte })
      landing.value.keyFacts = facts
    }
    await saveImmediate()
    toast.success('Aus Exposé / Fragebogen vorbefüllt — bitte prüfen und ggf. anpassen.')
  } catch (e) {
    toast.error('Vorbefüllen fehlgeschlagen: ' + e.message)
  }
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border-2 border-gray-200 bg-white rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
.lbl { @apply block text-xs font-medium text-gray-600 mb-1; }
</style>
