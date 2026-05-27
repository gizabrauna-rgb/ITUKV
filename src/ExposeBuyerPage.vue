<template>
  <div class="min-h-screen bg-gray-50">
    <header class="max-w-3xl mx-auto px-6 pt-6">
      <img src="/e4adade-577b-0f2-5be2-71a313ed1cd2_d023416-88e7-db0f-fedb-6b354cf65_itukv-form.jpg"
        alt="Mike Bergmann · IT-Unternehmen kaufen und verkaufen"
        class="w-full h-auto rounded-2xl block" />
    </header>

    <main class="max-w-3xl mx-auto px-6 py-10">
      <div v-if="loading" class="text-center text-gray-400">Lade…</div>
      <div v-else-if="!data" class="bg-white rounded-2xl border border-gray-100 p-10 text-center">
        <h2 class="font-bold text-gray-900 mb-2">Zugriff nicht möglich</h2>
        <p class="text-sm text-gray-500">Der Link ist ungültig oder abgelaufen. Bitte melde dich erneut über die Landing-Page an.</p>
      </div>

      <template v-else>
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-8 leading-tight">
          <template v-if="data.headline">{{ data.headline }}&nbsp;<span class="text-gray-400 font-normal mx-1">|</span>&nbsp;</template>Projektnummer&nbsp;<span class="font-mono">{{ data.mbNr.toLowerCase() }}</span>
        </h1>

        <p class="text-lg text-gray-800 mb-6">Hallo {{ data.name || data.firma }},</p>

        <!-- Exposé-Vorschau (immer sichtbar) -->
        <section class="bg-white rounded-2xl border border-gray-100 p-7 mb-5">
          <h2 class="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
            <FileText class="w-5 h-5 text-[#0088ba]" /> Anonymisiertes Exposé
          </h2>
          <p class="text-sm text-gray-600 mb-4">Direkt hier ansehen oder als PDF herunterladen.</p>
          <div class="flex gap-3">
            <button @click="openPreview('expose')"
              class="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-[#0088ba] text-white rounded-xl text-sm font-semibold hover:bg-[#00a0d8]">
              <Eye class="w-5 h-5" /> Exposé jetzt ansehen
            </button>
            <a :href="exposeDownloadUrl" target="_blank"
              class="flex items-center justify-center gap-2 px-4 py-3 border border-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50">
              <Download class="w-5 h-5" /> Download
            </a>
          </div>
        </section>

        <!-- =========== ZUSTAND: VOR NDA =========== -->
        <template v-if="!ndaUnterzeichnet">
          <!-- Erklär-Text -->
          <section class="bg-white rounded-2xl border border-gray-100 p-7 mb-5">
            <h2 class="text-xl font-bold text-gray-900 mb-3">Das Unternehmen hat Dein Interesse geweckt – wie geht es jetzt weiter?</h2>
            <p class="text-sm text-gray-700 leading-relaxed mb-4">
              Du hast oben bereits Zugriff auf das anonymisierte Exposé. Damit wir Dir im nächsten Schritt
              <strong>tiefere Einblicke und die Kontaktdaten</strong> des Verkäufers geben können, benötigen wir Dein NDA.
            </p>
            <p class="text-sm text-gray-700 leading-relaxed mb-4">
              Am einfachsten geht das <strong>direkt hier online mit ein paar Klicks</strong> — Du zeichnest Deine Unterschrift
              im Browser und wir generieren das fertige NDA-PDF automatisch (rechtssicher gemäß eIDAS, einfache elektronische
              Signatur). Alternativ kannst Du das NDA auch als PDF herunterladen, klassisch unterschreiben und wieder hochladen.
            </p>

            <div class="bg-amber-50 border-l-4 border-amber-400 p-4 rounded mb-4">
              <p class="text-sm text-amber-900">
                <strong>Wichtig:</strong> Die <strong>Termin-Buchung mit Jennifer Kaplan</strong> wird erst freigeschaltet,
                sobald Dein unterschriebenes NDA vorliegt.
              </p>
            </div>

            <h3 class="text-lg font-bold text-gray-900 mt-6 mb-2">Nächster Schritt: Terminbuchung</h3>
            <p class="text-sm text-gray-700 leading-relaxed mb-4">
              Sobald das NDA bei uns vorliegt, erhältst Du <strong>sofort die Möglichkeit</strong>, einen
              Termin mit unserer M&amp;A-Beraterin <strong>Jennifer Kaplan</strong> zu buchen.
              In einem ca. 15-minütigen Gespräch klären wir den weiteren Ablauf sowie alle offenen Fragen.
            </p>

            <h3 class="text-lg font-bold text-gray-900 mt-6 mb-2">Transparenz im Prozess</h3>
            <p class="text-sm text-gray-700 leading-relaxed mb-4">
              Wenn sich im Gespräch herausstellt, dass die Rahmenbedingungen passen, prüfen wir die nächsten Schritte mit dem Verkäufer.
              Nach finaler Freigabe erhältst Du die Kontaktdaten des Zielunternehmens.
            </p>

            <p class="text-sm text-gray-700 leading-relaxed mb-4">
              Bei Rückfragen erreichst Du Jennifer Kaplan unter
              <a href="mailto:jk@mike-bergmann.de" class="text-[#0088ba] hover:underline font-medium">jk@mike-bergmann.de</a>.
              Bitte beachte, dass tiefergehende Fragen <strong>erst nach Erhalt des unterschriebenen NDA</strong> beantwortet werden können.
            </p>

            <p class="text-sm text-gray-700 leading-relaxed mt-5">Wir freuen uns auf die Zusammenarbeit!</p>
            <p class="text-sm text-gray-700 leading-relaxed">Dein M&amp;A-Team der <strong>Mike Bergmann Akademie</strong></p>
          </section>

          <!-- NDA-Aktionen -->
          <section class="bg-white rounded-2xl border-2 border-[#FF6F00]/30 p-7 mb-5">
            <h2 class="text-lg font-bold text-gray-900 mb-2 flex items-center gap-2">
              <FileText class="w-5 h-5 text-[#FF6F00]" /> NDA unterschreiben
            </h2>
            <p class="text-sm text-gray-600 mb-5">Wähle den Weg, der für Dich am bequemsten ist:</p>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <button @click="showSignModal = true"
                class="md:col-span-3 flex items-center justify-center gap-2 px-4 py-4 bg-[#FF6F00] text-white rounded-xl text-sm font-semibold hover:bg-[#e56500]">
                <PenTool class="w-5 h-5" /> Jetzt online unterschreiben
              </button>
              <button @click="openPreview('nda')"
                class="flex items-center justify-center gap-2 px-4 py-3 bg-white border border-gray-200 text-gray-800 rounded-xl text-sm font-medium hover:bg-gray-50">
                <Eye class="w-4 h-4" /> NDA ansehen
              </button>
              <a :href="ndaDownloadUrl" target="_blank"
                class="flex items-center justify-center gap-2 px-4 py-3 bg-white border border-gray-200 text-gray-800 rounded-xl text-sm font-medium hover:bg-gray-50">
                <Download class="w-4 h-4" /> NDA-Download
              </a>
            </div>

            <div class="mt-4 pt-4 border-t border-gray-100">
              <p class="text-xs text-gray-500 mb-2">Alternativ: NDA ausgedruckt unterschrieben hochladen</p>
              <label class="flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-50 border border-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-100 cursor-pointer">
                <Upload class="w-4 h-4" /> Unterschriebenes NDA als Datei hochladen
                <input type="file" accept="application/pdf,image/*" @change="onFileChange" class="hidden" :disabled="uploading" />
              </label>
              <p v-if="uploading" class="text-xs text-amber-700 mt-2 text-center">Lade NDA hoch…</p>
            </div>
          </section>
        </template>

        <!-- =========== ZUSTAND: NACH NDA =========== -->
        <template v-else>
          <section class="bg-green-50 border-2 border-green-200 rounded-2xl p-6 mb-5">
            <div class="flex items-start gap-3">
              <CheckCircle2 class="w-7 h-7 text-green-600 flex-shrink-0" />
              <div>
                <h2 class="text-lg font-bold text-green-900 mb-1">NDA erhalten</h2>
                <p class="text-sm text-green-800">
                  Vielen Dank für Dein unterschriebenes NDA zu Projekt <strong>{{ data.mbNr.toUpperCase() }}</strong>.
                  Du kannst jetzt direkt einen Termin mit Jennifer Kaplan buchen.
                </p>
              </div>
            </div>
          </section>

          <!-- Termin-Buchung -->
          <section v-if="data.terminBookingUrl" class="bg-white rounded-2xl border-2 border-[#0088ba]/30 p-7 mb-5">
            <h2 class="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Calendar class="w-5 h-5 text-[#0088ba]" /> Termin mit Jennifer Kaplan buchen
            </h2>
            <p class="text-sm text-gray-700 mb-4">
              In einem ca. 15-minütigen Gespräch klären wir den weiteren Ablauf und alle offenen Fragen rund um Projekt
              <strong>{{ data.mbNr.toUpperCase() }}</strong>.
            </p>

            <div class="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4 flex items-center justify-between gap-3">
              <div class="text-sm">
                <strong class="text-amber-900">Wichtig:</strong>
                <span class="text-amber-800"> Bei der Buchung als Anlass die Projektnummer </span>
                <code class="font-mono font-bold bg-white border border-amber-300 px-2 py-0.5 rounded mx-1">{{ data.mbNr.toUpperCase() }}</code>
                <span class="text-amber-800">angeben.</span>
              </div>
              <button @click="copyMbNr" class="text-xs flex items-center gap-1 px-2 py-1 bg-white border border-amber-300 text-amber-900 rounded hover:bg-amber-100 flex-shrink-0">
                <Copy class="w-3 h-3" /> {{ copied ? 'Kopiert' : 'Kopieren' }}
              </button>
            </div>

            <a :href="data.terminBookingUrl" target="_blank"
              class="flex items-center justify-center gap-2 px-4 py-3 bg-[#0088ba] text-white rounded-xl text-sm font-semibold hover:bg-[#00a0d8]">
              <Calendar class="w-5 h-5" /> Jetzt Termin buchen
            </a>

            <ul class="text-xs text-gray-500 mt-5 space-y-1">
              <li>· Ob das Unternehmen zu Deiner Zukauf-Strategie passt</li>
              <li>· Deine konkreten Zukauf-Visionen — damit wir diese mit dem Profil abgleichen können</li>
              <li>· Den weiteren Ablauf des Prozesses</li>
              <li>· Ob ein Folgegespräch direkt mit dem Verkäufer sinnvoll ist</li>
            </ul>
          </section>
        </template>

        <!-- Team-Photos -->
        <section class="bg-white rounded-2xl border border-gray-100 p-7 mt-6">
          <h3 class="font-bold text-gray-900 mb-5 text-center">Dein M&A-Team der Mike Bergmann Akademie</h3>
          <div class="grid grid-cols-2 gap-6">
            <div class="text-center">
              <img src="/Jenny Kaplan.jpeg" alt="Jenny Kaplan" class="w-32 h-32 rounded-full object-cover mx-auto mb-3 border-4 border-gray-100" />
              <div class="font-semibold text-gray-900">Jennifer Kaplan</div>
              <div class="text-xs text-gray-500">M&A-Beraterin</div>
              <a href="mailto:jk@mike-bergmann.de" class="text-xs text-[#0088ba] hover:underline mt-1 inline-block">jk@mike-bergmann.de</a>
            </div>
            <div class="text-center">
              <img src="/Mike Bergmann.jpeg" alt="Mike Bergmann" class="w-32 h-32 rounded-full object-cover mx-auto mb-3 border-4 border-gray-100" />
              <div class="font-semibold text-gray-900">Mike Bergmann</div>
              <div class="text-xs text-gray-500">Gründer · M&A-Spezialist</div>
            </div>
          </div>
        </section>
      </template>
    </main>

    <footer class="border-t border-gray-100 mt-10 bg-white">
      <div class="max-w-3xl mx-auto px-6 py-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <a href="https://www.itukv.de" target="_blank" rel="noopener" title="Zur Startseite">
          <img src="/Logo_mibeca_Start.png" alt="mibeca" class="h-10 w-auto hover:opacity-80 transition-opacity" />
        </a>
        <div class="flex flex-wrap gap-4 text-xs text-gray-500">
          <a href="https://www.mike-bergmann-akademie.de/pages/impressum" target="_blank" rel="noopener" class="hover:text-[#0088ba]">Impressum</a>
          <a href="https://www.mike-bergmann-akademie.de/agb" target="_blank" rel="noopener" class="hover:text-[#0088ba]">AGB</a>
          <a href="https://www.mike-bergmann-akademie.de/pages/datenschutz" target="_blank" rel="noopener" class="hover:text-[#0088ba]">Datenschutz</a>
        </div>
      </div>
      <div class="text-center text-[11px] text-gray-400 pb-4">© {{ new Date().getFullYear() }} mibeca GmbH · Schillerstr. 1 · 29525 Uelzen · Gerichtsstand Uelzen</div>
    </footer>

    <!-- ============ PDF-PREVIEW-MODAL ============ -->
    <div v-if="previewUrl" class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" @click.self="closePreview">
      <div class="bg-white rounded-2xl w-full max-w-5xl h-[92vh] flex flex-col overflow-hidden shadow-2xl">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-100">
          <h3 class="font-bold text-gray-900 flex items-center gap-2">
            <FileText class="w-5 h-5 text-[#0088ba]" />
            {{ previewKind === 'nda' ? 'NDA-Vorschau' : 'Exposé-Vorschau' }}
          </h3>
          <div class="flex items-center gap-2">
            <a :href="previewUrl" :download="previewKind === 'nda' ? 'NDA_' + (data?.mbNr || '') + '.pdf' : 'Expose_' + (data?.mbNr || '') + '.pdf'"
              class="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">
              <Download class="w-3.5 h-3.5" /> Herunterladen
            </a>
            <button @click="closePreview" class="p-1.5 hover:bg-gray-100 rounded-lg"><X class="w-5 h-5 text-gray-500" /></button>
          </div>
        </div>
        <iframe :src="previewUrl" class="flex-1 w-full" frameborder="0"></iframe>
      </div>
    </div>

    <!-- ============ SIGN-MODAL (2-Schritt mit Code) ============ -->
    <div v-if="showSignModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[95vh] flex flex-col overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="font-bold text-gray-900 flex items-center gap-2"><PenTool class="w-5 h-5 text-[#FF6F00]" /> NDA online unterschreiben</h3>
          <button @click="closeSignModal" class="p-1.5 hover:bg-gray-100 rounded-lg"><X class="w-5 h-5 text-gray-500" /></button>
        </div>

        <!-- Schritt-Anzeige -->
        <div class="px-6 py-2 bg-gray-50 border-b border-gray-100 flex items-center gap-3 text-xs">
          <div :class="['flex items-center gap-1.5', signStep === 1 ? 'text-[#FF6F00] font-semibold' : 'text-gray-400']">
            <span :class="['w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold', signStep === 1 ? 'bg-[#FF6F00] text-white' : 'bg-gray-200 text-gray-500']">1</span>
            Unterschrift zeichnen
          </div>
          <div class="flex-1 h-px bg-gray-200"></div>
          <div :class="['flex items-center gap-1.5', signStep === 2 ? 'text-[#FF6F00] font-semibold' : 'text-gray-400']">
            <span :class="['w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold', signStep === 2 ? 'bg-[#FF6F00] text-white' : 'bg-gray-200 text-gray-500']">2</span>
            Bestätigungscode
          </div>
        </div>

        <div class="p-6 overflow-y-auto flex-1">
          <!-- ===== Schritt 1: Unterschrift ===== -->
          <template v-if="signStep === 1">
            <p class="text-sm text-gray-600 mb-4">
              Schreibe Deine Unterschrift mit der Maus oder dem Finger in das Feld unten.
              Mit Klick auf „Weiter" bestätigst Du die Vereinbarung digital
              (einfache elektronische Signatur gemäß eIDAS Art. 25 Abs. 1).
            </p>

            <div class="mb-3 flex items-center justify-between">
              <button @click="openPreview('nda')" class="text-xs text-[#0088ba] hover:underline flex items-center gap-1">
                <Eye class="w-3 h-3" /> NDA-Text vor Unterzeichnung ansehen
              </button>
            </div>

            <div class="bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl p-2 mb-3">
              <canvas ref="canvasEl" width="600" height="180" class="bg-white rounded-lg w-full touch-none cursor-crosshair"
                @mousedown="startDraw" @mousemove="draw" @mouseup="endDraw" @mouseleave="endDraw"
                @touchstart="startDrawTouch" @touchmove="drawTouch" @touchend="endDraw"></canvas>
            </div>
            <div class="flex items-center justify-between mb-4">
              <span class="text-xs text-gray-500">Unterschrift hier zeichnen</span>
              <button @click="clearCanvas" class="text-xs text-gray-500 hover:text-gray-700 underline">Zurücksetzen</button>
            </div>

            <label class="flex items-start gap-2 text-xs text-gray-600 mb-4">
              <input type="checkbox" v-model="zustimmung" class="mt-0.5" />
              <span>Ich, <strong>{{ data?.name || data?.firma }}</strong>, bestätige, dass ich berechtigt bin, diese Vereinbarung für <strong>{{ data?.firma || '(Firma)' }}</strong> rechtsverbindlich zu unterzeichnen.</span>
            </label>

            <div class="flex gap-3">
              <button @click="closeSignModal" class="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm">Abbrechen</button>
              <button @click="requestCode" :disabled="!zustimmung || !canvasDirty || codeSending"
                class="flex-1 px-4 py-3 bg-[#FF6F00] text-white rounded-xl text-sm font-semibold hover:bg-[#e56500] disabled:opacity-50">
                {{ codeSending ? 'Sende Code…' : 'Weiter – Code anfordern' }}
              </button>
            </div>
          </template>

          <!-- ===== Schritt 2: Code-Eingabe ===== -->
          <template v-else>
            <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
              <p class="text-sm text-amber-900">
                Wir haben einen 6-stelligen Code an <strong>{{ data?.email }}</strong> geschickt.
                Bitte gib ihn unten ein, um die Signatur abzuschließen.
              </p>
              <p class="text-xs text-amber-700 mt-1">Code ist 30 Minuten gültig. Mail kommt evtl. in den Spam-Ordner.</p>
            </div>

            <label class="block text-xs font-medium text-gray-600 mb-1">Bestätigungscode</label>
            <input v-model="codeInput" type="text" inputmode="numeric" maxlength="6" placeholder="123456"
              class="w-full px-3 py-3 border-2 border-gray-200 rounded-xl text-center text-2xl font-mono tracking-[0.5em] focus:outline-none focus:border-[#FF6F00]" />

            <button @click="requestCode" :disabled="codeSending" class="text-xs text-gray-500 hover:text-[#0088ba] mt-2">
              Code erneut senden
            </button>

            <div class="flex gap-3 mt-5">
              <button @click="signStep = 1" class="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm">← Zurück</button>
              <button @click="submitSign" :disabled="codeInput.length !== 6 || signing"
                class="flex-1 px-4 py-3 bg-[#FF6F00] text-white rounded-xl text-sm font-semibold hover:bg-[#e56500] disabled:opacity-50">
                {{ signing ? 'Wird signiert…' : 'NDA unterschreiben' }}
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { FileText, Download, Upload, CheckCircle2, Calendar, Copy, PenTool, X, Eye } from '@lucide/vue'
import { ndaPublicSendCode } from './api.js'

const token = (() => {
  const m = window.location.pathname.match(/^\/expose-[^\/]+\/([^\/?#]+)/i)
  return m ? m[1] : ''
})()
const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

const loading = ref(true)
const data = ref(null)
const uploading = ref(false)
const copied = ref(false)
const showSignModal = ref(false)
const signing = ref(false)
const zustimmung = ref(false)
const canvasEl = ref(null)
const canvasDirty = ref(false)
const signStep = ref(1)         // 1 = Unterschrift, 2 = Code-Eingabe
const codeSending = ref(false)
const codeInput = ref('')

const ndaUnterzeichnet = computed(() => data.value?.ndaStatus === 'unterzeichnet')

// PDF-Download-URLs: bevorzugt die vom Backend gelieferten Auto-PDFs (immer verfügbar),
// fallback auf manuelle Felder aus Landing-Editor
const exposeDownloadUrl = computed(() => {
  if (data.value?.exposeUrl) return data.value.exposeUrl
  if (data.value?.autoExposePdfUrl) return apiBase.replace(/\/api$/, '') + data.value.autoExposePdfUrl
  return '#'
})
const ndaDownloadUrl = computed(() => {
  if (data.value?.ndaTemplateUrl) return data.value.ndaTemplateUrl
  if (data.value?.autoNdaPdfUrl) return apiBase.replace(/\/api$/, '') + data.value.autoNdaPdfUrl
  return '#'
})

async function load() {
  if (!token) { loading.value = false; return }
  try {
    const res = await fetch(`${apiBase}/expose-public?token=${encodeURIComponent(token)}`)
    if (res.ok) data.value = await res.json()
  } catch (e) { console.error(e) }
  loading.value = false
}
onMounted(load)

function copyMbNr() {
  navigator.clipboard.writeText(data.value.mbNr.toUpperCase())
  copied.value = true
  setTimeout(() => copied.value = false, 1500)
}

// PDF-Preview-Modal (Inline-iframe)
// Wir laden das PDF immer als Blob und bauen eine Object-URL daraus -
// so ist die Vorschau unabhaengig davon ob der Server Content-Type
// korrekt setzt (Robustheit gegen Header-Bugs).
const previewUrl = ref(null)
const previewKind = ref('')
const previewLoading = ref(false)
async function openPreview(kind) {
  previewKind.value = kind
  previewLoading.value = true
  const url = kind === 'nda' ? ndaDownloadUrl.value : exposeDownloadUrl.value
  try {
    const r = await fetch(url)
    if (!r.ok) throw new Error('PDF nicht ladbar: ' + r.status)
    const ab = await r.arrayBuffer()
    previewUrl.value = URL.createObjectURL(new Blob([ab], { type: 'application/pdf' }))
  } catch (e) {
    console.error(e)
    // Fallback: direkter Link
    previewUrl.value = url
  } finally {
    previewLoading.value = false
  }
}
function closePreview() {
  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = null
}

// ========== Canvas-Signatur ==========
let ctx = null
let drawing = false
let lastX = 0, lastY = 0

watch(showSignModal, async (open) => {
  if (open) {
    await nextTick()
    setupCanvas()
  }
})

function setupCanvas() {
  if (!canvasEl.value) return
  ctx = canvasEl.value.getContext('2d')
  ctx.strokeStyle = '#161e2a'
  ctx.lineWidth = 2.5
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  canvasDirty.value = false
  ctx.clearRect(0, 0, canvasEl.value.width, canvasEl.value.height)
}

function clearCanvas() {
  if (!ctx) return
  ctx.clearRect(0, 0, canvasEl.value.width, canvasEl.value.height)
  canvasDirty.value = false
}

function getPos(e) {
  const rect = canvasEl.value.getBoundingClientRect()
  const scaleX = canvasEl.value.width / rect.width
  const scaleY = canvasEl.value.height / rect.height
  return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY }
}

function startDraw(e) { drawing = true; const p = getPos(e); lastX = p.x; lastY = p.y }
function draw(e) {
  if (!drawing) return
  const p = getPos(e)
  ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(p.x, p.y); ctx.stroke()
  lastX = p.x; lastY = p.y; canvasDirty.value = true
}
function endDraw() { drawing = false }

function startDrawTouch(e) { e.preventDefault(); startDraw(e.touches[0]) }
function drawTouch(e) { e.preventDefault(); draw(e.touches[0]) }

function closeSignModal() {
  showSignModal.value = false
  zustimmung.value = false
  canvasDirty.value = false
  signStep.value = 1
  codeInput.value = ''
}

async function requestCode() {
  codeSending.value = true
  try {
    await ndaPublicSendCode(token)
    signStep.value = 2
  } catch (e) {
    alert('Code-Versand fehlgeschlagen: ' + e.message)
  } finally { codeSending.value = false }
}

async function submitSign() {
  if (!canvasDirty.value || !zustimmung.value || codeInput.value.length !== 6) return
  signing.value = true
  try {
    const dataUrl = canvasEl.value.toDataURL('image/png')
    const res = await fetch(`${apiBase}/nda-public-sign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, signatureDataUrl: dataUrl, code: codeInput.value }),
    })
    if (!res.ok) {
      const d = await res.json().catch(() => ({}))
      throw new Error(d.error || `HTTP ${res.status}`)
    }
    closeSignModal()
    await load()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    alert('Signatur fehlgeschlagen: ' + e.message)
  } finally { signing.value = false }
}

// ========== Klassischer File-Upload ==========
async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const reader = new FileReader()
    reader.onload = async () => {
      try {
        const res = await fetch(`${apiBase}/nda-upload`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token, fileName: file.name, fileData: reader.result }),
        })
        if (!res.ok) {
          const d = await res.json().catch(() => ({}))
          throw new Error(d.error || `HTTP ${res.status}`)
        }
        await load()
        window.scrollTo({ top: 0, behavior: 'smooth' })
      } catch (err) {
        alert('Upload fehlgeschlagen: ' + err.message)
      } finally { uploading.value = false }
    }
    reader.readAsDataURL(file)
  } catch (err) {
    uploading.value = false
    alert('Datei konnte nicht gelesen werden.')
  }
}
</script>
