<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Links für den Kunden</h3>
        <p class="text-xs text-gray-500">Hier hinterlegst du Links die der Kunde im Portal sehen kann (Kajabi-Videos, Live-Calls, externe Dokumente).</p>
      </div>
      <button @click="openNew" class="flex items-center gap-2 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf]">
        <Plus class="w-4 h-4" /> Link hinzufügen
      </button>
    </div>

    <div v-if="!links.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400 text-sm">
      <LinkIcon class="w-10 h-10 mx-auto mb-2 text-gray-200" />
      Noch keine Links für diesen Mandanten hinterlegt.
    </div>

    <!-- Gruppiert nach Kategorie -->
    <div v-else class="space-y-4">
      <div v-for="kat in kategorien" :key="kat.value">
        <div v-if="byCategory(kat.value).length">
          <div class="flex items-center gap-2 mb-2">
            <component :is="kat.icon" class="w-4 h-4 text-[#097e92]" />
            <span class="font-semibold text-sm text-gray-800">{{ kat.label }}</span>
            <span class="text-xs text-gray-400">({{ byCategory(kat.value).length }})</span>
          </div>
          <div class="space-y-2">
            <div v-for="l in byCategory(kat.value)" :key="l.id" class="bg-white rounded-xl border border-gray-100 p-4 flex items-start gap-3">
              <div class="w-10 h-10 bg-[#097e92]/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <component :is="kat.icon" class="w-5 h-5 text-[#097e92]" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <a :href="l.url" target="_blank" rel="noopener" class="font-medium text-gray-900 hover:text-[#097e92] truncate">{{ l.titel }}</a>
                  <ExternalLink class="w-3 h-3 text-gray-400" />
                </div>
                <div v-if="l.beschreibung" class="text-sm text-gray-600 mt-1">{{ l.beschreibung }}</div>
                <div class="text-xs text-gray-400 mt-1 truncate">{{ l.url }}</div>
              </div>
              <div class="flex gap-1">
                <button @click="openEdit(l)" class="text-gray-300 hover:text-gray-600 p-1.5"><Pencil class="w-3.5 h-3.5" /></button>
                <button @click="deleteLink(l)" class="text-gray-300 hover:text-red-500 p-1.5"><Trash2 class="w-3.5 h-3.5" /></button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-900">{{ editing ? 'Link bearbeiten' : 'Neuer Link' }}</h3>
          <button @click="closeModal"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="space-y-3">
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Kategorie *</label>
            <select v-model="form.kategorie" class="input">
              <option v-for="k in kategorien" :key="k.value" :value="k.value">{{ k.label }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Titel *</label>
            <input v-model="form.titel" placeholder="z.B. Modul MB050 - Kapitel 3" class="input" />
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">URL *</label>
            <input v-model="form.url" type="url" placeholder="https://kajabi.com/…" class="input" />
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Beschreibung</label>
            <textarea v-model="form.beschreibung" rows="2" placeholder="Was ist das? Wann ansehen?" class="input resize-none"></textarea>
          </div>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="closeModal" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
          <button @click="saveLink" :disabled="!form.titel || !form.url" class="flex-1 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium disabled:opacity-50">Speichern</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Pencil, Trash2, X, Link as LinkIcon, ExternalLink, Video, Calendar, GraduationCap, FileText, Folder } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String })

const kategorien = [
  { value: 'kajabi', label: 'Kajabi Videokurse', icon: GraduationCap },
  { value: 'livecall', label: 'Live-Calls', icon: Video },
  { value: 'termin', label: 'Termine', icon: Calendar },
  { value: 'dokument', label: 'Externe Dokumente', icon: FileText },
  { value: 'datenraum', label: 'Datenräume', icon: Folder },
  { value: 'allgemein', label: 'Allgemein', icon: LinkIcon },
]

const links = ref([])
const showModal = ref(false)
const editing = ref(null)
const form = ref({ kategorie: 'kajabi', titel: '', url: '', beschreibung: '' })

function byCategory(kat) {
  return links.value.filter(l => l.kategorie === kat)
}

async function load() {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    links.value = t.linksJson ? JSON.parse(t.linksJson) : []
  } catch (e) { console.error(e) }
}

onMounted(load)

function openNew() {
  editing.value = null
  form.value = { kategorie: 'kajabi', titel: '', url: '', beschreibung: '' }
  showModal.value = true
}

function openEdit(l) {
  editing.value = l
  form.value = { ...l }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editing.value = null
}

async function saveLink() {
  if (editing.value) {
    const idx = links.value.findIndex(l => l.id === editing.value.id)
    if (idx >= 0) links.value[idx] = { ...editing.value, ...form.value }
  } else {
    links.value.push({ id: 'l' + Date.now(), ...form.value, createdAt: new Date().toISOString() })
  }
  await persist()
  closeModal()
}

async function deleteLink(l) {
  if (!confirm('Link wirklich löschen?')) return
  links.value = links.value.filter(x => x.id !== l.id)
  await persist()
}

async function persist() {
  await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, linksJson: JSON.stringify(links.value) } })
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]; }
</style>
