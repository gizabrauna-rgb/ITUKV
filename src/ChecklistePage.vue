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
          <p v-if="result.firma" class="text-sm text-gray-500 mb-5">für {{ firmaMitArtikel(result.firma) }}</p>

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

        <!-- Netzwerk-Hinweis: reine Zahl aus dem Datenstamm (keine Namen).
             Zukauf -> IT-Firmen im Umkreis · Verkauf/Nachfolge/... -> aktive Investoren -->
        <div v-if="result.netzwerk?.text" class="bg-[#0088ba]/5 border-2 border-[#0088ba]/20 rounded-2xl p-5 md:p-6">
          <div class="flex items-start gap-3">
            <component :is="result.netzwerk.typ === 'firmen' ? MapPin : Users"
              class="w-6 h-6 text-[#0088ba] flex-shrink-0 mt-0.5" />
            <div>
              <p class="text-sm md:text-base text-gray-800 font-semibold leading-relaxed">{{ result.netzwerk.text }}</p>
              <p class="text-xs text-gray-500 mt-1.5">Anonymisiert aus unserem Datenstamm – Namen nennen wir selbstverständlich erst im persönlichen Gespräch.</p>
            </div>
          </div>
        </div>

        <!-- Teaser: ungenutzte Werthebel (Ueberschrift/Text je nach Ziel individuell) -->
        <div v-if="result.hebel?.length" class="bg-white rounded-2xl border border-gray-100 p-6 md:p-8">
          <div class="flex items-center gap-2 mb-1">
            <TrendingUp class="w-5 h-5 text-[#0088ba]" />
            <h3 class="text-lg font-bold text-gray-900">{{ zielTexte.titel }}</h3>
          </div>
          <p class="text-sm text-gray-600 mb-5">{{ zielTexte.sub }}</p>
          <ul class="space-y-3">
            <li v-for="(h, i) in result.hebel" :key="i" class="flex items-start gap-3 bg-gray-50 rounded-xl p-4">
              <span class="flex-shrink-0 w-6 h-6 rounded-full bg-[#0088ba] text-white text-xs font-bold flex items-center justify-center">{{ i + 1 }}</span>
              <span class="text-sm text-gray-700">{{ h }}</span>
            </li>
          </ul>
          <div class="mt-5 rounded-xl bg-[#0088ba]/5 border border-[#0088ba]/15 p-4">
            <p class="text-sm text-gray-700 leading-relaxed">{{ zielTexte.gespraech }}</p>
          </div>
        </div>

        <!-- Vertrauensbelege -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div v-for="b in belege" :key="b.label" class="bg-white rounded-xl border border-gray-100 p-4 text-center">
            <div class="text-xl font-bold text-[#0088ba]">{{ b.zahl }}</div>
            <div class="text-[11px] text-gray-500 mt-1 leading-tight">{{ b.label }}</div>
          </div>
        </div>

        <!-- Fallback-Button, falls der Kalender einmal nicht laedt -->
        <div v-if="!CAL_ENABLED" class="bg-white rounded-2xl border border-gray-100 p-6 text-center">
          <a href="https://www.itukv.de" target="_blank" rel="noopener"
            class="inline-block px-6 py-3 bg-[#0088ba] text-white rounded-xl font-semibold hover:bg-[#00a0d8]">
            Kostenloses Strategiegespräch sichern
          </a>
          <p class="text-xs text-gray-400 mt-4">Kostenlos · vertraulich · unverbindlich – wir melden uns bei Dir.</p>
        </div>

        <!-- Terminbuchung als Popup (Cal.com element-click) – kompakte Karte, kein langes Scrollen -->
        <div v-if="CAL_ENABLED" class="bg-[#0088ba] rounded-2xl p-6 md:p-8 text-center text-white">
          <h3 class="text-xl font-bold mb-1">Buch Dir Dein kostenloses 20-Minuten-Erstgespräch</h3>
          <p class="text-sm text-white/80 mb-5">Kostenlos · vertraulich · unverbindlich · telefonisch</p>
          <button type="button"
            data-cal-namespace="checkliste-itukv"
            :data-cal-link="CAL_LINK"
            :data-cal-config="calConfig"
            class="inline-flex items-center gap-2 px-7 py-3.5 bg-white text-[#0088ba] rounded-xl font-bold hover:bg-gray-50 text-base">
            <CalendarClock class="w-5 h-5" /> Jetzt Termin auswählen
          </button>
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
          <div v-if="smsAngefragt" class="flex items-center gap-2 mt-3 text-xs text-green-700 bg-green-50 border border-green-100 rounded-lg px-3 py-2">
            <Check class="w-4 h-4 flex-shrink-0" />
            <span>Wir haben Dir diesen Link zusätzlich per SMS an Deine Nummer geschickt.</span>
          </div>

          <!-- PDF-Download der kompletten ausgefüllten Checkliste -->
          <div v-if="pdfUrl" class="mt-4 pt-4 border-t border-gray-100">
            <p class="text-xs text-gray-500 mb-2">Du willst Deine Checkliste schwarz auf weiß? Lad Dir Deine komplette Auswertung mit allen Antworten als PDF herunter.</p>
            <a :href="pdfUrl" target="_blank" rel="noopener"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-semibold text-[#0088ba] bg-[#f2f9fc] border-2 border-[#cfe7f2] rounded-xl hover:bg-[#e6f4fa]">
              <FileDown class="w-4 h-4" />
              Checkliste als PDF herunterladen
            </a>
          </div>
        </div>

        <!-- Rechtlicher Hinweis -->
        <p class="text-[11px] leading-relaxed text-gray-400 text-center px-2">
          Diese Einschätzung ist eine unverbindliche Ersteinschätzung auf Basis Deiner Angaben und ersetzt
          kein Wertgutachten. Der tatsächliche Kaufpreis hängt von einer detaillierten Prüfung und den
          Marktbedingungen ab.
        </p>
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
        <p class="text-sm text-gray-500 mb-4">Einen Moment – wir werten Deine Angaben gerade aus.</p>
        <div class="flex items-center gap-2 mb-7 px-4 py-2 rounded-lg bg-[#0088ba]/10 text-[#0088ba] text-sm font-medium">
          <Clock class="w-4 h-4 flex-shrink-0" />
          <span>Das dauert 1–3 Minuten. Bitte lass dieses Fenster so lange geöffnet.</span>
        </div>
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
          <div v-for="s in STEPS_TOTAL" :key="s" class="flex-1 h-1.5 rounded-full" :class="s <= step ? 'bg-[#0088ba]' : 'bg-gray-200'"></div>
        </div>

        <form @submit.prevent="onNext">
          <!-- SCHRITT 1: Kontakt -->
          <div v-show="step === 1" class="bg-white rounded-2xl border border-gray-100 p-6 space-y-3">
            <h2 class="text-lg font-bold text-gray-900 mb-1">Über Dich & Dein Unternehmen</h2>
            <p class="text-sm text-gray-500 mb-3">Damit wir Dir Deine Einschätzung persönlich zuordnen können.</p>
            <input v-model="form.firma" placeholder="Firma *" class="input" />
            <div class="flex gap-2">
              <input v-model="form.vorname" placeholder="Vorname *" class="input flex-1" />
              <input v-model="form.nachname" placeholder="Nachname *" class="input flex-1" />
            </div>
            <input v-model="form.email" type="email" placeholder="E-Mail *" class="input" />
            <div class="flex gap-2">
              <select v-model="form.telefonVorwahl" class="input !w-auto" style="flex:0 0 auto;">
                <option value="+49">DE +49</option>
                <option value="+43">AT +43</option>
                <option value="+41">CH +41</option>
              </select>
              <input v-model="form.telefon" placeholder="Mobilnummer *" class="input flex-1" inputmode="tel" />
            </div>
            <label v-if="form.telefon.trim()" class="flex items-start gap-2 text-xs text-gray-600">
              <input type="checkbox" v-model="form.smsEinverstaendnis" class="mt-0.5" />
              <span>Schickt mir meinen persönlichen Ergebnis-Link zusätzlich per SMS – ausschließlich an meine Mobilnummer. Meine Ergebnisse enthalten vertrauliche Daten und sind nur über diesen persönlichen Link abrufbar.</span>
            </label>
            <input v-model="form.website" placeholder="Website (z. B. www.firma.de)" class="input" />
            <input v-model="form.plzOrt" placeholder="Sitz (PLZ + Ort) *" class="input" />
            <label class="flex items-start gap-2 text-xs text-gray-600 pt-1">
              <input type="checkbox" v-model="form.dsgvo" class="mt-0.5" />
              <span>Ich willige ein, dass meine Angaben vertraulich verarbeitet werden, um meine persönliche Einschätzung zu erstellen und mit mir zu besprechen, und dass ich dazu kontaktiert werden darf. Es gilt die <a href="https://www.mike-bergmann-akademie.de/pages/datenschutz" target="_blank" rel="noopener" class="underline hover:text-[#0088ba]">Datenschutzerklärung</a>.</span>
            </label>
          </div>

          <!-- SCHRITT 2: Ziel -->
          <div v-show="step === 2" class="bg-white rounded-2xl border border-gray-100 p-6">
            <h2 class="text-lg font-bold text-gray-900 mb-1">Was ist Dein Ziel?</h2>
            <p class="text-sm text-gray-500 mb-4">Damit wir Deine Einschätzung und das Gespräch genau auf Dich ausrichten. Wähle, was am ehesten passt.</p>
            <div class="grid sm:grid-cols-2 gap-3">
              <button v-for="z in ZIEL_OPTIONEN" :key="z.key" type="button" @click="form.ziel = z.key"
                class="text-left border-2 rounded-xl p-4 transition"
                :class="form.ziel === z.key ? 'border-[#0088ba] bg-[#0088ba]/5' : 'border-gray-200 hover:border-[#0088ba]/40'">
                <span class="block font-semibold text-sm text-gray-900">{{ z.label }}</span>
                <span class="block text-xs text-gray-500 mt-0.5">{{ z.desc }}</span>
              </button>
            </div>
          </div>

          <!-- SCHRITT 3–5: Ja/Nein je Themenblock -->
          <div v-for="gs in JA_NEIN_STEPS" :key="gs.gruppe" v-show="step === gs.step"
            class="bg-white rounded-2xl border border-gray-100 p-6">
            <h3 class="text-base font-bold text-gray-900 mb-3">{{ gs.gruppe }}</h3>
            <div class="space-y-3">
              <div v-for="f in fragenIn(gs.gruppe)" :key="f.key" class="flex items-start justify-between gap-4">
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

          <!-- SCHRITT 6: Zahlen + Motive -->
          <div v-show="step === 6" class="space-y-4">
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
              <h3 class="text-base font-bold text-gray-900 mb-1">{{ motivConfig.heading }}</h3>
              <textarea v-model="form.motive.motivation" rows="2" :placeholder="motivConfig.motivation" class="input resize-y"></textarea>
              <div class="grid grid-cols-2 gap-3">
                <input v-for="f in motivConfig.felder" :key="f.key" v-model="form.motive[f.key]" :placeholder="f.ph" class="input" />
              </div>
            </div>
          </div>

          <p v-if="errMsg" class="text-sm text-red-600 mt-3">{{ errMsg }}</p>

          <!-- Navigation -->
          <div class="flex items-center justify-between mt-5">
            <button type="button" v-if="step > 1" @click="step--" class="px-4 py-2.5 text-gray-600 font-medium hover:text-gray-900">Zurück</button>
            <span v-else></span>
            <button type="submit" :disabled="sending || !stepGueltig"
              class="px-6 py-3 bg-[#0088ba] text-white rounded-xl font-semibold hover:bg-[#00a0d8] disabled:opacity-50 disabled:cursor-not-allowed">
              {{ step < STEPS_TOTAL ? 'Weiter' : (sending ? 'Wird ausgewertet…' : 'Auswertung anzeigen') }}
            </button>
          </div>
          <p v-if="hinweisText" class="text-right text-xs text-gray-500 mt-2">{{ hinweisText }}</p>
          <p class="text-center text-xs text-gray-400 mt-4">Kostenlos · in wenigen Minuten · diskret &amp; unverbindlich</p>
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
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { CheckCircle2, TrendingUp, Link2, Check, CalendarClock, Clock, FileDown, MapPin, Users } from '@lucide/vue'

// Vertrauensbelege (statische Marktbeweise, keine Live-Daten)
const belege = [
  { zahl: '50+', label: 'begleitete Transaktionen' },
  { zahl: '11', label: 'Tage bis zum Verkauf (Rekord)' },
  { zahl: '6.000+', label: 'Kontakte in der IT-Branche' },
  { zahl: '25', label: 'Käufer- & Investorennetzwerke' },
]

const apiBase = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'

// Download-Link fuer die ausgefuellte Checkliste als PDF (ueber den Ergebnis-Token).
const pdfUrl = computed(() => {
  const token = result.value?.resultToken
  return token ? `${apiBase}/checkliste-pdf?r=${encodeURIComponent(token)}` : ''
})

// Direkter Buchungskalender (Cal.com Inline-Embed) auf der Ergebnisseite.
const CAL_ENABLED = true
const CAL_NAMESPACE = 'checkliste-itukv'
const CAL_LINK = 'team/mike-bergmann-akademie/checkliste-itukv'
const CAL_BRAND = '#02aef1'
let calScriptGeladen = false

function ladeCalLoader() {
  // Cal.com Loader-Snippet (einmalig). Danach steht window.Cal bereit.
  if (calScriptGeladen || window.Cal) { calScriptGeladen = true; return }
  ;(function (C, A, L) { let p = function (a, ar) { a.q.push(ar) }; let d = C.document; C.Cal = C.Cal || function () { let cal = C.Cal; let ar = arguments; if (!cal.loaded) { cal.ns = {}; cal.q = cal.q || []; d.head.appendChild(d.createElement('script')).src = A; cal.loaded = true } if (ar[0] === L) { const api = function () { p(api, arguments) }; const namespace = ar[1]; api.q = api.q || []; if (typeof namespace === 'string') { cal.ns[namespace] = cal.ns[namespace] || api; p(cal.ns[namespace], ar); p(cal, ['initNamespace', namespace]) } else p(cal, ar); return } p(cal, ar) } })(window, 'https://app.cal.com/embed/embed.js', 'init')
  calScriptGeladen = true
}

// Cal-Popup-Konfiguration inkl. vorausgefuellter Felder aus dem ersten Formular.
// Wird als data-cal-config an den Buchungs-Button gehaengt (Klick oeffnet Overlay).
const calConfig = computed(() => {
  const cfg = { layout: 'month_view', useSlotsViewOnSmallScreen: 'true' }
  const name = (vollerName.value || result.value?.name || '').trim()
  const email = (form.email || '').trim()
  const localNumber = (form.telefon || '').trim().replace(/^0+/, '')
  const telefonE164 = localNumber ? `${form.telefonVorwahl}${localNumber}` : ''
  if (name) cfg.name = name
  if (email) cfg.email = email
  // Telefonisches Erstgespraech: Mobilnummer aus Schritt 1 vorbefuellen.
  // Nur attendeePhoneNumber setzen - das befuellt das Telefonfeld sauber.
  // KEIN location-Override: sonst zeigt Cal den Rohwert "phone" als Ort an
  // und blendet das Eingabefeld aus.
  if (telefonE164) cfg.attendeePhoneNumber = telefonE164
  // Kontext fuer Jenny als Notiz
  const firma = (form.firma || result.value?.firma || '').trim()
  const faktor = result.value?.auswertung?.faktor
  const notiz = []
  if (firma) notiz.push(`Firma: ${firma}`)
  if (faktor) notiz.push(`Checklisten-Faktor: ${faktor}`)
  if (notiz.length) cfg.notes = notiz.join(' · ')
  return JSON.stringify(cfg)
})

async function zeigeCalKalender() {
  if (!CAL_ENABLED) return
  ladeCalLoader()
  await nextTick()
  if (!window.Cal) return
  // Einmalig initialisieren; der Button oeffnet danach das Popup per Klick.
  if (window.__calChecklisteInit) return
  window.__calChecklisteInit = true
  window.Cal('init', CAL_NAMESPACE, { origin: 'https://app.cal.com' })
  window.Cal.config = window.Cal.config || {}
  window.Cal.config.forwardQueryParams = true
  window.Cal.ns[CAL_NAMESPACE]('ui', {
    cssVarsPerTheme: { light: { 'cal-brand': CAL_BRAND }, dark: { 'cal-brand': CAL_BRAND } },
    hideEventTypeDetails: false, layout: 'month_view',
  })
}

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

// Ziel-Kachel (Teil 2): Verkauf / Zukauf / Nachfolge / Beteiligung / nur Wert / offen
const ZIEL_OPTIONEN = [
  { key: 'verkauf', label: 'Verkauf', desc: 'Ich möchte mein Unternehmen ganz verkaufen.' },
  { key: 'zukauf', label: 'Zukauf (Wachstum)', desc: 'Ich möchte wachsen und ein Unternehmen übernehmen.' },
  { key: 'nachfolge', label: 'Nachfolge', desc: 'Ich suche eine geregelte Nachfolge.' },
  { key: 'beteiligung', label: 'Beteiligung / Teilverkauf', desc: 'Ich möchte einen Investor oder Partner an Bord holen.' },
  { key: 'wert', label: 'Nur den Wert wissen', desc: 'Ich möchte erstmal eine Standortbestimmung.' },
  { key: 'offen', label: 'Noch offen', desc: 'Ich bin noch am Anfang meiner Überlegungen.' },
]

// Abfrage-Schritte: 1 Daten · 2 Ziel · 3-5 Ja/Nein je Themenblock · 6 Zahlen+Motive
const STEPS_TOTAL = 6
const JA_NEIN_STEPS = gruppen.map((g, i) => ({ step: 3 + i, gruppe: g }))

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

// Eindeutige ID fuer diesen Ausfuell-Vorgang. Damit wird nach jeder Kachel
// zwischengespeichert (checkliste-draft) und der finale Absenden-Datensatz
// ueberschreibt denselben Eintrag – so entstehen keine Doppel-Eintraege und
// kein Lead geht verloren, wenn jemand mittendrin abspringt.
const draftToken = (typeof crypto !== 'undefined' && crypto.randomUUID)
  ? crypto.randomUUID()
  : String(Date.now()) + Math.random().toString(16).slice(2)
// Beim Aufruf eines fertigen Ergebnis-Links (?r=) NICHT zwischenspeichern.
const istWiederaufruf = ref(false)

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
  firma: '', vorname: '', nachname: '', email: '', telefonVorwahl: '+49', telefon: '', website: '', plzOrt: '',
  ziel: '',
  websiteEinverstaendnis: false,
  smsEinverstaendnis: false,
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
// Vor- und Nachname zu einem vollstaendigen Namen zusammensetzen (fuer Speicherung/Versand)
const vollerName = computed(() => `${form.vorname} ${form.nachname}`.replace(/\s+/g, ' ').trim())

// Passenden Artikel je nach Rechtsform/Firmierung waehlen ("fuer die GmbH", "fuer den e.V.", oder ohne Artikel bei reinen Namen)
function firmaMitArtikel(firma) {
  const f = (firma || '').trim()
  if (!f) return ''
  const low = f.toLowerCase().replace(/[.\s]+$/, '')
  if (/e\.?\s?v\.?$/.test(low)) return `den ${f}`           // eingetragener Verein -> fuer den
  if (/(gmbh|mbh|\bug\b|\bag\b|\bkg\b|kgaa|\bohg\b|\bgbr\b|\bse\b|\beg\b|\bltd\b|\bllc\b|\binc\b)/.test(low)) {
    return `die ${f}`                                        // GmbH, AG, KG, UG ... -> fuer die
  }
  return f                                                    // reiner Name / e.K. -> ohne Artikel
}
// Ergebnis-Texte je nach gewaehltem Ziel (Verkauf, Zukauf, Nachfolge ...).
// Individualisiert Ueberschrift, Unterzeile und den Gespraechs-Hinweis.
const ZIEL_TEXTE = {
  verkauf: {
    titel: 'Hier liegt Dein größtes ungenutztes Verkaufspotenzial',
    sub: 'Diese Punkte heben Deinen Faktor – und damit Deinen Verkaufspreis – am stärksten. Was zählt, siehst Du hier. Wie Du es vor dem Verkauf konkret umsetzt, gehen wir gemeinsam durch.',
    gespraech: 'Wer diese Hebel vor dem Verkauf zieht, holt beim Kaufpreis oft deutlich mehr heraus. Genau da setzen wir an: Im kostenlosen Erstgespräch zeigen wir Dir, welcher Hebel bei Dir am schnellsten wirkt und wie ein Verkauf diskret und begleitet abläuft.',
  },
  zukauf: {
    titel: 'Hier liegt Dein größtes Potenzial für den nächsten Zukauf',
    sub: 'Wer verkaufsfähig ist, ist auch stark genug, ein anderes Unternehmen zu übernehmen. Diese Punkte machen Dich als Käufer attraktiv und finanzierbar. Was zählt, siehst Du hier – wie Du gezielt zukaufst, gehen wir gemeinsam durch.',
    gespraech: 'Für einen erfolgreichen Zukauf zählt, dass Dein eigenes Unternehmen stark aufgestellt ist und Du die richtigen Ziele findest. Im kostenlosen Erstgespräch zeigen wir Dir, wie wir passende Übernahmekandidaten identifizieren und den Kauf für Dich begleiten.',
  },
  nachfolge: {
    titel: 'Hier liegt Dein größtes Potenzial für eine geregelte Nachfolge',
    sub: 'Je unabhängiger Dein Unternehmen von Dir läuft, desto reibungsloser die Nachfolge – und desto höher der Wert. Was zählt, siehst Du hier. Wie Du die Übergabe vorbereitest, gehen wir gemeinsam durch.',
    gespraech: 'Eine gute Nachfolge braucht Vorlauf. Im kostenlosen Erstgespräch zeigen wir Dir, wie Du Dein Unternehmen übergabefähig machst und einen passenden Nachfolger findest – diskret und Schritt für Schritt begleitet.',
  },
  beteiligung: {
    titel: 'Hier liegt Dein größtes Potenzial für einen Teilverkauf',
    sub: 'Diese Punkte machen Dich für Investoren und Partner attraktiv – und heben Deinen Unternehmenswert. Was zählt, siehst Du hier. Wie Du einen Partner an Bord holst, gehen wir gemeinsam durch.',
    gespraech: 'Ob Investor oder Partner: Ein Teilverkauf gelingt am besten, wenn Dein Unternehmen sauber aufgestellt und der Wert belastbar ist. Im kostenlosen Erstgespräch zeigen wir Dir, wie so ein Einstieg strukturiert und zu Deinen Bedingungen abläuft.',
  },
  wert: {
    titel: 'Hier liegt Dein größtes ungenutztes Potenzial',
    sub: 'Diese Punkte heben Deinen Faktor – und damit Deinen Unternehmenswert – am stärksten. Was zählt, siehst Du hier. Wie Du es konkret umsetzt, gehen wir gemeinsam durch.',
    gespraech: 'Deine Zahlen sind ein guter Startpunkt. Im kostenlosen Erstgespräch ordnen wir Deinen Wert realistisch ein und zeigen Dir, welche Hebel ihn am schnellsten steigern – ganz ohne Verkaufsdruck.',
  },
  offen: {
    titel: 'Hier liegt Dein größtes ungenutztes Potenzial',
    sub: 'Diese Punkte heben Deinen Faktor – und damit Deinen Kaufpreis – am stärksten. Was zählt, siehst Du hier. Wie Du es konkret umsetzt, gehen wir gemeinsam durch.',
    gespraech: 'Egal, wohin die Reise geht – verkaufen, zukaufen oder erst mal Klarheit gewinnen: Im kostenlosen Erstgespräch sortieren wir gemeinsam Deine Optionen und zeigen Dir, welcher nächste Schritt für Dich wirklich sinnvoll ist.',
  },
}
const zielTexte = computed(() => ZIEL_TEXTE[result.value?.ziel] || ZIEL_TEXTE.offen)

// Letzte Kachel ("Ziele & Rahmenbedingungen") an das gewaehlte Ziel anpassen.
// Ueberschrift, Freitext-Frage und die vier Felder heissen je Ziel unterschiedlich;
// nicht passende Felder (z. B. Kaufpreis bei "Nur Wert wissen") fallen weg.
const MOTIV_CONFIG = {
  verkauf: {
    heading: 'Deine Verkaufsziele & Rahmenbedingungen',
    motivation: 'Warum willst Du verkaufen? (z. B. Alter, neue Ziele, Gesundheit)',
    felder: [
      { key: 'zeitpunkt', ph: 'Wann willst Du verkaufen?' },
      { key: 'begleitungMonate', ph: 'Begleitung nach Verkauf (Monate)' },
      { key: 'wunschpreis', ph: 'Wunsch-Verkaufspreis' },
      { key: 'erwartetPreis', ph: 'Realistisch erwarteter Preis heute' },
    ],
  },
  zukauf: {
    heading: 'Deine Zukaufsziele & Rahmenbedingungen',
    motivation: 'Was ist Dein Ziel beim Zukauf? (z. B. Wachstum, neue Region, Fachkräfte, Kundenstamm)',
    felder: [
      { key: 'zeitpunkt', ph: 'Wann willst Du zukaufen?' },
      { key: 'begleitungMonate', ph: 'Wunschgröße des Ziels (Umsatz oder Mitarbeiter)' },
      { key: 'wunschpreis', ph: 'Budget für den Zukauf' },
      { key: 'erwartetPreis', ph: 'Bevorzugte Region oder Nische' },
    ],
  },
  nachfolge: {
    heading: 'Deine Nachfolge-Ziele & Rahmenbedingungen',
    motivation: 'Warum steht die Nachfolge an? (z. B. Alter, Ruhestand, neue Pläne)',
    felder: [
      { key: 'zeitpunkt', ph: 'Wann soll die Übergabe stattfinden?' },
      { key: 'begleitungMonate', ph: 'Wie lange willst Du begleiten? (Monate)' },
      { key: 'wunschpreis', ph: 'Wunsch-Verkaufspreis' },
      { key: 'erwartetPreis', ph: 'Realistisch erwarteter Preis heute' },
    ],
  },
  beteiligung: {
    heading: 'Deine Ziele für den Teilverkauf & Rahmenbedingungen',
    motivation: 'Was erhoffst Du Dir vom Partner/Investor? (z. B. Kapital, Know-how, Entlastung)',
    felder: [
      { key: 'zeitpunkt', ph: 'Wann willst Du den Einstieg?' },
      { key: 'begleitungMonate', ph: 'Welchen Anteil willst Du abgeben? (z. B. in %)' },
      { key: 'wunschpreis', ph: 'Wunsch-Preis für den Anteil' },
      { key: 'erwartetPreis', ph: 'Erwartete Unternehmensbewertung' },
    ],
  },
  wert: {
    heading: 'Deine Ziele & Rahmenbedingungen',
    motivation: 'Wofür brauchst Du die Einschätzung? (z. B. Standortbestimmung, Planung)',
    felder: [
      { key: 'zeitpunkt', ph: 'Ist ein Schritt geplant? Wenn ja, wann?' },
      { key: 'erwartetPreis', ph: 'Deine eigene Werteinschätzung heute (optional)' },
    ],
  },
  offen: {
    heading: 'Deine Ziele & Rahmenbedingungen',
    motivation: 'Was treibt Dich an? (z. B. Alter, Wachstum, Wettbewerbsdruck, Klarheit)',
    felder: [
      { key: 'zeitpunkt', ph: 'Wann könnte ein Schritt anstehen?' },
      { key: 'erwartetPreis', ph: 'Grobe eigene Werteinschätzung (optional)' },
    ],
  },
}
const motivConfig = computed(() => MOTIV_CONFIG[form.ziel] || MOTIV_CONFIG.offen)

const linkKopiert = ref(false)
const smsAngefragt = ref(false)
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
  istWiederaufruf.value = true
  ladeErgebnis.value = true
  try {
    const res = await fetch(`${apiBase}/checkliste-result?token=${encodeURIComponent(token)}`)
    if (res.ok) {
      result.value = await res.json()
      window.scrollTo({ top: 0 })
      zeigeCalKalender()
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

// Zwischenspeichern nach jeder Kachel (fire-and-forget). Legt KEINEN Kontakt an –
// das passiert erst beim vollstaendigen Absenden. keepalive: Anfrage laeuft auch
// noch, wenn die Person die Seite direkt danach schliesst.
function speichereEntwurf() {
  if (istWiederaufruf.value) return
  const email = (form.email || '').trim()
  if (!email) return  // ohne E-Mail keine Zuordnung moeglich
  let website = (form.website || '').trim()
  if (website && !/^https?:\/\//i.test(website)) website = 'https://' + website
  const localNumber = (form.telefon || '').trim().replace(/^0+/, '')
  const telefon = localNumber ? `${form.telefonVorwahl} ${localNumber}` : ''
  try {
    fetch(`${apiBase}/checkliste-draft`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      keepalive: true,
      body: JSON.stringify({
        draftToken,
        kontakt: { firma: form.firma, name: vollerName.value, vorname: form.vorname, nachname: form.nachname, email, telefon, website, plzOrt: form.plzOrt },
        ziel: form.ziel,
        antworten: form.antworten,
        zahlen: { jahre: form.zahlen.jahre },
        motive: form.motive,
        lastStep: step.value,
      }),
    }).catch(() => {})
  } catch {}
}

// Prueft, ob der aktuelle Schritt vollstaendig ausgefuellt ist. Solange das
// nicht der Fall ist, bleibt der "Weiter"-Knopf ausgegraut/gesperrt.
// Freiwillige Kaestchen (SMS, Website-Einverstaendnis) blockieren NICHT.
const stepGueltig = computed(() => {
  if (step.value === 1) {
    const emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())
    return !!(form.firma.trim() && form.vorname.trim() && form.nachname.trim()
      && emailOk && form.telefon.trim() && form.plzOrt.trim() && form.dsgvo)
  }
  if (step.value === 2) return !!form.ziel
  const gs = JA_NEIN_STEPS.find(s => s.step === step.value)
  if (gs) return fragenIn(gs.gruppe).every(f => typeof form.antworten[f.key] === 'boolean')
  return true
})

// Kleiner Hinweis unter dem "Weiter"-Knopf, solange der Schritt unvollstaendig
// ist – damit klar ist, WARUM der Knopf noch ausgegraut bleibt.
const hinweisText = computed(() => {
  if (stepGueltig.value) return ''
  if (step.value === 1) {
    const emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())
    const felderOk = form.firma.trim() && form.vorname.trim() && form.nachname.trim()
      && emailOk && form.telefon.trim() && form.plzOrt.trim()
    if (!felderOk) return 'Bitte fülle alle Pflichtfelder (*) aus, damit es weitergeht.'
    return 'Bitte bestätige noch die Einwilligung zur Datenverarbeitung.'
  }
  if (step.value === 2) return 'Bitte wähle Dein Ziel aus.'
  if (JA_NEIN_STEPS.some(s => s.step === step.value)) return 'Bitte beantworte alle Fragen mit Ja oder Nein.'
  return ''
})

async function onNext() {
  errMsg.value = ''
  if (step.value === 1) {
    if (!form.firma.trim() || !form.vorname.trim() || !form.nachname.trim() || !form.email.trim() || !form.telefon.trim() || !form.plzOrt.trim()) {
      errMsg.value = 'Bitte fülle alle Pflichtfelder aus (Firma, Vor- und Nachname, E-Mail, Mobilnummer und Sitz).'; return
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())) {
      errMsg.value = 'Bitte gib eine gültige E-Mail-Adresse ein.'; return
    }
  }
  if (step.value === 2 && !form.ziel) {
    errMsg.value = 'Bitte wähle Dein Ziel aus.'; return
  }
  // Ja/Nein-Kacheln (Schritt 3–5): jede Frage muss beantwortet sein
  const gs = JA_NEIN_STEPS.find(s => s.step === step.value)
  if (gs) {
    const fehlt = fragenIn(gs.gruppe).some(f => typeof form.antworten[f.key] !== 'boolean')
    if (fehlt) {
      errMsg.value = 'Bitte beantworte alle Fragen mit Ja oder Nein.'; return
    }
  }
  // Nach jeder abgeschlossenen Kachel den Stand sichern.
  speichereEntwurf()
  if (step.value < STEPS_TOTAL) { step.value++; window.scrollTo({ top: 0, behavior: 'smooth' }); return }
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
        draftToken,
        kontakt: { firma: form.firma, name: vollerName.value, vorname: form.vorname, nachname: form.nachname, email: form.email, telefon, website, plzOrt: form.plzOrt },
        ziel: form.ziel,
        websiteEinverstaendnis: form.websiteEinverstaendnis,
        smsEinverstaendnis: form.smsEinverstaendnis && !!telefon,
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
  zeigeCalKalender()

  // Ergebnis-Link per SMS zuschicken (fire-and-forget, nur bei Einwilligung + Nummer)
  if (form.smsEinverstaendnis && telefon && apiResult?.resultToken) {
    smsAngefragt.value = true
    fetch(`${apiBase}/checkliste-send-sms`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: apiResult.resultToken }),
    }).catch(() => {})
  }
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2.5 border-2 border-gray-200 bg-white rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
.input-cell { @apply w-full min-w-[52px] px-1.5 py-1.5 border border-gray-200 bg-white rounded-lg text-sm text-center focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
