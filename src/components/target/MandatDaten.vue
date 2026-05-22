<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-2">Meine Mandats-Daten</h2>
    <p class="text-sm text-gray-500 mb-5">Bitte ergänze hier alle relevanten Informationen zu deinem Verkaufsprojekt.</p>

    <!-- Fortschritts-Übersicht -->
    <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">Vollständigkeit</span>
        <span class="text-sm font-bold text-[#097e92]">{{ filledCount }} / {{ totalFields }} Felder</span>
      </div>
      <div class="w-full bg-gray-100 rounded-full h-2">
        <div class="bg-[#097e92] h-2 rounded-full transition-all" :style="`width: ${progress}%`"></div>
      </div>
      <div class="text-xs text-gray-400 mt-1">{{ progress }}% komplett</div>
    </div>

    <!-- Kontaktdaten -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <User class="w-4 h-4 text-[#097e92]" />
        <h3 class="font-semibold text-gray-800 text-sm">Persönliche Kontaktdaten</h3>
        <span class="ml-auto text-xs text-gray-400">{{ countSection(kontaktdatenFields) }} / {{ kontaktdatenFields.length }}</span>
      </header>
      <div class="p-5 grid grid-cols-2 gap-4">
        <Field v-model="data.vorname" label="Vorname" @blur="save" />
        <Field v-model="data.name" label="Name" @blur="save" />
        <Field v-model="data.privatEmail" label="Private E-Mail-Adresse" type="email" @blur="save" />
        <Field v-model="data.privatHandy" label="Private Handy-Nummer" @blur="save" />
      </div>
    </section>

    <!-- Links und Unterlagen -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <LinkIcon class="w-4 h-4 text-[#097e92]" />
        <h3 class="font-semibold text-gray-800 text-sm">Links und Unterlagen</h3>
        <span class="ml-auto text-xs text-gray-400">{{ countSection(unterlagenFields) }} / {{ unterlagenFields.length }}</span>
      </header>
      <div class="p-5 space-y-4">
        <LinkField v-model="data.websiteUrl" label="Webseite" placeholder="https://…" @blur="save" />
        <LinkField v-model="data.crmKontaktUrl" label="CRM-Kontakt" placeholder="Link zum CRM-Kontakt" @blur="save" />
        <LinkField v-model="data.bewertungLink" label="Unternehmensbewertung (Fragebogen)" placeholder="https://www.dropbox.com/…" @blur="save"
          :hint="bewertungVorlage" />
        <LinkField v-model="data.bewertungDokumentLink" label="Dokument der Unternehmensbewertung" placeholder="Link zum fertigen Bewertungs-Dokument" @blur="save" />
        <LinkField v-model="data.exposeLink" label="Exposé" placeholder="Link zum vorbereiteten Exposé" @blur="save" />
        <LinkField v-model="data.datenraumLink" label="Datenraum" placeholder="Link zum Datenraum" @blur="save" />
        <LinkField v-model="data.ndaLink" label="NDA / Verschwiegenheitserklärung" placeholder="Link zur Verschwiegenheitserklärung" @blur="save" />
      </div>
    </section>

    <!-- Kundennummer und Datenraum -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <Database class="w-4 h-4 text-[#097e92]" />
        <h3 class="font-semibold text-gray-800 text-sm">Kundennummer und Datenraum</h3>
        <span class="ml-auto text-xs text-gray-400">{{ countSection(datenraumFields) }} / {{ datenraumFields.length }}</span>
      </header>
      <div class="p-5 space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <Field v-model="data.kundennummer" label="Kundennummer" @blur="save" />
          <Field v-model="data.transaktionsnummer" label="Transaktionsnummer" @blur="save" />
        </div>
        <Field v-model="data.datenraumBeschreibung" label="Beschreibung" textarea @blur="save" />
        <LinkField v-model="data.sharepointLink" label="Link zum Sharepoint-Ordner" placeholder="https://…sharepoint.com/…" @blur="save" />
      </div>
    </section>

    <!-- Potentielle Käufer -->
    <section class="bg-white rounded-xl border border-gray-100 mb-4">
      <header class="px-5 py-3 border-b border-gray-50 flex items-center gap-2">
        <Users class="w-4 h-4 text-[#097e92]" />
        <h3 class="font-semibold text-gray-800 text-sm">Potentielle Käufer</h3>
        <span class="ml-auto text-xs text-gray-400">{{ kaeufer.length }} hinterlegt</span>
        <button @click="showKaeuferModal = true" class="text-xs text-[#097e92] hover:underline flex items-center gap-1 ml-3">
          <Plus class="w-3 h-3" /> Hinzufügen
        </button>
      </header>
      <div class="p-5">
        <div v-if="!kaeufer.length" class="text-center text-sm text-gray-400 py-6">
          Noch keine potentiellen Käufer eingetragen.
        </div>
        <div v-else class="space-y-2">
          <div v-for="k in kaeufer" :key="k.RowKey" class="flex items-start gap-3 p-3 rounded-xl border border-gray-100 hover:border-[#097e92]/30">
            <div class="w-9 h-9 bg-[#097e92]/10 rounded-lg flex items-center justify-center flex-shrink-0">
              <User class="w-4 h-4 text-[#097e92]" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-gray-800">{{ k.vorname }} {{ k.name }}</div>
              <div class="text-xs text-gray-500">{{ k.unternehmen }}</div>
              <div class="flex gap-3 text-xs text-gray-400 mt-1">
                <span v-if="k.email">{{ k.email }}</span>
                <span v-if="k.telefon">· {{ k.telefon }}</span>
              </div>
              <div v-if="k.beschreibung" class="text-xs text-gray-500 mt-1">{{ k.beschreibung }}</div>
            </div>
            <button @click="deleteKaeufer(k)" class="text-gray-300 hover:text-red-500"><Trash2 class="w-4 h-4" /></button>
          </div>
        </div>
      </div>
    </section>

    <!-- Modal: Käufer hinzufügen -->
    <div v-if="showKaeuferModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-900">Potentieller Käufer</h3>
          <button @click="showKaeuferModal = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="col-span-1">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Vorname</label>
            <input v-model="kaeuferForm.vorname" class="input" />
          </div>
          <div class="col-span-1">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Name</label>
            <input v-model="kaeuferForm.name" class="input" />
          </div>
          <div class="col-span-2">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Unternehmen</label>
            <input v-model="kaeuferForm.unternehmen" class="input" />
          </div>
          <div class="col-span-2">
            <label class="text-xs font-medium text-gray-600 mb-1 block">E-Mail</label>
            <input v-model="kaeuferForm.email" type="email" class="input" />
          </div>
          <div class="col-span-2">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Telefon</label>
            <input v-model="kaeuferForm.telefon" class="input" />
          </div>
          <div class="col-span-2">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Beschreibung</label>
            <textarea v-model="kaeuferForm.beschreibung" rows="2" class="input resize-none"></textarea>
          </div>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="showKaeuferModal = false" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
          <button @click="addKaeufer" class="flex-1 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium">Speichern</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h, defineComponent } from 'vue'
import { User, Users, Database, Plus, Trash2, X, Link as LinkIcon } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String, readOnly: Boolean })

const data = ref({
  vorname: '', name: '',
  privatEmail: '', privatHandy: '',
  websiteUrl: '', crmKontaktUrl: '',
  bewertungLink: '', bewertungDokumentLink: '',
  exposeLink: '', datenraumLink: '', ndaLink: '',
  kundennummer: '', transaktionsnummer: '',
  datenraumBeschreibung: '', sharepointLink: '',
})
const kaeufer = ref([])
const showKaeuferModal = ref(false)
const kaeuferForm = ref({ vorname: '', name: '', unternehmen: '', email: '', telefon: '', beschreibung: '' })

const bewertungVorlage = 'Vorlage: https://www.dropbox.com/scl/fi/vmafrqdpk13qil12kgfoi/Fragebogen-Unternehmensbewertung-blanko-2021-Kurzfassung.xlsx'

const kontaktdatenFields = ['vorname', 'name', 'privatEmail', 'privatHandy']
const unterlagenFields = ['websiteUrl', 'crmKontaktUrl', 'bewertungLink', 'bewertungDokumentLink', 'exposeLink', 'datenraumLink', 'ndaLink']
const datenraumFields = ['kundennummer', 'transaktionsnummer', 'datenraumBeschreibung', 'sharepointLink']
const allFields = [...kontaktdatenFields, ...unterlagenFields, ...datenraumFields]
const totalFields = allFields.length

const filledCount = computed(() => allFields.filter(f => data.value[f]?.trim()).length)
const progress = computed(() => Math.round((filledCount.value / totalFields) * 100))

function countSection(fields) {
  return fields.filter(f => data.value[f]?.trim()).length
}

onMounted(async () => {
  if (!props.targetId) return
  try {
    const target = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    // Bestehende Felder ins data-Objekt mergen
    for (const k of Object.keys(data.value)) {
      if (target[k] !== undefined) data.value[k] = target[k]
    }
    kaeufer.value = await authFetch(`/targets/${props.targetId}/kaeufer`)
  } catch (e) { console.error(e) }
})

let saveTimer = null
async function save() {
  if (props.readOnly || !props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try { await authFetch('/target-update', { method: 'POST', data: { id: props.targetId,  ...data.value  } }) }
    catch (e) { console.error('save failed', e) }
  }, 500)
}

async function addKaeufer() {
  if (!kaeuferForm.value.name && !kaeuferForm.value.email) return
  const created = await authFetch(`/targets/${props.targetId}/kaeufer`, { method: 'POST', data: kaeuferForm.value })
  kaeufer.value.push(created)
  showKaeuferModal.value = false
  kaeuferForm.value = { vorname: '', name: '', unternehmen: '', email: '', telefon: '', beschreibung: '' }
}

async function deleteKaeufer(k) {
  if (!confirm('Käufer entfernen?')) return
  await authFetch(`/targets/${props.targetId}/kaeufer/${k.RowKey}`, { method: 'DELETE' })
  kaeufer.value = kaeufer.value.filter(x => x.RowKey !== k.RowKey)
}

// Mini-Komponenten
const Field = defineComponent({
  props: ['modelValue', 'label', 'type', 'textarea'],
  emits: ['update:modelValue', 'blur'],
  setup(props, { emit }) {
    return () => h('div', [
      h('label', { class: 'block text-xs font-medium text-gray-600 mb-1' }, props.label),
      props.textarea
        ? h('textarea', {
            value: props.modelValue,
            rows: 2,
            onInput: e => emit('update:modelValue', e.target.value),
            onBlur: () => emit('blur'),
            class: 'w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92] resize-none'
          })
        : h('input', {
            type: props.type || 'text',
            value: props.modelValue,
            onInput: e => emit('update:modelValue', e.target.value),
            onBlur: () => emit('blur'),
            class: 'w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]'
          })
    ])
  }
})

const LinkField = defineComponent({
  props: ['modelValue', 'label', 'placeholder', 'hint'],
  emits: ['update:modelValue', 'blur'],
  setup(props, { emit }) {
    return () => h('div', [
      h('label', { class: 'block text-xs font-medium text-gray-600 mb-1' }, props.label),
      h('div', { class: 'flex gap-2' }, [
        h('input', {
          type: 'url',
          value: props.modelValue,
          placeholder: props.placeholder,
          onInput: e => emit('update:modelValue', e.target.value),
          onBlur: () => emit('blur'),
          class: 'flex-1 px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]'
        }),
        props.modelValue
          ? h('a', { href: props.modelValue, target: '_blank', rel: 'noopener', class: 'px-3 py-2 border border-gray-200 rounded-xl hover:bg-gray-50 text-[#097e92]', title: 'öffnen' }, '↗')
          : null
      ]),
      props.hint ? h('div', { class: 'text-xs text-gray-400 mt-1' }, props.hint) : null
    ])
  }
})
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]; }
</style>
