<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">
          {{ isKaufMandat ? 'NDA für Käufer' : 'NDA für Investor' }}
        </h3>
        <p class="text-xs text-gray-500">Beidseitige Vertraulichkeitsvereinbarung (Stand 2025) · digital signierbar</p>
      </div>
      <div class="flex gap-2">
        <button @click="openPreview" :disabled="previewLoading" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50 disabled:opacity-50">
          <FileText class="w-4 h-4" /> {{ previewLoading ? 'Lade…' : 'Vorschau (PDF)' }}
        </button>
      </div>
    </div>

    <!-- Variablen + Empfänger -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <h4 class="font-semibold text-sm text-gray-800 mb-3">Variablen für diesen {{ isKaufMandat ? 'Käufer' : 'Investor' }}</h4>
      <div class="grid grid-cols-2 gap-3">
        <div class="col-span-2">
          <label class="text-xs font-medium text-gray-600 mb-1 block">Projekt-Referenz (mb-Nr.)</label>
          <input v-model="vars.mbNr" readonly placeholder="(wird automatisch aus dem Target übernommen)"
            class="input bg-gray-50 font-mono cursor-not-allowed" />
          <p class="text-xs text-gray-400 mt-1">Diese Nummer erscheint im NDA, damit der Interessent eindeutig weiß, für welches Projekt er Vertraulichkeit zusichert.</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Mandantenfirma ({{ isKaufMandat ? 'Käufer' : 'Investor' }})</label>
          <input v-model="vars.firma" placeholder="z.B. Beispiel IT-Holding GmbH" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Vertreten durch</label>
          <input v-model="vars.vertreten" placeholder="z.B. Max Mustermann (Geschäftsführer)" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Anschrift (Straße + Hausnr.)</label>
          <input v-model="vars.adresse" placeholder="z.B. Beispielstraße 1" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">PLZ + Ort</label>
          <input v-model="vars.plzOrt" placeholder="z.B. 80331 München" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">E-Mail des Unterzeichners *</label>
          <input v-model="vars.email" type="email" placeholder="z.B. max@firma.de" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Ort der Unterzeichnung</label>
          <input v-model="vars.ort" placeholder="z.B. München" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Datum</label>
          <input v-model="vars.datum" type="date" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Gültig bis (Jahr)</label>
          <input v-model="vars.gueltigBis" type="number" placeholder="2027" class="input" />
        </div>
      </div>
      <button @click="zurSignaturSenden" :disabled="!canSend || sending"
        class="mt-4 w-full px-4 py-2.5 bg-[#0088ba] text-white rounded-xl text-sm font-semibold hover:bg-[#00a0d8] disabled:opacity-50 flex items-center justify-center gap-2">
        <Send class="w-4 h-4" /> {{ sending ? 'Wird gesendet…' : `NDA zur digitalen Signatur an ${vars.email || '...'} senden` }}
      </button>
      <p class="text-xs text-gray-400 mt-2">Der Empfänger bekommt einen Mail-Link, kann das NDA online ansehen und mit Code per Mail signieren – gleicher Workflow wie beim Mandatsvertrag.</p>
    </div>

    <!-- NDA-Vorschau -->
    <div class="bg-white rounded-xl border border-gray-100 p-8 font-serif text-sm leading-relaxed">
      <div class="text-center mb-6">
        <h2 class="text-xl font-bold mb-2">Vertraulichkeitsvereinbarung (NDA)</h2>
        <p class="text-xs text-gray-500">Beidseitig · Stand: 25.06.2025</p>
      </div>

      <p class="mb-4"><strong>Zwischen</strong></p>
      <div class="mb-4 border-l-2 border-gray-200 pl-4">
        <strong>{{ vars.firma || '[Mandantenfirma]' }}</strong><br>
        vertreten durch {{ vars.vertreten || '[Name Zeichnungsberechtigter]' }}<br>
        <span class="text-xs text-gray-500">— nachfolgend „Investor" —</span>
      </div>

      <p class="mb-4"><strong>und</strong></p>
      <div class="mb-4 border-l-2 border-[#0088ba] pl-4">
        <strong>mibeca GmbH</strong><br>
        Schillerstr. 1 · 29525 Uelzen<br>
        vertreten durch Jennifer Kaplan<br>
        <span class="text-xs text-gray-500">— nachfolgend „Transaktionsberater" —</span>
      </div>

      <p class="mb-4 italic text-gray-700">
        Die Parteien beabsichtigen, im Rahmen einer möglichen Transaktion vertrauliche Informationen auszutauschen.
        Zu diesem Zweck vereinbaren die Parteien Folgendes:
      </p>

      <ol class="list-decimal pl-5 space-y-3 text-justify">
        <li>
          <strong>Definition vertraulicher Informationen:</strong>
          Als vertrauliche Informationen gelten sämtliche unter dieser Vereinbarung ausgetauschten Daten,
          insbesondere Informationen zu M&A-Transaktionen, geschäftliche, technische, finanzielle und personelle Details.
        </li>
        <li>
          <strong>Behandlungspflichten:</strong>
          Die Parteien behandeln die vertraulichen Informationen mit größtmöglicher Sorgfalt, nutzen sie ausschließlich
          zum vereinbarten Zweck und unterlassen jegliche unbefugte Vervielfältigung oder Weitergabe.
        </li>
        <li>
          <strong>Ausnahmen:</strong>
          Von der Geheimhaltungspflicht ausgenommen sind Informationen, die (a) öffentlich bekannt sind oder werden,
          (b) der empfangenden Partei bereits durch Dritte zugänglich waren, oder (c) unabhängig entwickelt wurden.
        </li>
        <li>
          <strong>Weitergabe bei Rechtspflicht:</strong>
          Im Falle gesetzlicher oder behördlicher Verpflichtung zur Offenlegung wird die andere Partei unverzüglich informiert.
        </li>
        <li>
          <strong>Weitergabe an Angestellte/Berater:</strong>
          Die Weitergabe an eigene Mitarbeiter, Wirtschaftsprüfer, Rechtsanwälte und sonstige Berater ist zulässig,
          soweit diese ihrerseits zur Verschwiegenheit verpflichtet sind („need-to-know"-Prinzip).
        </li>
        <li>
          <strong>Keine Eigentums- oder Nutzungsrechte:</strong>
          Aus dem Erhalt vertraulicher Informationen entstehen keinerlei Eigentums-, Nutzungs- oder Lizenzrechte.
        </li>
        <li>
          <strong>Laufzeit:</strong>
          Diese Vereinbarung gilt bis zum <strong>31.12.2027</strong>. Die Nicht-Weitergabe-Verpflichtung besteht
          darüber hinaus für weitere drei Jahre fort.
        </li>
        <li>
          <strong>Schriftform:</strong>
          Änderungen und Ergänzungen bedürfen der Schriftform. Mündliche Nebenabreden bestehen nicht.
        </li>
        <li>
          <strong>Salvatorische Klausel:</strong>
          Sollten einzelne Bestimmungen unwirksam sein, bleibt die Wirksamkeit der übrigen Bestimmungen unberührt.
        </li>
        <li>
          <strong>Anwendbares Recht und Gerichtsstand:</strong>
          Es gilt deutsches Recht. Gerichtsstand ist Uelzen (Sitz des Transaktionsberaters).
        </li>
      </ol>

      <!-- Unterschriftenblock -->
      <div class="grid grid-cols-2 gap-8 mt-10 pt-6 border-t border-gray-200">
        <div>
          <div class="text-xs text-gray-500 mb-1">Investor:</div>
          <div class="border-b border-gray-400 pb-1 mb-2">{{ vars.ort || '[Ort]' }}, {{ formatDate(vars.datum) }}</div>
          <div class="h-12 border-b border-gray-400 mb-2"></div>
          <div class="text-xs text-gray-500">Unterschrift {{ vars.vertreten || '[Name]' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 mb-1">Transaktionsberater:</div>
          <div class="border-b border-gray-400 pb-1 mb-2">Uelzen, {{ formatDate(new Date().toISOString().slice(0,10)) }}</div>
          <div class="h-12 border-b border-gray-400 mb-2 italic text-gray-400 flex items-end pb-1">Jennifer Kaplan</div>
          <div class="text-xs text-gray-500">mibeca GmbH</div>
        </div>
      </div>
    </div>

    <!-- PDF-Vorschau Modal -->
    <div v-if="previewUrl" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" @click.self="closePreview">
      <div class="bg-white rounded-2xl w-full max-w-4xl h-[90vh] flex flex-col overflow-hidden shadow-2xl">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-100">
          <h3 class="font-bold text-gray-900 flex items-center gap-2"><FileText class="w-5 h-5 text-[#0088ba]" /> NDA-Vorschau</h3>
          <div class="flex items-center gap-2">
            <a :href="previewUrl" :download="`NDA_${vars.firma || 'Entwurf'}.pdf`" class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">Herunterladen</a>
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
import { FileText, Send, X } from '@lucide/vue'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })
const target = ref(null)

const vars = ref({
  mbNr: '',
  firma: '', vertreten: '', adresse: '', plzOrt: '',
  email: '', ort: '',
  datum: new Date().toISOString().slice(0, 10),
  gueltigBis: new Date().getFullYear() + 2,
})

const isKaufMandat = computed(() => /kauf|investor/i.test(target.value?.projekttyp || ''))
const docVariante = computed(() => isKaufMandat.value ? 'kaeufer' : 'investor')
const canSend = computed(() => !!(vars.value.firma && vars.value.vertreten && vars.value.email && vars.value.ort))

function formatDate(s) {
  if (!s) return '[Datum]'
  try { return new Date(s).toLocaleDateString('de-DE') } catch { return s }
}

const previewUrl = ref(null)
const previewLoading = ref(false)
const sending = ref(false)
const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

async function openPreview() {
  previewLoading.value = true
  try {
    const r = await fetch(`${apiBase}/nda-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (sessionStorage.getItem('customerJwt') || sessionStorage.getItem('msalToken') || '') },
      body: JSON.stringify({ form: vars.value, variante: docVariante.value }),
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = URL.createObjectURL(await r.blob())
  } catch (e) { toast.error('Vorschau fehlgeschlagen: ' + e.message) }
  finally { previewLoading.value = false }
}
function closePreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = null
}

async function zurSignaturSenden() {
  if (!canSend.value) return
  if (!confirm(`NDA an ${vars.value.email} zur digitalen Signatur senden?`)) return
  sending.value = true
  try {
    await authFetch('/nda-zur-signatur', { method: 'POST', data: {
      targetId: props.targetId, form: vars.value, variante: docVariante.value, empfaengerEmail: vars.value.email
    }})
    toast.success('NDA wurde an ' + vars.value.email + ' versendet. ✅')
  } catch (e) { toast.error('Versand fehlgeschlagen: ' + (e?.response?.data?.error || e.message)) }
  finally { sending.value = false }
}

onMounted(async () => {
  if (!props.targetId) return
  try {
    target.value = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (target.value?.mbNr) vars.value.mbNr = target.value.mbNr
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
