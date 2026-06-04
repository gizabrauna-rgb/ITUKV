<template>
  <div>
    <div>
      <h2 class="text-xl font-bold text-gray-900">Veröffentlichte Mandate</h2>
      <p class="text-sm text-gray-500 mt-1">Übersicht aller Landing-Pages. Schnell-Schalter zum Veröffentlichen oder Zurückziehen.</p>
    </div>

    <!-- Filter -->
    <div class="flex items-center gap-2 my-5">
      <button v-for="f in filterOptions" :key="f.key" @click="filter = f.key"
        :class="['px-3 py-1.5 rounded-full text-xs font-medium border', filter === f.key ? 'bg-[#0088ba] border-[#0088ba] text-white' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50']">
        {{ f.label }}<span v-if="counts[f.key] != null" class="ml-1.5 opacity-70">({{ counts[f.key] }})</span>
      </button>
    </div>

    <div v-if="loading" class="text-center text-gray-400 text-sm py-10">Lade…</div>
    <div v-else-if="!filtered.length" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">
      <Megaphone class="w-8 h-8 mx-auto mb-3 opacity-30" />
      <div v-if="!items.length">Noch keine Landing-Pages angelegt. Lege eine in einer Akte unter dem Tab „Marktansprache → Landing" an.</div>
      <div v-else>Keine Mandate in dieser Auswahl.</div>
    </div>

    <div v-else class="space-y-3">
      <div v-for="it in filtered" :key="it.targetId" class="bg-white rounded-xl border border-gray-100 p-5 hover:border-gray-200 transition-colors">
        <div class="flex items-start justify-between gap-4">
          <!-- Links: Status + Inhalt -->
          <div class="flex items-start gap-3 min-w-0 flex-1">
            <div :class="['w-2.5 h-2.5 rounded-full mt-2 flex-shrink-0', it.published ? 'bg-green-500' : 'bg-gray-300']"></div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 mb-1 flex-wrap">
                <span class="font-mono text-xs bg-blue-50 text-blue-800 px-2 py-0.5 rounded">{{ it.mbNr || '—' }}</span>
                <span :class="it.published ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'" class="text-[11px] font-medium px-2 py-0.5 rounded-full uppercase tracking-wide">
                  {{ it.published ? 'Online' : 'Offline' }}
                </span>
                <span class="text-xs text-gray-400">{{ it.verkaueferName }}</span>
              </div>
              <h3 class="font-semibold text-gray-900 truncate">{{ it.headline || '(noch keine Headline)' }}</h3>
              <p class="text-sm text-gray-500 mt-0.5 truncate">{{ it.subheadline || '—' }}</p>
              <div class="flex items-center gap-3 mt-2 text-xs text-gray-400">
                <span v-if="it.branche">{{ it.branche }}</span>
                <span v-if="it.region">· {{ it.region }}</span>
                <span v-if="it.umsatz">· {{ it.umsatz }}</span>
                <a v-if="it.published" :href="it.liveUrl" target="_blank" rel="noopener" class="text-[#0088ba] hover:underline inline-flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" /> {{ it.liveUrl.replace(/^https?:\/\//, '') }}
                </a>
              </div>
              <!-- Visit-Stats Unter-Zeile -->
              <div v-if="it.published && it.stats" class="flex items-center gap-3 mt-1.5 text-[11px]">
                <span class="bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">{{ it.stats.total }} Aufrufe</span>
                <span class="bg-green-50 text-green-700 px-2 py-0.5 rounded-full font-medium">{{ it.stats.uniqueVisitors }} unique</span>
                <span v-if="it.stats.lastVisit" class="text-gray-400">letzter: {{ fmtDate(it.stats.lastVisit) }}</span>
              </div>
            </div>
          </div>

          <!-- Rechts: Toggle + Aktionen -->
          <div class="flex items-center gap-2 flex-shrink-0">
            <button @click="togglePublish(it)" :disabled="it._busy"
              :class="['relative inline-flex items-center h-6 w-11 rounded-full transition-colors', it.published ? 'bg-green-500' : 'bg-gray-300', it._busy ? 'opacity-50' : '']"
              :title="it.published ? 'Klick: zurückziehen' : 'Klick: veröffentlichen'">
              <span :class="['inline-block w-5 h-5 bg-white rounded-full shadow transform transition-transform', it.published ? 'translate-x-5' : 'translate-x-0.5']"></span>
            </button>
            <button @click="$emit('open-akte', { targetId: it.targetId, tab: 'landing' })"
              class="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 rounded-lg text-xs hover:bg-gray-50">
              <Pencil class="w-3.5 h-3.5" /> Bearbeiten
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Megaphone, Pencil, ExternalLink } from '@lucide/vue'
import { getTargets, updateTarget } from '../../api.js'
import { authFetch } from '../../api.js'
import { toast } from '../../composables/useToast.js'

defineEmits(['open-akte'])

const LANDING_BASE = 'https://targets.itukv.de'

const loading = ref(true)
const items = ref([])
const filter = ref('online')

const filterOptions = [
  { key: 'online', label: 'Online' },
  { key: 'offline', label: 'Offline' },
  { key: 'alle', label: 'Alle' },
]

const counts = computed(() => ({
  online: items.value.filter(i => i.published).length,
  offline: items.value.filter(i => !i.published).length,
  alle: items.value.length,
}))

const filtered = computed(() => {
  if (filter.value === 'online') return items.value.filter(i => i.published)
  if (filter.value === 'offline') return items.value.filter(i => !i.published)
  return items.value
})

function parseLanding(t) {
  let landing = {}
  try { landing = JSON.parse(t.landingJson || '{}') } catch { landing = {} }
  return landing
}

function buildItem(t) {
  const landing = parseLanding(t)
  return {
    targetId: t.RowKey,
    mbNr: t.mbNr || '',
    verkaueferName: t.verkaueferName || '',
    branche: t.branche || '',
    region: t.region || '',
    umsatz: t.umsatz || '',
    headline: landing.headline || '',
    subheadline: landing.subheadline || '',
    published: landing.status === 'published',
    landing,
    liveUrl: `${LANDING_BASE}/${(t.mbNr || '').toLowerCase()}`,
    _busy: false,
  }
}

function fmtDate(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleDateString('de-DE') } catch { return '' }
}

onMounted(async () => {
  try {
    const targets = await getTargets()
    items.value = (targets || [])
      .map(buildItem)
      // Nur Targets mit Landing-Inhalt zeigen (verhindert Flut leerer Akten)
      .filter(it => it.headline || it.subheadline || it.published)
      .sort((a, b) => {
        if (a.published !== b.published) return a.published ? -1 : 1
        return (b.mbNr || '').localeCompare(a.mbNr || '')
      })
    // Visit-Stats parallel fuer alle online-Items laden (best-effort)
    const online = items.value.filter(it => it.published && it.mbNr)
    await Promise.all(online.map(async it => {
      try {
        it.stats = await authFetch('/landing-visit-stats', { method: 'POST', data: { mbNr: it.mbNr.toLowerCase() } })
      } catch {}
    }))
  } catch (e) {
    console.error(e)
    toast?.error?.('Mandate konnten nicht geladen werden.')
  } finally {
    loading.value = false
  }
})

async function togglePublish(it) {
  const willPublish = !it.published
  if (willPublish && (!it.headline || !it.subheadline)) {
    toast?.warn?.('Headline und Sub-Headline müssen gesetzt sein, bevor du veröffentlichst. Bitte „Bearbeiten" klicken.')
    return
  }
  if (!willPublish && !confirm(`Landing-Page „${it.headline}" zurückziehen? Sie ist dann nicht mehr öffentlich erreichbar.`)) return
  it._busy = true
  try {
    const newLanding = { ...it.landing, status: willPublish ? 'published' : 'draft' }
    await updateTarget(it.targetId, { landingJson: JSON.stringify(newLanding) })
    it.landing = newLanding
    it.published = willPublish
    toast?.success?.(willPublish ? 'Landing-Page ist jetzt online.' : 'Landing-Page zurückgezogen.')
  } catch (e) {
    console.error(e)
    toast?.error?.('Speichern fehlgeschlagen.')
  } finally {
    it._busy = false
  }
}
</script>
