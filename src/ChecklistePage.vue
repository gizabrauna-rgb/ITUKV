<template>
  <div class="min-h-screen bg-gray-50">
    <header class="max-w-3xl mx-auto px-6 pt-8 pb-2 text-center">
      <img src="/Favicon_mibeca.png" alt="Mike Bergmann" class="h-14 w-auto mx-auto mb-4" />
      <p class="text-sm font-semibold uppercase tracking-wide text-[#0088ba] mb-2">IT-Unternehmen (ver)kaufen</p>
      <h1 class="text-2xl md:text-3xl font-bold text-gray-900 leading-tight">
        Wie bereit bist Du für einen Unternehmensverkauf?
      </h1>
      <p class="text-gray-600 mt-2">
        Beantworte ehrlich ein paar Fragen und erhalte sofort eine grobe Einschätzung Deines Unternehmenswerts.
      </p>
      <p class="text-sm text-gray-500 mt-3 max-w-xl mx-auto bg-[#0088ba]/5 border border-[#0088ba]/15 rounded-xl px-4 py-3">
        Egal ob Du verkaufen oder zukaufen willst: Wer verkaufsfähig ist, ist auch stark genug, um ein anderes Unternehmen zu übernehmen und zu integrieren. Dieselben Werthebel entscheiden auf beiden Seiten.
      </p>
    </header>

    <main class="max-w-3xl mx-auto px-6 py-8">
      <!-- Ergebnis -->
      <div v-if="result" class="space-y-5">
        <div class="bg-white rounded-2xl border-2 border-[#0088ba]/20 p-8 text-center">
          <CheckCircle2 class="w-12 h-12 text-[#0088ba] mx-auto mb-3" />
          <h2 class="text-xl font-bold text-gray-900 mb-1">
            <template v-if="vorname">Hallo {{ vorname }}, das ist Deine persönliche Einschätzung</template>
            <template v-else>Deine persönliche Einschätzung</template>
          </h2>
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

          <div v-if="result.wertInsight" class="text-left bg-[#0088ba]/5 border border-[#0088ba]/25 rounded-xl p-5 mb-3">
            <p class="text-xs font-semibold text-[#0088ba] uppercase tracking-wide mb-2">Was das für Dich bedeutet</p>
            <p v-if="result.wertInsight.potenzialEur > 0" class="text-2xl md:text-3xl font-extrabold text-gray-900 leading-none mb-2">
              bis zu {{ euro(result.wertInsight.potenzialEur) }} <span class="text-base font-semibold text-gray-500">mehr Kaufpreis</span>
            </p>
            <p class="text-sm text-gray-700 leading-relaxed mb-2">{{ result.wertInsight.hook }}</p>
            <p class="text-sm text-gray-600 leading-relaxed">{{ result.wertInsight.beleg }}</p>
          </div>

          <div v-if="result.insight" class="text-left bg-amber-50 border border-amber-200 rounded-xl p-4 mb-2">
            <p class="text-xs font-semibold text-amber-800 uppercase tracking-wide mb-1">Markt-Einblick</p>
            <p class="text-sm text-amber-900">{{ result.insight }}</p>
          </div>
        </div>

        <!-- Teaser: ungenutzte Werthebel -->
        <div v-if="result.hebel?.length" class="bg-white rounded-2xl border border-gray-100 p-6 md:p-8">
          <div class="flex items-center gap-2 mb-1">
            <TrendingUp class="w-5 h-5 text-[#0088ba]" />
            <h3 class="text-lg font-bold text-gray-900">Hier liegt Dein größtes ungenutztes Potenzial</h3>
          </div>
          <p class="text-sm text-gray-600 mb-5">
            Diese Punkte heben Deinen Faktor – und damit Deinen Kaufpreis – am stärksten. <strong>Was</strong> zählt, siehst Du hier. <strong>Wie</strong> Du es konkret umsetzt, gehen wir gemeinsam durch.
          </p>
          <ul class="space-y-3">
            <li v-for="(h, i) in result.hebel" :key="i" class="flex items-start gap-3 bg-gray-50 rounded-xl p-4">
              <span class="flex-shrink-0 w-6 h-6 rounded-full bg-[#0088ba] text-white text-xs font-bold flex items-center justify-center">{{ i + 1 }}</span>
              <span class="text-sm text-gray-700">{{ h }}</span>
            </li>
          </ul>
          <div class="flex items-center gap-2 mt-4 text-sm text-gray-500">
            <Lock class="w-4 h-4 text-gray-400" />
            <span>Der genaue Fahrplan pro Hebel ist Teil unseres persönlichen Gesprächs.</span>
          </div>
        </div>

        <!-- Vertrauensbelege -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div v-for="b in belege" :key="b.label" class="bg-white rounded-xl border border-gray-100 p-4 text-center">
            <div class="text-xl font-bold text-[#0088ba]">{{ b.zahl }}</div>
            <div class="text-[11px] text-gray-500 mt-1 leading-tight">{{ b.label }}</div>
          </div>
        </div>

        <!-- CTA -->
        <div class="bg-[#161e2a] rounded-2xl p-8 text-center text-white">
          <h3 class="text-xl font-bold mb-2">Lass uns persönlich über Deinen nächsten Schritt sprechen</h3>
          <p class="text-gray-300 text-sm mb-5 max-w-lg mx-auto">
            In einem kostenlosen, vertraulichen Strategiegespräch zeigen wir Dir, wie Du genau diese Hebel ziehst – ob Du verkaufen oder selbst zukaufen willst. Unser Rekord vom ersten Gespräch bis zum Verkauf: 11 Tage.
          </p>
          <a href="https://www.itukv.de" target="_blank" rel="noopener"
            class="inline-block px-6 py-3 bg-[#0088ba] text-white rounded-xl font-semibold hover:bg-[#00a0d8]">
            Kostenloses Strategiegespräch sichern
          </a>
          <p class="text-xs text-gray-400 mt-4">Wir haben Deine Angaben erhalten und melden uns bei Dir.</p>
        </div>

        <!-- Persönlicher Ergebnis-Link -->
        <div v-if="result.ergebnisLink" class="bg-white rounded-2xl border border-gray-100 p-5">
          <div class="flex items-center gap-2 mb-2">
            <Link2 class="w-4 h-4 text-[#0088ba]" />
            <p class="text-sm font-semibold text-gray-900">Dein persönlicher Ergebnis-Link</p>
          </div>
          <p class="text-xs text-gray-500 mb-3">Speicher Dir diesen Link – so kannst Du Deine Einschätzung jederzeit wieder aufrufen.</p>
          <div class="flex gap-2">
            <input :value="result.ergebnisLink" readonly class="input flex-1 text-xs !py-2 text-gray-600" @focus="$event.target.select()" />
            <button type="button" @click="ergebnisLinkKopieren"
              class="flex items-center gap-1.5 px-3 py-2 text-sm border-2 border-gray-200 rounded-xl hover:bg-gray-50 flex-shrink-0">
              <Check v-if="linkKopiert" class="w-4 h-4 text-green-600" />
              <Link2 v-else class="w-4 h-4 text-gray-400" />
              {{ linkKopiert ? 'Kopiert' : 'Kopieren' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Analyse läuft -->
      <div v-else-if="analyzing" class="min-h-[60vh] flex flex-col items-center justify-center text-center py-10">
        <div class="relative w-28 h-28 mb-8">
          <svg class="w-28 h-28 animate-spin" style="animation-duration:1.1s" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="21" fill="none" stroke="#e5e7eb" stroke-width="4" />
            <circle cx="25" cy="25" r="21" fill="none" stroke="#0088ba" stroke-width="4" stroke-linecap="round" stroke-dasharray="80 132" />
          </svg>
          <div class="absolute inset-0 flex items-center justify-center text-xl font-extrabold text-[#0088ba] tabular-nums">{{ analyseProzent }}%</div>
        </div>
        <h2 class="text-xl font-bold text-gray-900 mb-1">Deine Analyse läuft</h2>
        <p class="text-sm text-gray-500 mb-7">Einen Moment – wir werten Deine Angaben gerade aus.</p>
        <ul class="w-full max-w-md space-y-2.5 text-left">
          <li v-for="(s, i) in ANALYSE_STEPS" :key="i" class="flex items-center gap-3 text-sm transition-all duration-300"
              :class="i <= analyseStep ? 'opacity-100' : 'opacity-40'">
            <span class="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center"
              :class="i < analyseStep ? 'bg-green-500 text-white' : (i === analyseStep ? 'bg-[#0088ba] text-white' : 'bg-gray-200')">
              <CheckCircle2 v-if="i < analyseStep" class="w-3.5 h-3.5" />
              <span v-else-if="i === analyseStep" class="w-2 h-2 rounded-full bg-white animate-ping"></span>
            </span>
            <span :class="i <= analyseStep ? 'text-gray-800 font-medium' : 'text-gray-400'">{{ s }}</span>
          </li>
        </ul>
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
                <option value="+49">DE +49</option>
                <option value="+43">AT +43</option>
                <option value="+41">CH +41</option>
              </select>
              <input v-model="form.telefon" placeholder="Mobilnummer" class="input flex-1" inputmode="tel" />
            </div>
            <input v-model="form.website" placeholder="Website (z. B. www.firma.de)" class="input" />
            <input v-model="form.plzOrt" placeholder="Sitz (PLZ + Ort)" class="input" />
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
              <p class="text-sm text-gray-500 mb-2">Grobe bzw. geschätzte Werte genügen – alle Angaben in TEUR (Tausend Euro). Leere Felder sind ok.</p>
              <div class="overflow-x-auto -mx-2 px-2">
                <table class="w-full border-collapse text-sm">
                  <thead>
                    <tr>
                      <th class="text-left font-semibold text-gray-500 pb-2 pr-2 align-bottom w-[42%]"></th>
                      <th v-for="j in form.zahlen.jahre" :key="j.jahr" class="text-center font-semibold text-gray-700 pb-2 px-1 whitespace-nowrap">
                        {{ j.jahr }}<span v-if="j.geplant" class="block text-[10px] font-normal text-gray-400">geplant</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="z in ZAHL_ZEILEN" :key="z.key" class="border-t border-gray-100">
                      <td class="py-1.5 pr-2 text-gray-700 text-[13px] leading-tight">{{ z.label }}</td>
                      <td v-for="j in form.zahlen.jahre" :key="j.jahr" class="py-1.5 px-1">
                        <input v-model="j[z.key]" class="input-cell" inputmode="numeric" />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="text-[11px] text-gray-400 leading-snug pt-1">
                <strong>Bereinigtes EBIT</strong> = Dein Gewinn, wenn Dein GF-Gehalt durch das eines angestellten Geschäftsführers ersetzt und private Kosten (z. B. Gehalt nicht mitarbeitender Angehöriger, privat genutzte Fahrzeuge) herausgerechnet wären.
              </p>
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
          <img src="/Neues Logo Mike Bergmann Beratung.png" alt="Mike Bergmann – Beratung für KI- & IT-Unternehmer" class="h-12 w-auto hover:opacity-80 transition-opacity" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { CheckCircle2, TrendingUp, Lock, Link2, Check } from '@lucide/vue'

// Vertrauensbelege (statische Marktbeweise, keine Live-Daten)
const belege = [
  { zahl: '50+', label: 'begleitete Transaktionen' },
  { zahl: '11', label: 'Tage bis zum Verkauf (Rekord)' },
  { zahl: '6.000+', label: 'Kontakte in der IT-Branche' },
  { zahl: '25', label: 'Käufer- & Investorennetzwerke' },
]

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
  { key: 'f11', gruppe: 'Know-how und Technologien', text: 'Führt Dein Unternehmen regelmäßig neue, zukunftsträchtige Technologien ein (z. B. Cloud, Microsoft Azure, Managed IT Security)?' },
  { key: 'f12', gruppe: 'Know-how und Technologien', text: 'Machst Du mindestens 50 % Deiner Umsätze in spezialisierten Nischen (nicht klassisches Systemhausgeschäft)?' },
  { key: 'f13', gruppe: 'Know-how und Technologien', text: 'Sind mindestens 30 % Deiner Techniker mit hohen Hersteller-Zertifizierungen qualifiziert?' },
]
const gruppen = ['Führung, Personal, Prozesse', 'Vertragseinnahmen und Vertrieb', 'Know-how und Technologien']
const fragenIn = (g) => FRAGEN.filter(f => f.gruppe === g)

// Zahlen-Tabelle: letzte 3 Jahre + laufendes Jahr ("geplant")
const jahrJetzt = new Date().getFullYear()
const JAHRE = [jahrJetzt - 3, jahrJetzt - 2, jahrJetzt - 1, jahrJetzt]
const ZAHL_ZEILEN = [
  { key: 'umsatz', label: 'Umsatz (TEUR)' },
  { key: 'ebit', label: 'Betriebsergebnis / EBIT (TEUR)' },
  { key: 'bereinigtesEbit', label: 'Bereinigtes EBIT (TEUR)' },
  { key: 'gfGehalt', label: 'davon: Eigenes GF-Gehalt (TEUR)' },
  { key: 'mitarbeiter', label: 'Anzahl Mitarbeiter (inkl. GF, Azubis, Teilzeit)' },
  { key: 'vertragsumsatz', label: 'Umsatz aus Verträgen (TEUR)' },
]

const step = ref(1)
const sending = ref(false)
const errMsg = ref('')
const result = ref(null)

// Analyse-Animation
const ANALYSE_STEPS = [
  'Deine Antworten werden ausgewertet',
  'Betriebswirtschaftliche Zahlen werden geprüft',
  'Bereinigtes EBIT & Bewertungsfaktor werden berechnet',
  'Abgleich mit über 6.000 IT-Unternehmen',
  'Deine größten Werthebel werden ermittelt',
  'Deine persönliche Einschätzung wird erstellt',
]
const analyzing = ref(false)
const analyseStep = ref(0)
const analyseProzent = ref(0)

const form = reactive({
  firma: '', name: '', email: '', telefonVorwahl: '+49', telefon: '', website: '', plzOrt: '',
  websiteEinverstaendnis: true,
  antworten: {},
  zahlen: {
    jahre: JAHRE.map(j => ({
      jahr: j, geplant: j === jahrJetzt,
      umsatz: '', ebit: '', bereinigtesEbit: '', gfGehalt: '', mitarbeiter: '', vertragsumsatz: '',
    })),
  },
  motive: { motivation: '', zeitpunkt: '', begleitungMonate: '', wunschpreis: '', erwartetPreis: '' },
  dsgvo: false,
})

const vorname = computed(() => (result.value?.name || '').trim().split(/\s+/)[0] || '')
const linkKopiert = ref(false)
async function ergebnisLinkKopieren() {
  try {
    await navigator.clipboard.writeText(result.value?.ergebnisLink || location.href)
    linkKopiert.value = true
    setTimeout(() => { linkKopiert.value = false }, 2000)
  } catch {}
}

// Individueller Ergebnis-Link: ?r=<token> -> Ergebnis erneut laden
const ladeErgebnis = ref(false)
onMounted(async () => {
  const token = new URLSearchParams(location.search).get('r')
  if (!token) return
  ladeErgebnis.value = true
  try {
    const res = await fetch(`${apiBase}/checkliste-result?token=${encodeURIComponent(token)}`)
    if (res.ok) {
      result.value = await res.json()
      window.scrollTo({ top: 0 })
    }
  } catch {}
  finally { ladeErgebnis.value = false }
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
  errMsg.value = ''
  sending.value = true
  analyzing.value = true
  analyseStep.value = 0
  analyseProzent.value = 0
  window.scrollTo({ top: 0, behavior: 'smooth' })

  // Analyse-Animation: Schritte durchrattern + Prozent hochzählen
  const stepMs = 700
  const gesamtMs = ANALYSE_STEPS.length * stepMs
  const stepTimer = setInterval(() => {
    if (analyseStep.value < ANALYSE_STEPS.length - 1) analyseStep.value++
  }, stepMs)
  const prozentTimer = setInterval(() => {
    if (analyseProzent.value < 96) analyseProzent.value++
  }, Math.floor(gesamtMs / 96))
  const minDauer = new Promise(r => setTimeout(r, gesamtMs))

  let website = (form.website || '').trim()
  if (website && !/^https?:\/\//i.test(website)) website = 'https://' + website
  const localNumber = (form.telefon || '').trim().replace(/^0+/, '')
  const telefon = localNumber ? `${form.telefonVorwahl} ${localNumber}` : ''

  let apiResult = null, fehler = ''
  try {
    const res = await fetch(`${apiBase}/checkliste-submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        kontakt: { firma: form.firma, name: form.name, email: form.email, telefon, website, plzOrt: form.plzOrt },
        websiteEinverstaendnis: form.websiteEinverstaendnis,
        antworten: form.antworten,
        zahlen: { jahre: form.zahlen.jahre },
        motive: form.motive,
        dsgvo: form.dsgvo,
      }),
    })
    if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.error || `HTTP ${res.status}`) }
    apiResult = await res.json()
  } catch (e) {
    fehler = 'Etwas ist schiefgegangen: ' + e.message
  }

  // Animation mindestens komplett durchlaufen lassen
  await minDauer
  clearInterval(stepTimer)
  clearInterval(prozentTimer)
  analyseStep.value = ANALYSE_STEPS.length
  analyseProzent.value = 100
  await new Promise(r => setTimeout(r, 450))

  analyzing.value = false
  sending.value = false
  if (fehler) { errMsg.value = fehler; return }
  result.value = apiResult
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2.5 border-2 border-gray-200 bg-white rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
.input-cell { @apply w-full min-w-[52px] px-1.5 py-1.5 border border-gray-200 bg-white rounded-lg text-sm text-center focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
