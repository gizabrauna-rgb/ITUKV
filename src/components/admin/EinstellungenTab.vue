<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-6">Einstellungen</h2>

    <!-- Webhook-Block -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden mb-6">
      <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="font-semibold text-gray-900 flex items-center gap-2">
            <Webhook class="w-4 h-4 text-[#0088ba]" />
            Webhook für neue Kunden
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">Damit kann dein bestehendes CRM-System neue Kunden automatisch ins ITUKV-Dashboard übertragen</p>
        </div>
      </div>

      <div v-if="loading" class="p-6 text-center text-sm text-gray-400">Lade…</div>
      <div v-else class="p-5 space-y-4">

        <!-- URL -->
        <div>
          <label class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5 block">Endpoint URL</label>
          <div class="flex items-center gap-2">
            <code class="flex-1 px-3 py-2 bg-gray-50 border border-gray-100 rounded-lg text-sm font-mono text-gray-700 truncate">{{ data.url }}</code>
            <button @click="copy(data.url, 'url')" class="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600">
              <Check v-if="copied === 'url'" class="w-4 h-4 text-green-500" />
              <Copy v-else class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Token -->
        <div>
          <label class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5 block">Geheim-Token (im Header X-Webhook-Token)</label>
          <div class="flex items-center gap-2">
            <code class="flex-1 px-3 py-2 bg-gray-50 border border-gray-100 rounded-lg text-sm font-mono text-gray-700 truncate">
              {{ showToken ? data.token : '••••••••••••••••••••••••••••••••' }}
            </code>
            <button @click="showToken = !showToken" class="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600">
              <Eye v-if="!showToken" class="w-4 h-4" />
              <EyeOff v-else class="w-4 h-4" />
            </button>
            <button @click="copy(data.token, 'token')" class="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600">
              <Check v-if="copied === 'token'" class="w-4 h-4 text-green-500" />
              <Copy v-else class="w-4 h-4" />
            </button>
          </div>
          <p class="text-xs text-red-500 mt-1.5 flex items-center gap-1">
            <AlertTriangle class="w-3 h-3" />
            Token geheim halten – damit kann jeder Kunden in deinem Dashboard anlegen
          </p>
        </div>

        <!-- Pflichtfelder -->
        <div class="bg-blue-50 border border-blue-100 rounded-xl p-4">
          <div class="text-xs font-semibold text-blue-900 mb-2 flex items-center gap-1.5">
            <Info class="w-3.5 h-3.5" /> Verhalten
          </div>
          <ul class="text-xs text-blue-800 space-y-1 list-disc list-inside">
            <li>Mit <code class="bg-blue-100 px-1 rounded">email</code> → wird als <strong>Kontakt</strong> im CRM angelegt</li>
            <li>Mit <code class="bg-blue-100 px-1 rounded">mbNr</code> (z.B. <code>mb-401</code>) → wird als <strong>Target</strong> (Verkaufsmandat) angelegt</li>
            <li>Existiert die E-Mail / mb-Nummer bereits → wird der bestehende Eintrag aktualisiert</li>
          </ul>
        </div>

        <!-- Beispiel-Snippet -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Beispiel-Anfrage (curl)</label>
            <button @click="copy(curlExample, 'curl')" class="text-xs text-[#0088ba] hover:underline flex items-center gap-1">
              <Check v-if="copied === 'curl'" class="w-3 h-3 text-green-500" />
              <Copy v-else class="w-3 h-3" /> kopieren
            </button>
          </div>
          <pre class="px-3 py-3 bg-[#161e2a] text-gray-100 rounded-lg text-xs font-mono overflow-x-auto leading-relaxed"><code>{{ curlExample }}</code></pre>
        </div>

        <!-- JSON Felder-Tabelle -->
        <div>
          <label class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5 block">Felder im JSON-Body</label>
          <div class="border border-gray-100 rounded-xl overflow-hidden">
            <table class="w-full text-sm">
              <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                <tr>
                  <th class="text-left px-3 py-2 font-medium">Feld</th>
                  <th class="text-left px-3 py-2 font-medium">Typ</th>
                  <th class="text-left px-3 py-2 font-medium">Beschreibung</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="f in fields" :key="f.name">
                  <td class="px-3 py-2 font-mono text-xs text-gray-800">
                    {{ f.name }}
                    <span v-if="f.required" class="text-red-500">*</span>
                  </td>
                  <td class="px-3 py-2 text-xs text-gray-500">{{ f.type }}</td>
                  <td class="px-3 py-2 text-xs text-gray-600">{{ f.desc }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="text-xs text-gray-400 mt-2">* mindestens eines der beiden Felder (email oder mbNr) muss vorhanden sein</p>
        </div>

      </div>
    </div>

    <!-- KI-Analyse Compliance-Status -->
    <div class="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden mt-6">
      <div class="border-b border-gray-100 px-6 py-4 flex items-start gap-3">
        <Sparkles class="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
        <div>
          <h3 class="text-lg font-semibold text-gray-900">KI-Analyse (Compliance-Status)</h3>
          <p class="text-xs text-gray-500 mt-1">Dokument-Analyse durch Anthropic Claude. Default: deaktiviert. Aktivierung erfordert AVV + DSFA.</p>
        </div>
      </div>
      <div class="p-6 space-y-3">
        <div v-if="aiCfgLoading" class="text-xs text-gray-400">Lade Status…</div>
        <template v-else>
          <div class="flex items-center justify-between p-3 rounded-lg border" :class="aiCfg.keyVorhanden ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'">
            <div class="flex items-center gap-2 text-sm">
              <component :is="aiCfg.keyVorhanden ? CheckCircle2 : AlertTriangle" :class="['w-4 h-4', aiCfg.keyVorhanden ? 'text-green-600' : 'text-amber-600']" />
              <span class="font-medium">Anthropic API-Key</span>
            </div>
            <span :class="['text-xs px-2 py-0.5 rounded-full font-semibold', aiCfg.keyVorhanden ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700']">
              {{ aiCfg.keyVorhanden ? 'hinterlegt' : 'fehlt' }}
            </span>
          </div>
          <div class="flex items-center justify-between p-3 rounded-lg border" :class="aiCfg.globalAktiv ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'">
            <div class="flex items-center gap-2 text-sm">
              <component :is="aiCfg.globalAktiv ? CheckCircle2 : EyeOff" :class="['w-4 h-4', aiCfg.globalAktiv ? 'text-green-600' : 'text-gray-500']" />
              <span class="font-medium">Globaler Compliance-Schalter (AI_ANALYSE_AKTIV)</span>
            </div>
            <span :class="['text-xs px-2 py-0.5 rounded-full font-semibold', aiCfg.globalAktiv ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600']">
              {{ aiCfg.globalAktiv ? 'aktiv' : 'deaktiviert' }}
            </span>
          </div>
          <div class="p-3 rounded-lg bg-blue-50 border border-blue-100 text-xs text-blue-900">
            <strong>Aktivierung:</strong> erfolgt durch Setzen von <code class="bg-white px-1 rounded">AI_ANALYSE_AKTIV=true</code> in Azure-Function-App-Settings. Vor dem Umlegen: AVV mit Anthropic abgeschlossen, DSFA durchgeführt, Mandanten-Information ergänzt.
          </div>
          <div v-if="aiCfg.globalAktiv && aiCfg.keyVorhanden" class="p-3 rounded-lg bg-purple-50 border border-purple-100 text-xs text-purple-900">
            <strong>Hinweis:</strong> KI-Analyse ist verfügbar. Pro Akte muss zusätzlich der „KI-freigeben"-Toggle gesetzt werden (passiert beim ersten Klick auf „KI-Analyse" mit Bestätigungs-Dialog).
          </div>
        </template>
      </div>
    </div>

    <!-- Browser-Benachrichtigungen -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mt-5">
      <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
        <Bell class="w-4 h-4 text-[#0088ba]" /> Browser-Benachrichtigungen
      </h3>
      <PushToggle />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Webhook, Copy, Check, Eye, EyeOff, AlertTriangle, Info, Sparkles, CheckCircle2, Bell } from '@lucide/vue'
import PushToggle from '../PushToggle.vue'
import { aiConfig } from '../../api.js'
import { authFetch } from '../../api.js'

const data = ref({ url: '', token: '', headerName: 'X-Webhook-Token' })
const loading = ref(true)
const showToken = ref(false)
const copied = ref('')

const fields = [
  { name: 'email', type: 'string', required: true, desc: 'E-Mail des Kunden (wird zum Deduplizieren genutzt)' },
  { name: 'mbNr', type: 'string', required: true, desc: 'mb-Nummer (z.B. "mb-401") – legt Target an statt Kontakt' },
  { name: 'firma', type: 'string', required: false, desc: 'Firmenname' },
  { name: 'vorname', type: 'string', required: false, desc: 'Vorname (alternativ: name = "Vorname Nachname")' },
  { name: 'nachname', type: 'string', required: false, desc: 'Nachname' },
  { name: 'telefon', type: 'string', required: false, desc: 'Telefonnummer' },
  { name: 'website', type: 'string', required: false, desc: 'Webseite' },
  { name: 'plz', type: 'string', required: false, desc: 'Postleitzahl (für Karte)' },
  { name: 'ort', type: 'string', required: false, desc: 'Stadt' },
  { name: 'typ', type: 'enum', required: false, desc: 'PE | Systemhausgruppe | Strategisch | Sonstige' },
  { name: 'sucht', type: 'string', required: false, desc: 'Was sucht der Kontakt (zu kaufen)' },
  { name: 'bietet', type: 'string', required: false, desc: 'Was bietet der Kontakt' },
  { name: 'notizen', type: 'string', required: false, desc: 'Freitext-Notizen' },
  { name: 'kundennummer', type: 'string', required: false, desc: 'Deine interne Kundennummer' },
  { name: 'kundenstatus', type: 'string', required: false, desc: 'z.B. "Kunde", "Ex-Kunde"' },
  { name: 'branche', type: 'string', required: false, desc: 'Nur bei Target: Branche' },
  { name: 'mitarbeiter', type: 'string', required: false, desc: 'Nur bei Target: Mitarbeiterzahl' },
  { name: 'umsatz', type: 'string', required: false, desc: 'Nur bei Target: Jahresumsatz' },
]

const curlExample = computed(() => `curl -X POST ${data.value.url} \\
  -H "Content-Type: application/json" \\
  -H "X-Webhook-Token: ${showToken.value ? data.value.token : 'DEIN_TOKEN'}" \\
  -d '{
    "email": "max@beispielfirma.de",
    "firma": "Beispiel IT GmbH",
    "vorname": "Max",
    "nachname": "Mustermann",
    "telefon": "+49 89 12345678",
    "plz": "80331",
    "ort": "München",
    "typ": "Strategisch",
    "sucht": "IT-Systemhaus 5-15 MA Süddeutschland",
    "notizen": "Über Mike kennengelernt"
  }'`)

const aiCfg = ref({ globalAktiv: false, keyVorhanden: false })
const aiCfgLoading = ref(true)

onMounted(async () => {
  try {
    data.value = await authFetch('/settings/webhook')
  } finally { loading.value = false }
  try {
    aiCfg.value = await aiConfig()
  } catch {} finally { aiCfgLoading.value = false }
})

async function copy(text, key) {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = key
    setTimeout(() => { copied.value = '' }, 2000)
  } catch {}
}
</script>
