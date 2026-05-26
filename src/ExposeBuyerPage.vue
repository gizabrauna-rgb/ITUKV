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
          <template v-if="data.headline">{{ data.headline }} <span class="text-gray-400 font-normal">|</span> </template>Projektnummer <span class="font-mono">{{ data.mbNr.toLowerCase() }}</span>
        </h1>

        <p class="text-lg text-gray-800 mb-6">Hallo {{ data.name || data.firma }},</p>

        <!-- =========== ZUSTAND: VOR NDA-UPLOAD =========== -->
        <template v-if="!ndaUnterzeichnet">
          <!-- Erklär-Text-Block -->
          <section class="bg-white rounded-2xl border border-gray-100 p-7 mb-5">
            <h2 class="text-xl font-bold text-gray-900 mb-3">Das Unternehmen hat Dein Interesse geweckt – Wie geht es jetzt weiter?</h2>
            <p class="text-sm text-gray-700 leading-relaxed mb-4">
              Bevor wir Dir nähere Informationen zum Unternehmen geben können, benötigen wir Dein unterschriebenes NDA.
              Lade Dir die <strong>Vertraulichkeitsvereinbarung (NDA)</strong> unten herunter, unterschreibe sie und lade sie direkt hier wieder hoch.
            </p>

            <div class="bg-amber-50 border-l-4 border-amber-400 p-4 rounded mb-4">
              <p class="text-sm text-amber-900">
                <strong>Wichtig:</strong> Das Exposé und die Termin-Buchung mit Jennifer Kaplan werden erst freigeschaltet, sobald das unterschriebene NDA bei uns eingegangen ist.
              </p>
            </div>

            <p class="text-sm text-gray-700 leading-relaxed mb-5">
              Wenn das vorgestellte IT-Unternehmen Dein Interesse geweckt hat, lade das unterzeichnete NDA bitte
              <strong>schnellstmöglich</strong> hoch.
            </p>

            <h3 class="text-lg font-bold text-gray-900 mt-6 mb-2">Nächster Schritt: Terminbuchung</h3>
            <p class="text-sm text-gray-700 leading-relaxed mb-4">
              Sobald das NDA bei uns eingegangen ist, erhältst Du die Möglichkeit, direkt einen
              <strong>Termin mit unserer M&amp;A-Beraterin Jennifer Kaplan</strong> zu buchen. In diesem Gespräch besprechen wir den weiteren Ablauf sowie alle offenen Fragen.
            </p>

            <h3 class="text-lg font-bold text-gray-900 mt-6 mb-2">Transparenz im Prozess</h3>
            <p class="text-sm text-gray-700 leading-relaxed mb-4">
              Wenn sich im Gespräch herausstellt, dass die Rahmenbedingungen passen, prüfen wir die nächsten Schritte mit dem Verkäufer.
              Nach finaler Freigabe erhältst Du die Kontaktdaten des Zielunternehmens.
            </p>

            <p class="text-sm text-gray-700 leading-relaxed mb-4">
              Bei Rückfragen erreichst Du Jennifer Kaplan unter
              <a href="mailto:jk@mike-bergmann.de" class="text-[#097e92] hover:underline font-medium">jk@mike-bergmann.de</a>.
              Bitte beachte, dass Rückfragen <strong>nur nach Erhalt des unterschriebenen NDA</strong> beantwortet werden können.
            </p>

            <p class="text-sm text-gray-700 leading-relaxed mt-5">Wir freuen uns auf die Zusammenarbeit!</p>
            <p class="text-sm text-gray-700 leading-relaxed">Dein M&amp;A Team der <strong>Mike Bergmann Akademie</strong></p>
          </section>

          <!-- NDA-Aktionen -->
          <section class="bg-white rounded-2xl border-2 border-[#097e92]/30 p-7 mb-5">
            <h2 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <FileText class="w-5 h-5 text-[#097e92]" /> NDA herunterladen, unterschreiben, hochladen
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <a v-if="data.ndaTemplateUrl" :href="data.ndaTemplateUrl" target="_blank"
                class="flex items-center justify-center gap-2 px-4 py-3 bg-white border border-gray-200 text-gray-800 rounded-xl text-sm font-medium hover:bg-gray-50">
                <Download class="w-4 h-4" /> NDA herunterladen
              </a>
              <div v-else class="flex items-center justify-center px-4 py-3 bg-gray-50 border border-gray-200 text-gray-400 rounded-xl text-sm italic">
                NDA-Vorlage folgt per E-Mail
              </div>

              <label class="flex items-center justify-center gap-2 px-4 py-3 bg-[#097e92] text-white rounded-xl text-sm font-semibold hover:bg-[#0a9aaf] cursor-pointer">
                <Upload class="w-4 h-4" /> Unterschriebenes NDA hochladen
                <input type="file" accept="application/pdf,image/*" @change="onFileChange" class="hidden" :disabled="uploading" />
              </label>
            </div>
            <p v-if="uploading" class="text-xs text-amber-700 mt-3 text-center">Lade NDA hoch…</p>
          </section>
        </template>

        <!-- =========== ZUSTAND: NACH NDA-UPLOAD =========== -->
        <template v-else>
          <section class="bg-green-50 border-2 border-green-200 rounded-2xl p-6 mb-5">
            <div class="flex items-start gap-3">
              <CheckCircle2 class="w-7 h-7 text-green-600 flex-shrink-0" />
              <div>
                <h2 class="text-lg font-bold text-green-900 mb-1">NDA erfolgreich hochgeladen</h2>
                <p class="text-sm text-green-800">
                  Vielen Dank für Dein unterschriebenes NDA zu Projekt <strong>{{ data.mbNr.toUpperCase() }}</strong>.
                  Du hast jetzt Zugang zum Exposé und kannst direkt einen Termin mit Jennifer Kaplan buchen.
                </p>
              </div>
            </div>
          </section>

          <!-- Exposé-Download -->
          <section class="bg-white rounded-2xl border border-gray-100 p-7 mb-5">
            <h2 class="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <FileText class="w-5 h-5 text-[#097e92]" /> Exposé zum Unternehmen
            </h2>
            <p class="text-sm text-gray-600 mb-4">Das vollständige anonymisierte Exposé mit allen relevanten Informationen.</p>
            <a v-if="data.exposeUrl" :href="data.exposeUrl" target="_blank"
              class="flex items-center justify-center gap-2 px-4 py-3 bg-[#097e92] text-white rounded-xl text-sm font-semibold hover:bg-[#0a9aaf]">
              <Download class="w-5 h-5" /> Exposé jetzt herunterladen
            </a>
            <p v-else class="text-sm text-gray-500 italic text-center py-3">Das Exposé wird in Kürze hier verfügbar sein.</p>
          </section>

          <!-- Termin-Buchung -->
          <section v-if="data.terminBookingUrl" class="bg-white rounded-2xl border-2 border-[#097e92]/30 p-7 mb-5">
            <h2 class="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Calendar class="w-5 h-5 text-[#097e92]" /> Termin mit Jennifer Kaplan buchen
            </h2>
            <p class="text-sm text-gray-700 mb-4">
              In einem ca. 15-minütigen Gespräch klären wir den weiteren Ablauf und alle offenen Fragen rund um Projekt
              <strong>{{ data.mbNr.toUpperCase() }}</strong>.
            </p>

            <!-- Projektnummer-Hinweis -->
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
              class="flex items-center justify-center gap-2 px-4 py-3 bg-[#097e92] text-white rounded-xl text-sm font-semibold hover:bg-[#0a9aaf]">
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
              <a href="mailto:jk@mike-bergmann.de" class="text-xs text-[#097e92] hover:underline mt-1 inline-block">jk@mike-bergmann.de</a>
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

    <footer class="text-center text-xs text-gray-400 py-6 border-t border-gray-100 mt-10">
      mibeca GmbH · Schillerstr. 1 · 29525 Uelzen · Gerichtsstand Uelzen
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { FileText, Download, Upload, CheckCircle2, Calendar, Copy } from '@lucide/vue'

const token = (() => {
  const m = window.location.pathname.match(/^\/expose-[^\/]+\/([^\/?#]+)/i)
  return m ? m[1] : ''
})()
const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

const loading = ref(true)
const data = ref(null)
const uploading = ref(false)
const copied = ref(false)

const ndaUnterzeichnet = computed(() => data.value?.ndaStatus === 'unterzeichnet')

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
        // Nach erfolgreichem Upload: nach oben scrollen, damit der Erfolg-Block sichtbar ist
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
