<template>
  <div class="min-h-screen bg-gray-50">
    <header>
      <img src="/e4adade-577b-0f2-5be2-71a313ed1cd2_d023416-88e7-db0f-fedb-6b354cf65_itukv-form.jpg"
        alt="Mike Bergmann · IT-Unternehmen kaufen und verkaufen"
        class="w-full h-auto block" />
      <div class="bg-[#161e2a] text-white py-2 px-6 text-center text-xs">
        Exposé-Bereich · Projektnummer <span class="font-mono font-bold">{{ (data?.mbNr || 'mb-xxx').toUpperCase() }}</span>
      </div>
    </header>

    <main class="max-w-3xl mx-auto px-6 py-10">
      <div v-if="loading" class="text-center text-gray-400">Lade…</div>
      <div v-else-if="!data" class="bg-white rounded-2xl border border-gray-100 p-10 text-center">
        <h2 class="font-bold text-gray-900 mb-2">Zugriff nicht möglich</h2>
        <p class="text-sm text-gray-500">Der Link ist ungültig oder abgelaufen. Bitte melde dich erneut über die Landing-Page an.</p>
      </div>

      <template v-else>
        <h1 class="text-2xl font-bold text-gray-900 mb-1">Hallo {{ data.name || data.firma }},</h1>
        <p class="text-base text-gray-600 mb-6">{{ data.headline || `Dein Exposé-Bereich zu Projekt ${data.mbNr.toUpperCase()}` }}</p>

        <!-- Schritt 1: NDA -->
        <section :class="['rounded-2xl border-2 p-6 mb-4', ndaUnterzeichnet ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50']">
          <div class="flex items-start gap-3 mb-3">
            <component :is="ndaUnterzeichnet ? CheckCircle2 : FileText" :class="['w-7 h-7 flex-shrink-0', ndaUnterzeichnet ? 'text-green-600' : 'text-amber-600']" />
            <div class="flex-1">
              <h2 class="text-lg font-bold mb-1" :class="ndaUnterzeichnet ? 'text-green-900' : 'text-amber-900'">
                Schritt 1: Vertraulichkeitsvereinbarung (NDA)
              </h2>
              <p v-if="ndaUnterzeichnet" class="text-sm text-green-800">
                NDA wurde erfolgreich hochgeladen am {{ formatDate(data.ndaUploadedAt) }}. Du hast jetzt vollen Zugriff.
              </p>
              <p v-else class="text-sm text-amber-800">
                Wichtig: Weitere Informationen zum Unternehmen erhältst Du erst nach Upload des unterschriebenen NDA.
              </p>
            </div>
          </div>

          <div v-if="!ndaUnterzeichnet" class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
            <a v-if="data.ndaTemplateUrl" :href="data.ndaTemplateUrl" target="_blank" class="flex items-center justify-center gap-2 px-4 py-3 bg-white border border-amber-300 text-amber-900 rounded-xl text-sm font-medium hover:bg-amber-100">
              <Download class="w-4 h-4" /> NDA herunterladen
            </a>
            <label class="flex items-center justify-center gap-2 px-4 py-3 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf] cursor-pointer">
              <Upload class="w-4 h-4" /> Unterschriebenes NDA hochladen
              <input type="file" accept="application/pdf,image/*" @change="onFileChange" class="hidden" :disabled="uploading" />
            </label>
          </div>
          <p v-if="uploading" class="text-xs text-amber-700 mt-2 text-center">Lade NDA hoch…</p>
        </section>

        <!-- Schritt 2: Exposé (erst nach NDA) -->
        <section v-if="ndaUnterzeichnet" class="bg-white rounded-2xl border border-gray-100 p-6 mb-4">
          <div class="flex items-start gap-3 mb-3">
            <FileText class="w-7 h-7 text-[#097e92] flex-shrink-0" />
            <div class="flex-1">
              <h2 class="text-lg font-bold text-gray-900 mb-1">Schritt 2: Exposé herunterladen</h2>
              <p class="text-sm text-gray-600">Das vollständige Exposé mit allen relevanten Informationen.</p>
            </div>
          </div>
          <a v-if="data.exposeUrl" :href="data.exposeUrl" target="_blank" class="flex items-center justify-center gap-2 px-4 py-3 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf]">
            <Download class="w-4 h-4" /> Exposé herunterladen
          </a>
          <p v-else class="text-sm text-gray-500 italic">Das Exposé wird in Kürze hier verfügbar sein.</p>
        </section>

        <!-- Schritt 3: Termin buchen (erst nach NDA) -->
        <section v-if="ndaUnterzeichnet && data.terminBookingUrl" class="bg-white rounded-2xl border border-gray-100 p-6 mb-4">
          <div class="flex items-start gap-3 mb-3">
            <Calendar class="w-7 h-7 text-[#097e92] flex-shrink-0" />
            <div class="flex-1">
              <h2 class="text-lg font-bold text-gray-900 mb-1">Schritt 3: Termin mit Jennifer Kaplan buchen</h2>
              <p class="text-sm text-gray-600">In ca. 15 Minuten klären wir den weiteren Ablauf und alle offenen Fragen.</p>
            </div>
          </div>

          <!-- Projektnummer-Hinweis -->
          <div class="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4 flex items-center justify-between gap-3">
            <div class="text-sm">
              <strong class="text-amber-900">Wichtig:</strong>
              <span class="text-amber-800"> Bitte gib bei der Buchung als Anlass die Projektnummer </span>
              <code class="font-mono font-bold bg-white border border-amber-300 px-2 py-0.5 rounded mx-1">{{ data.mbNr.toUpperCase() }}</code>
              <span class="text-amber-800">an.</span>
            </div>
            <button @click="copyMbNr" class="text-xs flex items-center gap-1 px-2 py-1 bg-white border border-amber-300 text-amber-900 rounded hover:bg-amber-100 flex-shrink-0">
              <Copy class="w-3 h-3" /> {{ copied ? 'Kopiert' : 'Kopieren' }}
            </button>
          </div>

          <a :href="data.terminBookingUrl" target="_blank" class="flex items-center justify-center gap-2 px-4 py-3 bg-[#097e92] text-white rounded-xl text-sm font-semibold hover:bg-[#0a9aaf]">
            <Calendar class="w-4 h-4" /> Termin jetzt buchen
          </a>

          <ul class="text-xs text-gray-500 mt-4 space-y-1">
            <li>· Ob das Unternehmen zu Deiner Zukauf-Strategie passt</li>
            <li>· Deine konkreten Zukauf-Visionen — damit wir diese mit dem Profil abgleichen können</li>
            <li>· Den weiteren Ablauf des Prozesses</li>
            <li>· Ob ein Folgegespräch direkt mit dem Verkäufer sinnvoll ist</li>
          </ul>
        </section>

        <!-- Hinweis-Text wenn noch kein NDA -->
        <section v-if="!ndaUnterzeichnet" class="bg-white rounded-2xl border border-gray-100 p-6">
          <h3 class="font-semibold text-gray-800 mb-2">Wie geht es weiter?</h3>
          <p class="text-sm text-gray-600 leading-relaxed">
            Sobald das NDA bei uns eingegangen ist, hast Du die Möglichkeit, das vollständige Exposé herunterzuladen und
            direkt einen Termin mit unserer M&amp;A-Beraterin <strong>Jennifer Kaplan</strong> zu buchen.
            In diesem Gespräch besprechen wir den weiteren Ablauf sowie alle offenen Fragen.
          </p>
          <p class="text-xs text-gray-500 mt-3">
            Bei Rückfragen erreichst Du Jennifer Kaplan unter <a href="mailto:jk@mike-bergmann.de" class="text-[#097e92] hover:underline">jk@mike-bergmann.de</a> —
            bitte beachte, dass tiefergehende Fragen erst nach Erhalt des unterschriebenen NDA beantwortet werden.
          </p>
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

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

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
