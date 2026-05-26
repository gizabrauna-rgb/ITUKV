<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h2 class="text-xl font-bold text-gray-900">E-Mail-Vorlagen</h2>
        <p class="text-xs text-gray-500 mt-1">Platzhalter: <code v-for="(ph, i) in platzhalter" :key="ph" class="bg-gray-100 px-1 rounded mr-1">{{ ph }}</code></p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="reseed" :disabled="reseeding" class="flex items-center gap-2 px-3 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm hover:bg-gray-50 disabled:opacity-50" title="Jenny-Vorlagen einspielen, die noch fehlen (vorhandene werden nicht überschrieben)">
          <Download class="w-4 h-4" /> {{ reseeding ? 'Importiere…' : 'Jenny-Vorlagen importieren' }}
        </button>
        <button @click="newVorlage" class="flex items-center gap-2 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8]">
          <Plus class="w-4 h-4" /> Neue Vorlage
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Liste -->
      <div class="lg:col-span-1 bg-white rounded-xl border border-gray-100 p-2 max-h-[70vh] overflow-y-auto">
        <div v-if="loading" class="p-4 text-sm text-gray-400 text-center">Lade…</div>
        <div v-else-if="!vorlagen.length" class="p-4 text-sm text-gray-400 text-center">Noch keine Vorlagen.</div>
        <ul v-else class="space-y-1">
          <li v-for="v in vorlagen" :key="v.RowKey">
            <button @click="select(v)"
              :class="['w-full text-left p-3 rounded-lg transition-colors',
                       selected?.RowKey === v.RowKey ? 'bg-[#0088ba]/10 border border-[#0088ba]/30' : 'hover:bg-gray-50 border border-transparent']">
              <div class="font-medium text-sm text-gray-800 truncate">{{ v.name }}</div>
              <div class="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
                <span class="px-1.5 py-0.5 rounded-full bg-gray-100">{{ v.kategorie }}</span>
                <span class="truncate">{{ v.betreff }}</span>
              </div>
            </button>
          </li>
        </ul>
      </div>

      <!-- Editor -->
      <div class="lg:col-span-2 bg-white rounded-xl border border-gray-100 p-5">
        <div v-if="!selected" class="text-center py-16 text-gray-400 text-sm">
          <FileText class="w-10 h-10 mx-auto mb-2 text-gray-300" />
          Vorlage auswählen oder neu anlegen.
        </div>
        <div v-else class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Name *</label>
              <input v-model="form.name" placeholder="z.B. Erstkontakt Target" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Kategorie</label>
              <input v-model="form.kategorie" list="kat-list" placeholder="Akquise / Mandat / Abschluss" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
              <datalist id="kat-list">
                <option value="Akquise" />
                <option value="Mandat" />
                <option value="Abschluss" />
                <option value="Allgemein" />
              </datalist>
            </div>
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Betreff</label>
            <input v-model="form.betreff" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Text</label>
            <textarea v-model="form.body" rows="14" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 font-mono resize-y"></textarea>
          </div>
          <div class="flex items-center justify-between">
            <button v-if="selected.RowKey && !selected.RowKey.startsWith('new-')" @click="remove"
              class="flex items-center gap-1.5 text-sm text-red-600 hover:text-red-700">
              <Trash2 class="w-4 h-4" /> Löschen
            </button>
            <div v-else></div>
            <button @click="save" :disabled="!form.name || saving"
              class="px-5 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium hover:bg-[#00a0d8] disabled:opacity-50">
              {{ saving ? 'Speichern…' : 'Speichern' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, FileText, Trash2, Download } from '@lucide/vue'
import { getMailvorlagen, saveMailvorlage, deleteMailvorlage, reseedMailvorlagen } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const platzhalter = ['{{firma}}', '{{name}}', '{{mbNr}}', '{{absender}}', '{{datum}}', '{{anfrageLink}}']
const vorlagen = ref([])
const reseeding = ref(false)

async function reseed() {
  reseeding.value = true
  try {
    const r = await reseedMailvorlagen()
    if (r.added > 0) toast.success(`${r.added} neue Vorlage(n) importiert`)
    else toast.info('Alle Jenny-Vorlagen sind bereits vorhanden')
    await load()
  } catch (e) {
    toast.error('Import fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally { reseeding.value = false }
}
const selected = ref(null)
const form = ref({ name: '', kategorie: 'Allgemein', betreff: '', body: '' })
const loading = ref(true)
const saving = ref(false)

async function load() {
  loading.value = true
  try { vorlagen.value = await getMailvorlagen() }
  catch (e) { toast.error('Laden fehlgeschlagen') }
  finally { loading.value = false }
}

function select(v) {
  selected.value = v
  form.value = { name: v.name, kategorie: v.kategorie, betreff: v.betreff, body: v.body, RowKey: v.RowKey }
}

function newVorlage() {
  const placeholder = { RowKey: 'new-' + Date.now(), name: '', kategorie: 'Allgemein', betreff: '', body: '' }
  selected.value = placeholder
  form.value = { ...placeholder }
}

async function save() {
  saving.value = true
  try {
    const payload = { ...form.value }
    if (payload.RowKey && payload.RowKey.startsWith('new-')) delete payload.RowKey
    const saved = await saveMailvorlage(payload)
    toast.success('Vorlage gespeichert')
    await load()
    const found = vorlagen.value.find(v => v.RowKey === saved.RowKey)
    if (found) select(found)
  } catch (e) {
    toast.error('Speichern fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally { saving.value = false }
}

async function remove() {
  if (!confirm(`Vorlage „${selected.value.name}" wirklich löschen?`)) return
  try {
    await deleteMailvorlage(selected.value.RowKey)
    toast.success('Vorlage gelöscht')
    selected.value = null
    await load()
  } catch (e) {
    toast.error('Löschen fehlgeschlagen')
  }
}

onMounted(load)
</script>
