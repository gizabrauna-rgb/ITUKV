<script setup>
import { ref, onMounted, computed } from 'vue'
import { ClipboardList, RefreshCw, ChevronDown, Mail, Globe, ExternalLink } from '@lucide/vue'
import { getChecklisten } from '../../api.js'

const loading = ref(true)
const items = ref([])
const fragen = ref([])
const offen = ref(null)  // aufgeklappte Zeile (id)
const err = ref('')

const CHECKLISTE_URL = 'https://checkliste.itukv.de'

const ZAHL_ZEILEN = [
  { key: 'umsatz', label: 'Umsatz (TEUR)' },
  { key: 'ebit', label: 'EBIT (TEUR)' },
  { key: 'bereinigtesEbit', label: 'Bereinigtes EBIT (TEUR)' },
  { key: 'gfGehalt', label: 'davon: GF-Gehalt (TEUR)' },
  { key: 'mitarbeiter', label: 'Mitarbeiter' },
  { key: 'vertragsumsatz', label: 'Umsatz aus Verträgen (TEUR)' },
]

async function load() {
  loading.value = true
  err.value = ''
  try {
    const res = await getChecklisten()
    items.value = res.items || []
    fragen.value = res.fragen || []
  } catch (e) {
    err.value = 'Konnte Checklisten nicht laden.'
    console.error(e)
  } finally {
    loading.value = false
  }
}
onMounted(load)

const anzahl = computed(() => items.value.length)

function euro(n) {
  if (!n || n <= 0) return '–'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n)
}
function datum(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) } catch { return iso }
}
function faktorFarbe(f) {
  if (f >= 6) return 'bg-green-100 text-green-700'
  if (f >= 4) return 'bg-amber-100 text-amber-700'
  return 'bg-red-100 text-red-700'
}
function toggle(id) { offen.value = offen.value === id ? null : id }

async function copyLink() {
  try { await navigator.clipboard.writeText(CHECKLISTE_URL); linkKopiert.value = true; setTimeout(() => linkKopiert.value = false, 2000) } catch {}
}
const linkKopiert = ref(false)
</script>

<template>
  <div>
    <!-- Kopf -->
    <div class="flex items-start justify-between gap-4 mb-6 flex-wrap">
      <div>
        <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
          <ClipboardList class="w-5 h-5 text-[#0088ba]" /> ITUKV-Checkliste
        </h2>
        <p class="text-sm text-gray-500 mt-1">Digitale „Wie verkaufsbereit ist Dein IT-Unternehmen?"-Auswertungen ({{ anzahl }}).</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="copyLink" class="flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
          <Globe class="w-4 h-4 text-gray-400" /> {{ linkKopiert ? 'Link kopiert!' : 'Link kopieren' }}
        </button>
        <a :href="CHECKLISTE_URL" target="_blank" rel="noopener" class="flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
          Öffnen <ExternalLink class="w-3.5 h-3.5 text-gray-400" />
        </a>
        <button @click="load" class="flex items-center gap-1.5 px-3 py-2 text-sm bg-[#0088ba] text-white rounded-lg hover:bg-[#00a0d8]">
          <RefreshCw class="w-4 h-4" :class="loading ? 'animate-spin' : ''" /> Aktualisieren
        </button>
      </div>
    </div>

    <p v-if="err" class="text-sm text-red-600 mb-4">{{ err }}</p>
    <div v-if="loading" class="text-center text-gray-400 py-10">Lade Auswertungen…</div>

    <div v-else-if="!anzahl" class="bg-white border border-gray-100 rounded-2xl p-10 text-center">
      <ClipboardList class="w-10 h-10 text-gray-300 mx-auto mb-3" />
      <p class="font-semibold text-gray-700">Noch keine Checklisten ausgefüllt.</p>
      <p class="text-sm text-gray-500 mt-1">Teile den Link <a :href="CHECKLISTE_URL" target="_blank" class="text-[#0088ba] underline">checkliste.itukv.de</a>, um Leads zu sammeln.</p>
    </div>

    <div v-else class="space-y-2">
      <div v-for="c in items" :key="c.id" class="bg-white border border-gray-100 rounded-xl overflow-hidden">
        <!-- Zeile -->
        <button @click="toggle(c.id)" class="w-full flex items-center gap-3 p-4 text-left hover:bg-gray-50">
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-gray-900 truncate">{{ c.firma || c.enrichFirmenname || 'Unbekannte Firma' }}</p>
            <p class="text-xs text-gray-500 truncate">{{ c.name }}<span v-if="c.email"> · {{ c.email }}</span></p>
          </div>
          <div class="hidden sm:block text-right">
            <p class="text-sm font-semibold text-gray-900">{{ euro(c.wertMidEur) }}</p>
            <p class="text-[11px] text-gray-400">grober Wert</p>
          </div>
          <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="faktorFarbe(c.faktor)">Faktor {{ c.faktor }}</span>
          <span class="text-xs text-gray-400 w-16 text-right">{{ c.jaCount }}/{{ c.fragenGesamt }} JA</span>
          <span class="text-xs text-gray-400 hidden md:block w-20 text-right">{{ datum(c.createdAt) }}</span>
          <ChevronDown class="w-4 h-4 text-gray-400 transition-transform" :class="offen === c.id ? 'rotate-180' : ''" />
        </button>

        <!-- Detail -->
        <div v-if="offen === c.id" class="border-t border-gray-100 p-5 bg-gray-50/60 space-y-5">
          <!-- Ansprache + Insight -->
          <div class="grid md:grid-cols-2 gap-4">
            <div class="bg-white rounded-xl border border-gray-100 p-4">
              <p class="text-xs font-semibold text-gray-400 uppercase mb-1">Individuelle Einschätzung</p>
              <p class="text-sm text-gray-700">{{ c.ansprache || '–' }}</p>
              <p v-if="c.geschaeftsmodell" class="text-xs text-gray-500 mt-2">Geschäftsmodell: {{ c.geschaeftsmodell }}</p>
              <p v-if="c.schwerpunkte" class="text-xs text-gray-500">Schwerpunkte: {{ c.schwerpunkte }}</p>
            </div>
            <div class="bg-amber-50 rounded-xl border border-amber-200 p-4">
              <p class="text-xs font-semibold text-amber-700 uppercase mb-1">Markt-Einblick</p>
              <p class="text-sm text-amber-900">{{ c.insight || '–' }}</p>
            </div>
          </div>

          <!-- Kontakt + Zahlen -->
          <div class="grid md:grid-cols-2 gap-4">
            <div class="bg-white rounded-xl border border-gray-100 p-4 text-sm space-y-1">
              <p class="text-xs font-semibold text-gray-400 uppercase mb-2">Kontakt</p>
              <p v-if="c.email"><a :href="'mailto:' + c.email" class="text-[#0088ba] inline-flex items-center gap-1"><Mail class="w-3.5 h-3.5" /> {{ c.email }}</a></p>
              <p v-if="c.telefon" class="text-gray-600">{{ c.telefon }}</p>
              <p v-if="c.website"><a :href="c.website" target="_blank" rel="noopener" class="text-[#0088ba] inline-flex items-center gap-1"><Globe class="w-3.5 h-3.5" /> {{ c.website }}</a></p>
              <p v-if="c.plz || c.ort" class="text-gray-600">{{ c.plz }} {{ c.ort }}</p>
              <p v-if="c.mitarbeiter" class="text-gray-600">{{ c.mitarbeiter }} Mitarbeiter</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-100 p-4 text-sm space-y-3">
              <div>
                <p class="text-xs font-semibold text-gray-400 uppercase mb-2">Betriebswirtschaftliche Zahlen</p>
                <div v-if="c.zahlenJahre?.length" class="overflow-x-auto">
                  <table class="w-full text-xs border-collapse">
                    <thead>
                      <tr class="text-gray-400">
                        <th class="text-left font-medium pb-1 pr-2"></th>
                        <th v-for="j in c.zahlenJahre" :key="j.jahr" class="text-right font-medium pb-1 px-1.5 whitespace-nowrap">
                          {{ j.jahr }}<span v-if="j.geplant"> gpl.</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="z in ZAHL_ZEILEN" :key="z.key" class="border-t border-gray-50">
                        <td class="py-1 pr-2 text-gray-500 leading-tight">{{ z.label }}</td>
                        <td v-for="j in c.zahlenJahre" :key="j.jahr" class="py-1 px-1.5 text-right text-gray-800 tabular-nums">{{ j[z.key] || '–' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="text-gray-500 space-y-0.5">
                  <p><span class="text-gray-400">Umsatz:</span> {{ c.zahlUmsatz || '–' }} TEUR · <span class="text-gray-400">EBIT:</span> {{ c.zahlEbit || '–' }} TEUR</p>
                  <p><span class="text-gray-400">Bereinigtes EBIT:</span> {{ c.zahlBereinigtesEbit || '–' }} TEUR · <span class="text-gray-400">Vertragsumsatz:</span> {{ c.zahlVertragsumsatz || '–' }} TEUR</p>
                </div>
                <p class="text-[11px] text-gray-400 mt-1">EBIT-Trend: {{ c.zahlEbitTrend || '–' }}</p>
              </div>
              <div v-if="c.motivZeitpunkt || c.motivWunschpreis || c.motivMotivation" class="border-t border-gray-100 pt-2 space-y-0.5">
                <p class="text-xs font-semibold text-gray-400 uppercase mb-1">Verkaufsziele</p>
                <p v-if="c.motivZeitpunkt" class="text-gray-600"><span class="text-gray-400">Verkauf geplant:</span> {{ c.motivZeitpunkt }}</p>
                <p v-if="c.motivWunschpreis" class="text-gray-600"><span class="text-gray-400">Wunschpreis:</span> {{ c.motivWunschpreis }}</p>
                <p v-if="c.motivMotivation" class="text-gray-600"><span class="text-gray-400">Motivation:</span> {{ c.motivMotivation }}</p>
              </div>
            </div>
          </div>

          <!-- Antworten -->
          <div class="bg-white rounded-xl border border-gray-100 p-4">
            <p class="text-xs font-semibold text-gray-400 uppercase mb-3">Antworten ({{ c.jaCount }}/{{ c.fragenGesamt }} JA)</p>
            <ul class="space-y-1.5">
              <li v-for="f in fragen" :key="f.key" class="flex items-start gap-2 text-sm">
                <span class="mt-0.5 w-4 h-4 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold"
                  :class="c.antworten[f.key] === true ? 'bg-green-100 text-green-700' : (c.antworten[f.key] === false ? 'bg-gray-200 text-gray-500' : 'bg-gray-100 text-gray-300')">
                  {{ c.antworten[f.key] === true ? 'J' : (c.antworten[f.key] === false ? 'N' : '?') }}
                </span>
                <span class="text-gray-600">{{ f.text }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
