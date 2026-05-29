<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 class="w-6 h-6 text-[#0088ba]" /> Controlling & Auswertung
        </h2>
        <p class="text-sm text-gray-500 mt-1">Jahresübersicht aller M&A-Prozesse: Erfolgsquote, Deal-Dauer, Pipeline</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="downloadBeiratsbericht" :disabled="pdfLoading"
          class="flex items-center gap-1.5 px-3 py-2 border border-[#0088ba] text-[#0088ba] rounded-xl text-sm font-medium hover:bg-[#0088ba]/5 disabled:opacity-50">
          <FileText class="w-4 h-4" /> {{ pdfLoading ? 'Erzeuge…' : 'Beirats-Bericht (PDF)' }}
        </button>
        <select v-model.number="year" @change="load" class="border border-gray-200 rounded-xl px-4 py-2 text-sm">
          <option :value="0">Alle Jahre</option>
          <option v-for="y in stats.yearsAvailable" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="text-center text-gray-400 py-10">Lade Daten…</div>

    <div v-else>
      <!-- Top-KPIs -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-gray-400 font-medium uppercase tracking-wide">Mandate gesamt</span>
            <Briefcase class="w-4 h-4 text-[#0088ba]" />
          </div>
          <div class="text-3xl font-bold text-gray-900">{{ stats.total }}</div>
          <div class="text-xs text-gray-500 mt-1">{{ stats.verkaufAnzahl }} Verkauf · {{ stats.kaufAnzahl }} Kauf</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-gray-400 font-medium uppercase tracking-wide">Abschlüsse</span>
            <CheckCircle2 class="w-4 h-4 text-green-600" />
          </div>
          <div class="text-3xl font-bold text-green-700">{{ stats.closed }}</div>
          <div class="text-xs text-gray-500 mt-1">Erfolgsquote {{ stats.successRate }}%</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-gray-400 font-medium uppercase tracking-wide">Ø Deal-Dauer</span>
            <Clock class="w-4 h-4 text-amber-600" />
          </div>
          <div class="text-3xl font-bold text-gray-900">{{ stats.avgDurationDays }}<span class="text-base font-normal text-gray-500"> Tg</span></div>
          <div class="text-xs text-gray-500 mt-1">Mandat-Start bis Closing</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-gray-400 font-medium uppercase tracking-wide">PR-Quote</span>
            <Megaphone class="w-4 h-4 text-purple-600" />
          </div>
          <div class="text-3xl font-bold text-gray-900">{{ stats.prQuote }}%</div>
          <div class="text-xs text-gray-500 mt-1">{{ stats.prCount }}/{{ stats.closed }} mit Pressemitteilung</div>
        </div>
      </div>

      <!-- Pipeline-Wert + Provision (NEU für Beirats-Bericht) -->
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-gradient-to-br from-[#0088ba] to-[#00a0d8] text-white rounded-xl p-5">
          <div class="text-xs uppercase tracking-wide opacity-80 mb-1">Pipeline-Wert (offen)</div>
          <div class="text-3xl font-bold">{{ formatTeur(stats.pipelineWertTeur) }}</div>
          <div class="text-xs opacity-90 mt-1">Summe Umsätze aktiver Mandate</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="text-xs uppercase tracking-wide text-gray-400 font-medium mb-1">Provisions-Forecast</div>
          <div class="text-3xl font-bold text-[#0088ba]">{{ formatTeur(stats.provisionForecastTeur) }}</div>
          <div class="text-xs text-gray-500 mt-1">bei {{ stats.provisionQuotePct || 4 }}% Erfolgshonorar</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="text-xs uppercase tracking-wide text-gray-400 font-medium mb-1">Realisierte Provision</div>
          <div class="text-3xl font-bold text-green-600">{{ formatTeur(stats.provisionRealisiertTeur) }}</div>
          <div class="text-xs text-gray-500 mt-1">{{ stats.closed || 0 }} abgeschlossene Mandate</div>
        </div>
      </div>

      <!-- Top-Mandate -->
      <div v-if="stats.topMandate?.length" class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
        <h3 class="font-semibold text-gray-800 text-sm mb-3">Top-Mandate nach Umsatz</h3>
        <table class="w-full text-sm">
          <thead class="text-xs text-gray-400 uppercase tracking-wide">
            <tr><th class="text-left pb-2">mb-Nr</th><th class="text-left pb-2">Verkäufer</th><th class="text-right pb-2">Umsatz</th><th class="text-left pb-2">Phase</th><th class="text-left pb-2">Status</th></tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="m in stats.topMandate" :key="m.mbNr || m.verkaueferName" class="hover:bg-gray-50">
              <td class="py-2 font-mono text-xs">{{ m.mbNr || '—' }}</td>
              <td class="py-2">{{ m.verkaueferName || '—' }}</td>
              <td class="py-2 text-right font-semibold">{{ m.umsatz || formatTeur(m.umsatzTeur) }}</td>
              <td class="py-2 text-gray-600">Phase {{ m.phase || '-' }}</td>
              <td class="py-2 text-gray-600">{{ m.status || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pipeline-Funnel (grober Ueberblick) -->
      <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
        <h3 class="font-semibold text-gray-800 text-sm mb-4 flex items-center gap-2">
          <GitBranch class="w-4 h-4 text-[#0088ba]" /> Pipeline – wo stehen die offenen Mandate?
        </h3>
        <div class="space-y-2">
          <div v-for="(count, key) in stats.pipelineFunnel" :key="key" class="flex items-center gap-3">
            <span class="text-xs text-gray-500 w-32 flex-shrink-0">Phasen {{ key }}</span>
            <div class="flex-1 bg-gray-100 rounded-full h-7 overflow-hidden relative">
              <div class="bg-[#0088ba] h-full rounded-full transition-all flex items-center justify-end pr-2"
                :style="`width: ${maxBucket ? (count / maxBucket) * 100 : 0}%`">
                <span v-if="count > 0" class="text-xs font-bold text-white">{{ count }}</span>
              </div>
            </div>
            <span class="text-sm font-medium text-gray-700 w-8 text-right">{{ count }}</span>
          </div>
        </div>
        <p class="text-xs text-gray-400 mt-3">{{ phaseLegende }}</p>
      </div>

      <!-- Phasen-Verteilung Detail (NEU) -->
      <div v-if="stats.pipelineByPhaseVerkauf?.length || stats.pipelineByPhaseKauf?.length" class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <!-- Verkäufer -->
        <div v-if="stats.pipelineByPhaseVerkauf?.length" class="bg-white rounded-xl border border-gray-100 p-5">
          <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
            <Briefcase class="w-4 h-4 text-orange-600" /> Verkäufer-Mandate pro Phase
          </h3>
          <div class="space-y-2">
            <div v-for="p in stats.pipelineByPhaseVerkauf" :key="'v'+p.phase" class="flex items-start gap-2 text-xs">
              <span class="w-6 flex-shrink-0 font-mono text-gray-400 mt-1">P{{ p.phase }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-gray-700 truncate">{{ cleanTitel(p.titel) }}</span>
                  <span class="font-semibold text-orange-700">{{ p.count }}</span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-1.5 mt-1">
                  <div class="bg-orange-500 h-1.5 rounded-full" :style="`width: ${maxPhaseVerkauf ? (p.count/maxPhaseVerkauf)*100 : 0}%`"></div>
                </div>
                <div class="flex flex-wrap gap-1 mt-1">
                  <span v-for="m in p.mandate" :key="m.targetId" class="bg-orange-50 text-orange-700 text-[10px] font-mono px-1.5 py-0.5 rounded">
                    {{ m.mbNr || '—' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- Käufer -->
        <div v-if="stats.pipelineByPhaseKauf?.length" class="bg-white rounded-xl border border-gray-100 p-5">
          <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
            <Users class="w-4 h-4 text-green-600" /> Käufer-Mandate pro Phase
          </h3>
          <div class="space-y-2">
            <div v-for="p in stats.pipelineByPhaseKauf" :key="'k'+p.phase" class="flex items-start gap-2 text-xs">
              <span class="w-6 flex-shrink-0 font-mono text-gray-400 mt-1">P{{ p.phase }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-gray-700 truncate">{{ cleanTitel(p.titel) }}</span>
                  <span class="font-semibold text-green-700">{{ p.count }}</span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-1.5 mt-1">
                  <div class="bg-green-500 h-1.5 rounded-full" :style="`width: ${maxPhaseKauf ? (p.count/maxPhaseKauf)*100 : 0}%`"></div>
                </div>
                <div class="flex flex-wrap gap-1 mt-1">
                  <span v-for="m in p.mandate" :key="m.targetId" class="bg-green-50 text-green-700 text-[10px] font-mono px-1.5 py-0.5 rounded">
                    {{ m.mbNr || '—' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Deal-Dauer pro Projekttyp -->
      <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
        <h3 class="font-semibold text-gray-800 text-sm mb-4 flex items-center gap-2">
          <Clock class="w-4 h-4 text-[#0088ba]" /> Ø Deal-Dauer pro Projekttyp
        </h3>
        <div v-if="!Object.keys(stats.dauerProTyp).length" class="text-sm text-gray-400 py-4 text-center">
          Noch keine abgeschlossenen Deals zum Auswerten.
        </div>
        <div v-else class="space-y-2">
          <div v-for="(tage, typ) in stats.dauerProTyp" :key="typ" class="flex items-center gap-3">
            <span class="text-sm text-gray-700 w-44 flex-shrink-0">{{ typ }}</span>
            <div class="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
              <div class="bg-amber-400 h-full" :style="`width: ${maxDauer ? (tage / maxDauer) * 100 : 0}%`"></div>
            </div>
            <span class="text-sm font-bold text-gray-800 w-20 text-right">{{ tage }} Tage</span>
          </div>
        </div>
      </div>

      <!-- Monatlicher Verlauf -->
      <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6" v-if="stats.monthly?.length">
        <h3 class="font-semibold text-gray-800 text-sm mb-4 flex items-center gap-2">
          <TrendingUp class="w-4 h-4 text-[#0088ba]" /> Monatlicher Verlauf
        </h3>
        <div class="flex items-end gap-2 h-32">
          <div v-for="m in stats.monthly" :key="m.month" class="flex-1 flex flex-col items-center gap-1">
            <div class="w-full bg-gray-100 rounded-t flex flex-col-reverse" :style="`height: ${maxMonth ? Math.max((m.created + m.closed) / maxMonth, 0.05) * 100 : 0}%`">
              <div class="w-full bg-[#0088ba]" :style="`height: ${(m.closed / Math.max(m.created+m.closed, 1)) * 100}%`" :title="`${m.closed} Abschluss`"></div>
              <div class="w-full bg-[#0088ba]/40" :style="`height: ${(m.created / Math.max(m.created+m.closed, 1)) * 100}%`" :title="`${m.created} neu`"></div>
            </div>
            <span class="text-[10px] text-gray-500 -rotate-45 origin-top-left whitespace-nowrap mt-2">{{ m.month }}</span>
          </div>
        </div>
        <div class="flex gap-3 text-xs text-gray-500 mt-4">
          <span class="flex items-center gap-1"><span class="w-3 h-3 bg-[#0088ba] rounded"></span> Abschluss</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 bg-[#0088ba]/40 rounded"></span> Neue Mandate</span>
        </div>
      </div>

      <!-- Lessons Learned Aggregat -->
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <h3 class="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
          <BookOpen class="w-4 h-4 text-[#0088ba]" /> Lessons Learned aus abgeschlossenen Deals
        </h3>
        <div v-if="!lessons.length" class="text-sm text-gray-400 py-6 text-center">
          Noch keine Lessons-Learned-Einträge. Fülle in jedem Mandant unter „Erfolgsmeldung" den entsprechenden Bereich.
        </div>
        <div v-else class="space-y-3">
          <div v-for="l in lessons" :key="l.targetId" class="border border-gray-100 rounded-xl p-4">
            <div class="flex items-center gap-2 mb-2">
              <span :class="['font-mono text-xs px-2 py-0.5 rounded',
                /kauf|investor/i.test(l.projekttyp || '') ? 'bg-green-50 text-green-700' : 'bg-orange-50 text-orange-700']">{{ l.mbNr }}</span>
              <span class="font-medium text-gray-800">{{ l.verkaueferName }}</span>
              <span class="text-xs text-gray-500">{{ l.projekttyp }}</span>
            </div>
            <div v-if="l.keyLearning" class="text-sm font-medium text-gray-800 mb-2">💡 {{ l.keyLearning }}</div>
            <div class="grid grid-cols-2 gap-3 text-xs">
              <div v-if="l.pro"><span class="text-green-700 font-semibold">Pro:</span> {{ l.pro }}</div>
              <div v-if="l.contra"><span class="text-red-700 font-semibold">Contra:</span> {{ l.contra }}</div>
            </div>
            <div v-if="l.anders" class="text-xs mt-2"><span class="text-purple-700 font-semibold">Anders machen:</span> {{ l.anders }}</div>
            <div v-if="l.tags?.length" class="flex flex-wrap gap-1 mt-2">
              <span v-for="t in l.tags" :key="t" class="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { BarChart3, Briefcase, CheckCircle2, Clock, Megaphone, GitBranch, TrendingUp, BookOpen, FileText, Users } from '@lucide/vue'
import { authFetch, controllingPdf } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const year = ref(new Date().getFullYear())
const loading = ref(true)
const stats = ref({ total: 0, open: 0, closed: 0, successRate: 0, avgDurationDays: 0, pipelineFunnel: {}, dauerProTyp: {}, monthly: [], yearsAvailable: [], prQuote: 0, prCount: 0, verkaufAnzahl: 0, kaufAnzahl: 0 })
const lessons = ref([])

const maxBucket = computed(() => Math.max(...Object.values(stats.value.pipelineFunnel || {}), 1))
const maxDauer = computed(() => Math.max(...Object.values(stats.value.dauerProTyp || {}), 1))
const maxMonth = computed(() => Math.max(...(stats.value.monthly || []).map(m => m.created + m.closed), 1))
const maxPhaseVerkauf = computed(() => Math.max(...(stats.value.pipelineByPhaseVerkauf || []).map(p => p.count), 1))
const maxPhaseKauf = computed(() => Math.max(...(stats.value.pipelineByPhaseKauf || []).map(p => p.count), 1))

function cleanTitel(t) {
  return (t || '').replace(/^\d+\.\s*/, '')
}

const phaseLegende = computed(() => stats.value.kaufAnzahl > 0
  ? 'Verkauf-Mandate: 1-3 Start/Vorbereitung · 4-6 Marktansprache · 7-9 Verhandlung · 10-12 LOI/DD · 13-15 Closing · Kauf-Mandate: kürzerer 10-Phasen-Prozess (im selben Schema gruppiert)'
  : 'Phase 1-3: UVE/Vorbereitung · 4-6: Marktansprache · 7-9: Verhandlung · 10-12: LOI/Due Diligence · 13-15: Closing & Erfolgsmeldung')

async function load() {
  loading.value = true
  try {
    const url = year.value ? `/controlling-stats?year=${year.value}` : '/controlling-stats'
    stats.value = await authFetch(url)
    const l = await authFetch('/lessons-learned')
    lessons.value = l.items || []
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const pdfLoading = ref(false)
async function downloadBeiratsbericht() {
  pdfLoading.value = true
  try {
    const blob = await controllingPdf(year.value || '')
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Beiratsbericht_${year.value || 'gesamt'}.pdf`
    document.body.appendChild(a); a.click(); a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    toast.success('Beirats-Bericht erstellt')
  } catch (e) {
    toast.error('PDF-Erstellung fehlgeschlagen: ' + (e?.message || ''))
  } finally {
    pdfLoading.value = false
  }
}

function formatTeur(n) {
  if (!n) return '0 T€'
  if (n >= 1000) return `${(n / 1000).toFixed(1).replace('.', ',')} Mio €`
  return `${Math.round(n).toLocaleString('de-DE')} T€`
}

onMounted(load)
</script>
