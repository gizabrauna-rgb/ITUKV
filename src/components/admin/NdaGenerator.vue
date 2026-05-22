<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">NDA-Vorlage (Stand 2025)</h3>
        <p class="text-xs text-gray-500">Beidseitige Vertraulichkeitsvereinbarung mit Investoren</p>
      </div>
      <div class="flex gap-2">
        <button @click="printPdf" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
          <Printer class="w-4 h-4" /> PDF / Drucken
        </button>
      </div>
    </div>

    <!-- Vorlauf für einzelne Investoren -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-4">
      <h4 class="font-semibold text-sm text-gray-800 mb-3">Variablen für diesen Investor (nur 4 Felder)</h4>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Mandantenfirma (Investor)</label>
          <input v-model="vars.firma" placeholder="z.B. Beispiel IT-Holding GmbH" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Vertreten durch</label>
          <input v-model="vars.vertreten" placeholder="z.B. Max Mustermann (Geschäftsführer)" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Ort der Unterzeichnung</label>
          <input v-model="vars.ort" placeholder="z.B. München" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">Datum</label>
          <input v-model="vars.datum" type="date" class="input" />
        </div>
      </div>
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
      <div class="mb-4 border-l-2 border-[#097e92] pl-4">
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

    <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 mt-4 text-xs text-blue-900">
      <Info class="w-4 h-4 inline mr-1" />
      Diese NDA wird Interessenten auf der öffentlichen Landing-Page <code>anfrage.itukv.de/mb-XX</code> automatisch
      mit ihren Daten gefüllt und kann digital akzeptiert werden (Click-Accept + Audit-Log).
      Vollständige Auto-Signatur folgt im nächsten Schritt.
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Printer, Info } from '@lucide/vue'

const vars = ref({
  firma: '',
  vertreten: '',
  ort: '',
  datum: new Date().toISOString().slice(0, 10),
})

function formatDate(s) {
  if (!s) return '[Datum]'
  try { return new Date(s).toLocaleDateString('de-DE') } catch { return s }
}

function printPdf() {
  window.print()
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]; }
</style>
