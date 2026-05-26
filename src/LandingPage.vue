<template>
  <div class="min-h-screen bg-gray-50">
    <header class="max-w-3xl mx-auto px-6 pt-6">
      <img src="/e4adade-577b-0f2-5be2-71a313ed1cd2_d023416-88e7-db0f-fedb-6b354cf65_itukv-form.jpg"
        alt="Mike Bergmann · IT-Unternehmen kaufen und verkaufen"
        class="w-full h-auto rounded-2xl block" />
    </header>

    <main class="max-w-3xl mx-auto px-6 py-10">
      <div v-if="loading" class="text-center text-gray-400">Lade Projekt…</div>

      <div v-else-if="!data" class="bg-white rounded-2xl border border-gray-100 p-10 text-center">
        <h2 class="font-bold text-gray-900 mb-2">Projekt nicht gefunden</h2>
        <p class="text-sm text-gray-500">Die angefragte Projektnummer existiert nicht oder ist nicht veröffentlicht.</p>
      </div>

      <div v-else-if="sent" class="bg-white rounded-2xl border border-green-200 bg-green-50 p-10 text-center">
        <CheckCircle2 class="w-12 h-12 text-green-600 mx-auto mb-3" />
        <h2 class="text-xl font-bold text-green-900 mb-2">Vielen Dank für dein Interesse!</h2>
        <p class="text-sm text-green-800">Wir haben dir gerade eine E-Mail an <strong>{{ form.email }}</strong> geschickt – darin findest du den Link zum Exposé-Bereich + NDA.</p>
        <p class="text-xs text-green-700 mt-4">Tipp: Falls die Mail nicht ankommt, schau bitte auch im Spam-Ordner.</p>
      </div>

      <template v-else>
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2 leading-tight">
          {{ data.headline }} <span class="text-gray-400 font-normal">|</span> Projektnummer <span class="font-mono">{{ mbNr.toLowerCase() }}</span>
        </h1>
        <p class="text-lg text-gray-600 mb-8">{{ data.subheadline }}</p>

        <div v-if="data.description" class="bg-white rounded-2xl border border-gray-100 p-6 mb-6 text-gray-700 leading-relaxed whitespace-pre-line">{{ data.description }}</div>

        <!-- Key Facts -->
        <div v-if="data.keyFacts?.length" class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-8">
          <div v-for="(f, idx) in data.keyFacts" :key="idx" class="bg-white rounded-xl border border-gray-100 p-4">
            <div class="text-2xl font-bold text-[#0088ba]">{{ f.wert }}</div>
            <div class="text-sm font-medium text-gray-800 mt-1">{{ f.label }}</div>
            <div v-if="f.beschreib" class="text-xs text-gray-500 mt-1">{{ f.beschreib }}</div>
          </div>
        </div>

        <!-- Formular -->
        <div class="bg-white rounded-2xl border-2 border-[#0088ba]/20 p-8">
          <h2 class="text-xl font-bold text-gray-900 mb-2">Jetzt Formular ausfüllen und Exposé sichern!</h2>
          <p class="text-sm text-gray-600 mb-5">
            Deine Daten werden <strong>streng vertraulich</strong> behandelt und ausschließlich gegenüber dem Verkäufer kommuniziert.
          </p>
          <form @submit.prevent="abschicken" class="space-y-3">
            <input v-model="form.firma" placeholder="Firma *" required class="input" />
            <div class="grid grid-cols-2 gap-3">
              <input v-model="form.vorname" placeholder="Vorname *" required class="input" />
              <input v-model="form.nachname" placeholder="Nachname *" required class="input" />
            </div>
            <input v-model="form.email" type="email" placeholder="E-Mail *" required class="input" />
            <input v-model="form.telefon" placeholder="Mobilnummer *" required class="input" />
            <input v-model="form.website" type="url" placeholder="Website (z.B. https://...) *" required class="input" />
            <input v-model="form.plzOrt" placeholder="Sitz des Unternehmens (PLZ + Ort) *" required class="input" />
            <textarea v-model="form.kommentar" rows="3" placeholder="Was möchtest Du uns mitteilen? (optional)" class="input resize-y"></textarea>

            <label class="flex items-start gap-2 text-xs text-gray-600">
              <input type="checkbox" v-model="form.dsgvo" required class="mt-0.5" />
              <span>Ich willige ein, dass meine Daten vertraulich verarbeitet und ausschließlich für diese Anfrage sowie gegenüber dem Verkäufer kommuniziert werden (DSGVO).</span>
            </label>
            <button type="submit" :disabled="sending || !form.dsgvo" class="w-full px-4 py-3 bg-[#0088ba] text-white rounded-xl font-semibold hover:bg-[#00a0d8] disabled:opacity-50">
              {{ sending ? 'Wird gesendet…' : 'Jetzt absenden' }}
            </button>
            <p v-if="errMsg" class="text-xs text-red-600">{{ errMsg }}</p>
          </form>
        </div>
      </template>
    </main>

    <footer class="text-center text-xs text-gray-400 py-6 border-t border-gray-100 mt-10">
      mibeca GmbH · Schillerstr. 1 · 29525 Uelzen · Gerichtsstand Uelzen
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { CheckCircle2 } from '@lucide/vue'

const mbNr = (() => {
  const m = window.location.pathname.match(/^\/(mb-[^\/?#]+)/i)
  return m ? m[1].toLowerCase() : ''
})()
const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

const loading = ref(true)
const data = ref(null)
const form = ref({ firma: '', vorname: '', nachname: '', email: '', telefon: '', website: '', plzOrt: '', kommentar: '', dsgvo: false })
const sending = ref(false)
const sent = ref(false)
const errMsg = ref('')

async function abschicken() {
  errMsg.value = ''
  sending.value = true
  try {
    const res = await fetch(`${apiBase}/landing-anfrage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mbNr, ...form.value }),
    })
    if (!res.ok) { const d = await res.json().catch(()=>({})); throw new Error(d.error || `HTTP ${res.status}`) }
    const data = await res.json().catch(() => ({}))
    if (data?.exposeUrl) {
      // Direkt zur Exposé-Seite weiterleiten (Bestaetigungs-Mail kommt parallel)
      window.location.href = data.exposeUrl
      return
    }
    sent.value = true
  } catch (e) { errMsg.value = 'Etwas ist schiefgegangen: ' + e.message }
  finally { sending.value = false }
}

onMounted(async () => {
  if (!mbNr) { loading.value = false; return }
  try {
    const res = await fetch(`${apiBase}/landing-public?mbNr=${mbNr}`)
    if (res.ok) data.value = await res.json()
  } catch (e) { console.error(e) }
  loading.value = false
})
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2.5 border-2 border-gray-200 bg-white rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
