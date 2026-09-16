<template>
  <div class="min-h-screen bg-gray-50">
    <header class="max-w-3xl mx-auto px-6 pt-8 pb-2 text-center">
      <img src="/mibeca_google_4zu1_LOGO.jpg" alt="Mike Bergmann" class="h-12 w-auto mx-auto mb-4" />
      <h1 class="text-2xl md:text-3xl font-bold text-gray-900 leading-tight">
        Wie verkaufsbereit ist Dein IT-Unternehmen?
      </h1>
      <p class="text-gray-600 mt-2">
        Beantworte ehrlich ein paar Fragen und erhalte sofort eine grobe Einschätzung Deines Unternehmenswerts.
      </p>
    </header>

    <main class="max-w-3xl mx-auto px-6 py-8">
      <!-- Ergebnis -->
      <div v-if="result" class="space-y-5">
        <div class="bg-white rounded-2xl border-2 border-[#0088ba]/20 p-8 text-center">
          <CheckCircle2 class="w-12 h-12 text-[#0088ba] mx-auto mb-3" />
          <h2 class="text-xl font-bold text-gray-900 mb-1">Deine persönliche Einschätzung</h2>
          <p v-if="result.firma" class="text-sm text-gray-500 mb-5">für {{ result.firma }}</p>

          <p class="text-gray-700 leading-relaxed mb-6">{{ result.ansprache }}</p>

          <div class="grid grid-cols-3 gap-3 mb-6">
            <div class="bg-gray-50 rounded-xl p-4">
              <div class="text-2xl font-bold text-[#0088ba]">{{ result.auswertung.faktor }}</div>
              <div class="text-xs text-gray-500 mt-1">Faktor</div>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <div class="text-2xl font-bold text-[#0088ba]">{{ result.auswertung.jaCount }}/{{ result.auswertung.fragenGesamt }}</div>
              <div class="text-xs text-gray-500 mt-1">Kriterien erfüllt</div>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <div class="text-2xl font-bold text-[#0088ba]">{{ euroKurz(result.auswertung.wertMidEur) }}</div>
              <div class="text-xs text-gray-500 mt-1">grober Wert</div>
            </div>
          </div>

          <div v-if="result.auswertung.wertMidEur > 0" class="bg-[#0088ba]/5 border border-[#0088ba]/20 rounded-xl p-5 mb-4">
            <p class="text-sm text-gray-600 mb-1">Geschätzte Wert-Bandbreite</p>
            <p class="text-lg font-bold text-gray-900">{{ euro(result.auswertung.wertMinEur) }} – {{ euro(result.auswertung.wertMaxEur) }}</p>
            <p class="text-xs text-gray-400 mt-2">Grobe Orientierung (bereinigtes EBIT × Faktor). Erhebliche Abweichungen nach oben und unten sind möglich.</p>
          </div>

          <div v-if="result.schwerpunkte?.length" class="flex flex-wrap justify-center gap-2 mb-4">
            <span v-for="s in result.schwerpunkte" :key="s" class="text-xs bg-gray-100 text-gray-700 px-3 py-1 rounded-full">{{ s }}</span>
          </div>

          <div v-if="result.insight" class="text-left bg-amber-50 border border-amber-200 rounded-xl p-4 mb-2">
            <p class="text-xs font-semibold text-amber-800 uppercase tracking-wide mb-1">Markt-Einblick</p>
            <p class="text-sm text-amber-900">{{ result.insight }}</p>
          </div>
        </div>

        <div class="bg-[#161e2a] rounded-2xl p-8 text-center text-white">
          <h3 class="text-xl font-bold mb-2">Lass uns persönlich darüber sprechen</h3>
          <p class="text-gray-300 text-sm mb-5 max-w-lg mx-auto">
            In einem kostenlosen Strategiegespräch zeigen wir Dir, wie Du Deinen Unternehmenswert vor einem Verkauf gezielt steigerst.
          </p>
          <a href="https://www.itukv.de" target="_blank" rel="noopener"
            class="inline-block px-6 py-3 bg-[#0088ba] text-white rounded-xl font-semibold hover:bg-[#00a0d8]">
            Kostenloses Strategiegespräch sichern
          </a>
          <p class="text-xs text-gray-400 mt-4">Wir haben Deine Angaben erhalten und melden uns bei Dir.</p>
        </div>
      </div>

      <!-- Formular -->
      <template v-else>
        <!-- Fortschritt -->
        <div class="flex items-center gap-2 mb-6">
          <div v-for="s in 3" :key="s" class="flex-1 h-1.5 rounded-full" :class="s <= step ? 'bg-[#0088ba]' : 'bg-gray-200'"></div>
        </div>

        <form @submit.prevent="onNext">
          <!-- SCHRITT 1: Kontakt -->
          <div v-show="step === 1" class="bg-white rounded-2xl border border-gray-100 p-6 space-y-3">
            <h2 class="text-lg font-bold text-gray-900 mb-1">Über Dich & Dein Unternehmen</h2>
            <p class="text-sm text-gray-500 mb-3">Damit wir Dir Deine Einschätzung persönlich zuordnen können.</p>
            <input v-model="form.firma" placeholder="Firma *" class="input" />
            <input v-model="form.name" placeholder="Dein Name *" class="input" />
            <input v-model="form.email" type="email" placeholder="E-Mail *" class="input" />
            <div class="flex gap-2">
              <select v-model="form.telefonVorwahl" class="input !w-auto" style="flex:0 0 auto;">
                <option value="+49">🇩🇪 +49</option>
                <option value="+43">🇦🇹 +43</option>
                <option value="+41">🇨🇭 +41</option>
              </select>
              <input v-model="form.telefon" placeholder="Mobilnummer" class="input flex-1" inputmode="tel" />
            </div>
            <input v-model="form.website" placeholder="Website (z. B. www.firma.de)" class="input" />
            <input v-model="form.plzOrt" placeholder="Sitz (PLZ + Ort)" class="input" />
            <input v-model="form.mitarbeiter" placeholder="Anzahl Mitarbeiter (inkl. GF, Azubis, Teilzeit)" class="input" inputmode="numeric" />
            <label class="flex items-start gap-2 text-xs text-gray-600 pt-1">
              <input type="checkbox" v-model="form.websiteEinverstaendnis" class="mt-0.5" />
              <span>Ihr dürft Euch meine öffentlich zugängliche Website ansehen, um mir eine passendere Einschätzung zu geben.</span>
            </label>
          </div>

          <!-- SCHRITT 2: Ja/Nein -->
          <div v-show="step === 2" class="space-y-4">
            <div v-for="gruppe in gruppen" :key="gruppe" class="bg-white rounded-2xl border border-gray-100 p-6">
              <h3 class="text-base font-bold text-gray-900 mb-3">{{ gruppe }}</h3>
              <div class="space-y-3">
                <div v-for="f in fragenIn(gruppe)" :key="f.key" class="flex items-start justify-between gap-4">
                  <p class="text-sm text-gray-700 flex-1">{{ f.text }}</p>
                  <div class="flex gap-1 flex-shrink-0">
                    <button type="button" @click="form.antworten[f.key] = true"
                      class="px-3 py-1.5 rounded-lg text-xs font-semibold border-2 transition"
                      :class="form.antworten[f.key] === true ? 'bg-green-500 border-green-500 text-white' : 'border-gray-200 text-gray-500 hover:border-green-300'">Ja</button>
                    <button type="button" @click="form.antworten[f.key] = false"
                      class="px-3 py-1.5 rounded-lg text-xs font-semibold border-2 transition"
                      :class="form.antworten[f.key] === false ? 'bg-gray-400 border-gray-400 text-white' : 'border-gray-200 text-gray-500 hover:border-gray-300'">Nein</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- SCHRITT 3: Zahlen + Motive -->
          <div v-show="step === 3" class="space-y-4">
            <div class="bg-white rounded-2xl border border-gray-100 p-6 space-y-3">
              <h3 class="text-base font-bold text-gray-900 mb-1">Betriebswirtschaftliche Zahlen</h3>
              <p class="text-sm text-gray-500 mb-2">Grobe Werte genügen – alle Angaben in TEUR (Tausend Euro).</p>
              <div class="grid grid-cols-2 gap-3">
                <input v-model="form.zahlen.umsatz" placeholder="Umsatz (TEUR)" class="input" inputmode="numeric" />
                <input v-model="form.zahlen.ebit" placeholder="EBIT (TEUR)" class="input" inputmode="numeric" />
                <input v-model="form.zahlen.bereinigtesEbit" placeholder="Bereinigtes EBIT (TEUR)" class="input" inputmode="numeric" />
                <input v-model="form.zahlen.vertragsumsatz" placeholder="Umsatz aus Verträgen (TEUR)" class="input" inputmode="numeric" />
              </div>
              <p class="text-[11px] text-gray-400 leading-snug">
                Bereinigtes EBIT = Gewinn, wenn Dein Gehalt durch das eines angestellten GF ersetzt und private Kosten herausgerechnet wären.
              </p>
              <div>
                <label class="text-sm text-gray-700 block mb-1">Wie entwickelt sich Dein EBIT?</label>
                <select v-model="form.zahlen.ebitTrend" class="input">
                  <option value="">Bitte wählen</option>
                  <option value="wachsend">Es wächst kontinuierlich</option>
                  <option value="stabil">Es bleibt etwa stabil</option>
                  <option value="ruecklaeufig">Es ist rückläufig</option>
                </select>
              </div>
            </div>

            <div class="bg-white rounded-2xl border border-gray-100 p-6 space-y-3">
              <h3 class="text-base font-bold text-gray-900 mb-1">Deine Verkaufsziele</h3>
              <textarea v-model="form.motive.motivation" rows="2" placeholder="Was ist Deine Motivation zu verkaufen? (z. B. Alter, neue Interessen, Wettbewerbsdruck)" class="input resize-y"></textarea>
              <div class="grid grid-cols-2 gap-3">
                <input v-model="form.motive.zeitpunkt" placeholder="Wann planst Du den Verkauf?" class="input" />
                <input v-model="form.motive.begleitungMonate" placeholder="Begleitung nach Verkauf (Monate)" class="input" />
                <input v-model="form.motive.wunschpreis" placeholder="Wunsch-Kaufpreis (sofort Ja)" class="input" />
                <input v-model="form.motive.erwartetPreis" placeholder="Erwarteter Kaufpreis heute" class="input" />
              </div>
            </div>

            <label class="flex items-start gap-2 text-xs text-gray-600">
              <input type="checkbox" v-model="form.dsgvo" class="mt-0.5" />
              <span>Ich willige ein, dass meine Daten vertraulich verarbeitet und ausschließlich zur Bearbeitung meiner Anfrage genutzt werden (DSGVO).</span>
            </label>
          </div>

          <p v-if="errMsg" class="text-sm text-red-600 mt-3">{{ errMsg }}</p>

          <!-- Navigation -->
          <div class="flex items-center justify-between mt-5">
            <button type="button" v-if="step > 1" @click="step--" class="px-4 py-2.5 text-gray-600 font-medium hover:text-gray-900">Zurück</button>
            <span v-else></span>
            <button type="submit" :disabled="sending"
              class="px-6 py-3 bg-[#0088ba] text-white rounded-xl font-semibold hover:bg-[#00a0d8] disabled:opacity-50">
              {{ step < 3 ? 'Weiter' : (sending ? 'Wird ausgewertet…' : 'Auswertung anzeigen') }}
            </button>
          </div>
        </form>
      </template>
    </main>

    <footer class="border-t border-gray-100 mt-10 bg-white">
      <div class="max-w-3xl mx-auto px-6 py-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <a href="https://www.itukv.de" target="_blank" rel="noopener">
          <img src="/mibeca_google_4zu1_LOGO.jpg" alt="mibeca" class="h-10 w-auto hover:opacity-80 transition-opacity" />
        </a>
        <div class="flex flex-wrap gap-4 text-xs text-gray-500">
          <a href="https://www.mike-bergmann-akademie.de/pages/impressum" target="_blank" rel="noopener" class="hover:text-[#0088ba]">Impressum</a>
          <a href="https://www.mike-bergmann-akademie.de/pages/datenschutz" target="_blank" rel="noopener" class="hover:text-[#0088ba]">Datenschutz</a>
        </div>
      </div>
      <div class="text-center text-[11px] text-gray-400 pb-4">© {{ new Date().getFullYear() }} mibeca GmbH · Schillerstr. 1 · 29525 Uelzen</div>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { CheckCircle2 } from '@lucide/vue'

const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

const FRAGEN = [
  { key: 'f1', gruppe: 'Führung, Personal, Prozesse', text: 'Gibt es schon ein Führungsteam, das das Tagesgeschäft ohne den Chef führen kann?' },
  { key: 'f2', gruppe: 'Führung, Personal, Prozesse', text: 'Würde das Unternehmen auch ohne Dich genauso weiterlaufen, ohne dass die Zahlen schlechter würden?' },
  { key: 'f3', gruppe: 'Führung, Personal, Prozesse', text: 'Sind Prozesse und Strukturen so ausgelegt, dass jeder Mitarbeiter an jeder Position direkt ersetzbar ist?' },
  { key: 'f4', gruppe: 'Führung, Personal, Prozesse', text: 'Ist das gesamte Unternehmenswissen in einer Wissensdatenbank (Videos, Checklisten, Anleitungen) dokumentiert?' },
  { key: 'f5', gruppe: 'Führung, Personal, Prozesse', text: 'Gibt es eine aktive Mitarbeitergewinnung, die planbar neue Mitarbeiter ins Unternehmen bringt?' },
  { key: 'f6', gruppe: 'Vertragseinnahmen und Vertrieb', text: 'Gibt es ein schlüssiges, skalierbares Vertragswerk für Managed Services, das die Aufnahme neuer Kunden ermöglicht?' },
  { key: 'f7', gruppe: 'Vertragseinnahmen und Vertrieb', text: 'Deckt Dein Unternehmen mehr als 70 % aller Kosten durch regelmäßige Vertragseinnahmen (z. B. Managed Services, IT-Flatrates)?' },
  { key: 'f8', gruppe: 'Vertragseinnahmen und Vertrieb', text: 'Gibt es eigene Vertriebsmitarbeiter, die nur Vertrieb machen (keine Techniker)?' },
  { key: 'f9', gruppe: 'Vertragseinnahmen und Vertrieb', text: 'Gibt es eine eigene Marketingabteilung, die selbständig Konzepte für Neukunden, Mitarbeiter und Sichtbarkeit entwickelt und umsetzt?' },
  { key: 'f10', gruppe: 'Vertragseinnahmen und Vertrieb', text: 'Gibt es eine aktive Neukundengewinnung durch Online-Marketing, die planbar neue Kunden bringt („Online-Marketing-Maschine“)?' },
  { key: 'f11', gruppe: 'KnowHow und Technologien', text: 'Führt Dein Unternehmen regelmäßig neue, zukunftsträchtige Technologien ein (z. B. Cloud, Microsoft Azure, Managed IT Security)?' },
  { key: 'f12', gruppe: 'KnowHow und Technologien', text: 'Machst Du mindestens 50 % Deiner Umsätze in spezialisierten Nischen (nicht klassisches Systemhausgeschäft)?' },
  { key: 'f13', gruppe: 'KnowHow und Technologien', text: 'Sind mindestens 30 % Deiner Techniker mit hohen Hersteller-Zertifizierungen qualifiziert?' },
]
const gruppen = ['Führung, Personal, Prozesse', 'Vertragseinnahmen und Vertrieb', 'KnowHow und Technologien']
const fragenIn = (g) => FRAGEN.filter(f => f.gruppe === g)

const step = ref(1)
const sending = ref(false)
const errMsg = ref('')
const result = ref(null)

const form = reactive({
  firma: '', name: '', email: '', telefonVorwahl: '+49', telefon: '', website: '', plzOrt: '', mitarbeiter: '',
  websiteEinverstaendnis: true,
  antworten: {},
  zahlen: { umsatz: '', ebit: '', bereinigtesEbit: '', vertragsumsatz: '', ebitTrend: '' },
  motive: { motivation: '', zeitpunkt: '', begleitungMonate: '', wunschpreis: '', erwartetPreis: '' },
  dsgvo: false,
})

function euro(n) {
  if (!n || n <= 0) return '–'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n)
}
function euroKurz(n) {
  if (!n || n <= 0) return '–'
  if (n >= 1000000) return (n / 1000000).toLocaleString('de-DE', { maximumFractionDigits: 1 }) + ' Mio €'
  if (n >= 1000) return Math.round(n / 1000) + ' TEUR'
  return euro(n)
}

async function onNext() {
  errMsg.value = ''
  if (step.value === 1) {
    if (!form.firma.trim() || !form.name.trim() || !form.email.trim()) {
      errMsg.value = 'Bitte fülle Firma, Name und E-Mail aus.'; return
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())) {
      errMsg.value = 'Bitte gib eine gültige E-Mail-Adresse ein.'; return
    }
  }
  if (step.value < 3) { step.value++; window.scrollTo({ top: 0, behavior: 'smooth' }); return }
  await abschicken()
}

async function abschicken() {
  if (!form.dsgvo) { errMsg.value = 'Bitte stimme der Datenverarbeitung zu.'; return }
  sending.value = true
  let website = (form.website || '').trim()
  if (website && !/^https?:\/\//i.test(website)) website = 'https://' + website
  const localNumber = (form.telefon || '').trim().replace(/^0+/, '')
  const telefon = localNumber ? `${form.telefonVorwahl} ${localNumber}` : ''
  try {
    const res = await fetch(`${apiBase}/checkliste-submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        kontakt: { firma: form.firma, name: form.name, email: form.email, telefon, website, plzOrt: form.plzOrt, mitarbeiter: form.mitarbeiter },
        websiteEinverstaendnis: form.websiteEinverstaendnis,
        antworten: form.antworten,
        zahlen: form.zahlen,
        motive: form.motive,
        dsgvo: form.dsgvo,
      }),
    })
    if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.error || `HTTP ${res.status}`) }
    result.value = await res.json()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    errMsg.value = 'Etwas ist schiefgegangen: ' + e.message
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2.5 border-2 border-gray-200 bg-white rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
