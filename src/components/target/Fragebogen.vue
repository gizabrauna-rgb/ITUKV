<template>
  <div>
    <div class="mb-4">
      <h2 class="text-xl font-bold text-gray-900 mb-1">Fragebogen Unternehmensbewertung</h2>
      <p class="text-sm text-gray-500">Bitte fülle alle Bereiche aus – wir nutzen die Daten zur Bewertung deines Unternehmens und zur Erstellung des anonymisierten Exposés.</p>
    </div>

    <!-- Fortschritt -->
    <div class="bg-white rounded-xl border border-gray-100 p-4 mb-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">Gesamtfortschritt</span>
        <span class="text-sm font-bold text-[#097e92]">{{ filledCount }} / {{ totalFields }} ({{ progress }}%)</span>
      </div>
      <div class="w-full bg-gray-100 rounded-full h-2">
        <div class="bg-[#097e92] h-2 rounded-full transition-all" :style="`width: ${progress}%`"></div>
      </div>
    </div>

    <!-- Sektion-Navigation -->
    <div class="flex flex-wrap gap-1 mb-4 bg-white rounded-xl border border-gray-100 p-1">
      <button v-for="(s, i) in sections" :key="i" @click="activeSection = i"
        :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                activeSection === i ? 'bg-[#097e92] text-white' : 'text-gray-600 hover:bg-gray-50']">
        <span class="text-[10px] opacity-70">{{ i + 1 }}</span>
        {{ s.kurz }}
        <Check v-if="sectionDone(i)" class="w-3 h-3" />
      </button>
    </div>

    <!-- Sektion-Inhalt -->
    <div class="bg-white rounded-xl border border-gray-100 p-6">
      <h3 class="font-bold text-gray-900 mb-1">{{ currentSection.titel }}</h3>
      <p v-if="currentSection.hinweis" class="text-xs text-gray-500 mb-4">{{ currentSection.hinweis }}</p>

      <!-- Sektion 0: Stammdaten -->
      <div v-if="activeSection === 0" class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <Feld v-model="data.unternehmensname" label="Unternehmensname *" />
          <div>
            <label class="lbl">Gesellschaftsform *</label>
            <select v-model="data.gesellschaftsform" @blur="save" class="input">
              <option value="">— wählen —</option>
              <option>GmbH</option><option>UG</option><option>GmbH & Co. KG</option>
              <option>AG</option><option>GbR</option><option>Einzelunternehmen</option>
            </select>
          </div>
          <Feld v-model="data.gesellschafter1" label="1. Gesellschafter (Name + Anteil)" />
          <Feld v-model="data.gesellschafter2" label="2. Gesellschafter (Name + Anteil)" />
          <Feld v-model="data.gesellschafter3" label="3. Gesellschafter (Name + Anteil)" />
          <Feld v-model="data.gf1" label="1. Geschäftsführer" />
          <Feld v-model="data.gf2" label="2. Geschäftsführer" />
          <Feld v-model="data.gruendungsjahr" label="Gründungsjahr" type="number" />
          <Feld v-model="data.plzOrt" label="PLZ / Ort" />
          <Feld v-model="data.stammkapital" label="Stammkapital (€)" type="number" />
          <Feld v-model="data.gf1Alter" label="Alter / Geburtsdatum 1. GF" />
          <Feld v-model="data.gesellschafter1Alter" label="Alter / Geburtsdatum 1. Gesellschafter" />
        </div>
        <ToggleFeld v-model="data.besitzgesellschaft" label="Gibt es im Hintergrund eine Besitz-/Verwaltungsgesellschaft?" />
        <Feld v-if="data.besitzgesellschaft" v-model="data.besitzgesellschaftName" label="Bezeichnung der Besitzgesellschaft" />
        <ToggleFeld v-model="data.eigeneImmobilie" label="Hat das Unternehmen eine eigene Immobilie, die selbst genutzt wird?" />
      </div>

      <!-- Sektion 1: Dokumente-Checkliste -->
      <div v-else-if="activeSection === 1" class="space-y-3">
        <div v-for="(d, di) in dokumente" :key="di" class="flex items-center gap-3 p-3 border border-gray-100 rounded-lg">
          <select v-model="data.dokumenteStatus[di]" @blur="save" class="text-xs border border-gray-200 rounded-lg px-2 py-1 w-32">
            <option value="">— Status —</option>
            <option value="bereit">liegt bereit</option>
            <option value="in_arbeit">wird erstellt</option>
            <option value="nicht_vorhanden">nicht vorhanden</option>
          </select>
          <div class="flex-1 text-sm text-gray-700">{{ d }}</div>
        </div>
      </div>

      <!-- Sektion 2: Wartungsverträge -->
      <div v-else-if="activeSection === 2" class="space-y-3">
        <p class="text-xs text-gray-500">Jahresumsätze aus Service- und Wartungsverträgen</p>
        <div v-for="jahr in [2020, 2021, 2022, 2023, 2024]" :key="jahr" class="grid grid-cols-3 gap-3 items-center">
          <div class="text-sm text-gray-700">Jahr {{ jahr }}</div>
          <Feld v-model="data.wartungUmsatz[jahr]" :type="'number'" :placeholder="'€'" />
          <label class="flex items-center gap-2 text-xs text-gray-600">
            <input type="checkbox" v-model="data.wartungGeschaetzt[jahr]" @change="save" class="rounded" />
            geschätzt
          </label>
        </div>
      </div>

      <!-- Sektion 3: Personal -->
      <div v-else-if="activeSection === 3" class="space-y-4">
        <Feld v-model="data.anzahlGf" label="Anzahl Geschäftsführer" type="number" />
        <div v-for="abt in ['technik', 'vertrieb', 'innendienst']" :key="abt">
          <h4 class="font-semibold text-sm text-gray-800 mb-2 capitalize">Abteilung {{ abt === 'innendienst' ? 'Innendienst (Verwaltung, Buchhaltung)' : abt }}</h4>
          <div class="grid grid-cols-4 gap-3">
            <Feld v-model="data.personal[abt+'Vollzeit']" label="Vollzeit" type="number" />
            <Feld v-model="data.personal[abt+'Azubis']" label="Azubis" type="number" />
            <Feld v-model="data.personal[abt+'Aushilfen']" label="Aushilfen" type="number" />
            <Feld v-model="data.personal[abt+'Aufgaben']" label="Aufgaben" />
          </div>
        </div>
      </div>

      <!-- Sektion 4: Zeitaufteilung GF -->
      <div v-else-if="activeSection === 4" class="space-y-4">
        <div v-for="gf in [1, 2]" :key="gf">
          <h4 class="font-semibold text-sm text-gray-800 mb-2">{{ gf }}. Geschäftsführer – Zeitaufteilung (%)</h4>
          <div class="grid grid-cols-4 gap-3 mb-2">
            <Feld v-model="data.zeitGf[gf].technik" label="Technik %" type="number" />
            <Feld v-model="data.zeitGf[gf].vertrieb" label="Vertrieb %" type="number" />
            <Feld v-model="data.zeitGf[gf].innendienst" label="Innendienst %" type="number" />
            <Feld v-model="data.zeitGf[gf].geschaeftsfuehrung" label="GF %" type="number" />
          </div>
          <div :class="['text-xs px-3 py-2 rounded-lg', sumZeit(gf) === 100 ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700']">
            Summe: {{ sumZeit(gf) }}% {{ sumZeit(gf) === 100 ? '✓' : '— sollte 100 % ergeben' }}
          </div>
        </div>
      </div>

      <!-- Sektion 5: Kundenstruktur -->
      <div v-else-if="activeSection === 5" class="space-y-3">
        <Feld v-model="data.aktiveGeschaeftskunden" label="Anzahl aktiver Geschäftskunden" type="number" />
        <Feld v-model="data.privatkundenAnteil" label="Anteil Privatkunden in %" type="number" />
        <FeldText v-model="data.branchenschwerpunkte" label="Branchenschwerpunkte" placeholder="z.B. Industrie, Steuerberater, Arztpraxen, Handel..." />
        <Feld v-model="data.typischeArbeitsplaetze" label="PC-Arbeitsplätze pro Kunde" placeholder="z.B. 20 bis 250" />
        <Feld v-model="data.kundenRegionen" label="Hauptregionen" placeholder="z.B. 50 km um PLZ 295.." />
      </div>

      <!-- Sektion 6: Wachstum & Wettbewerb -->
      <div v-else-if="activeSection === 6" class="space-y-3">
        <FeldText v-model="data.wachstumspotenzial" label="Wachstumspotenzial" placeholder="positiv formulieren..." rows="4" />
        <FeldText v-model="data.wettbewerbssituation" label="Wettbewerbssituation" placeholder="z.B. 3 direkte regionale Wettbewerber..." rows="4" />
      </div>

      <!-- Sektion 7: Lösungen (Skala 1-10) -->
      <div v-else-if="activeSection === 7" class="space-y-2">
        <p class="text-xs text-gray-500 mb-2">Bewerte die Bedeutung jeder Lösung von 1 (unwichtig) bis 10 (sehr wichtig)</p>
        <SkalaFeld v-for="(l, i) in loesungen" :key="i" :label="l"
          v-model="data.loesungen[l]" @blur="save" />
        <Feld v-model="data.loesungenSonstiges" label="Sonstiges (direkt eintragen)" />
      </div>

      <!-- Sektion 8: Lieferanten / Partner -->
      <div v-else-if="activeSection === 8" class="space-y-3">
        <div v-for="(p, pi) in data.partner" :key="pi" class="grid grid-cols-12 gap-2 items-start">
          <div class="col-span-3"><input v-model="p.name" @blur="save" placeholder="Lieferant" class="input text-sm" /></div>
          <div class="col-span-3"><input v-model="p.status" @blur="save" placeholder="Status (z.B. Premium Partner)" class="input text-sm" /></div>
          <div class="col-span-5"><input v-model="p.bemerkung" @blur="save" placeholder="Bemerkungen" class="input text-sm" /></div>
          <button @click="data.partner.splice(pi, 1); save()" class="text-red-400 hover:text-red-600 text-xs p-2"><X class="w-4 h-4" /></button>
        </div>
        <button @click="data.partner.push({name:'',status:'',bemerkung:''}); save()" class="w-full border border-dashed border-gray-300 text-xs py-2 rounded-lg text-gray-500 hover:text-[#097e92] hover:border-[#097e92] flex items-center justify-center gap-1.5">
          <Plus class="w-3.5 h-3.5" /> Partner hinzufügen
        </button>
      </div>

      <!-- Sektion 9: Verkaufsgründe -->
      <div v-else-if="activeSection === 9" class="space-y-2">
        <p class="text-xs text-gray-500 mb-2">Bewerte jeden Grund von 1 (unwichtig) bis 10 (sehr wichtig)</p>
        <SkalaFeld v-for="(g, i) in verkaufsgruende" :key="i" :label="g"
          v-model="data.verkaufsgruende[g]" @blur="save" />
        <Feld v-model="data.verkaufsgruendeSonstige" label="Weitere Gründe (direkt eintragen)" />
      </div>

      <!-- Sektion 10: Feinheiten der Übergabe -->
      <div v-else-if="activeSection === 10" class="space-y-3">
        <ToggleFeld v-model="data.verbleibImUnternehmen" label="Wollen Sie nach dem Verkauf im Unternehmen verbleiben (z.B. als angestellte Führungskraft, Teilgesellschafter)?" />
        <FeldText v-model="data.verbleibDetails" label="Falls ja: Details" rows="2" />
        <FeldText v-model="data.uebergabeVerfuegbarkeit" label="Wie können Sie dem Käufer nach dem Verkauf zur Übergabe zur Verfügung stehen?" placeholder="z.B. 3 Monate, 10 Std. pro Woche" rows="3" />
        <FeldText v-model="data.assetDealDetails" label="Asset Deal: Welche Anlagegüter zu welchen Preisen?" placeholder="z.B. VW Golf Bj.2013 für 10.000 €, Mietvertrag 700 € mtl." rows="3" />
      </div>
    </div>

    <!-- Navigation Buttons -->
    <div class="flex items-center justify-between mt-4">
      <button @click="activeSection = Math.max(0, activeSection - 1)" :disabled="activeSection === 0"
        class="flex items-center gap-1.5 px-4 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50 disabled:opacity-40">
        <ChevronLeft class="w-4 h-4" /> Zurück
      </button>
      <div class="text-xs text-gray-400">Auto-Speichern aktiv</div>
      <button @click="activeSection = Math.min(sections.length - 1, activeSection + 1)" :disabled="activeSection === sections.length - 1"
        class="flex items-center gap-1.5 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm hover:bg-[#0a9aaf] disabled:opacity-40">
        Weiter <ChevronRight class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { Check, ChevronLeft, ChevronRight, Plus, X } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String })

const sections = [
  { kurz: 'Stammdaten', titel: 'Stammdaten zum Unternehmen', hinweis: '' },
  { kurz: 'Dokumente', titel: 'Checkliste Dokumente', hinweis: 'Bitte angeben welche Unterlagen verfügbar sind. Die Dateien selbst lädst du im Dokumente-Tab hoch.' },
  { kurz: 'Wartung', titel: 'Wartungsverträge / Wiederkehrende Umsätze', hinweis: 'Jahresumsatz aus Service- und Wartungsverträgen' },
  { kurz: 'Personal', titel: 'Personal und Geschäftsführung', hinweis: '' },
  { kurz: 'GF-Zeit', titel: 'Zeitaufteilung Geschäftsführer', hinweis: 'Wofür verwendest du deine Arbeitszeit? Summe = 100 %' },
  { kurz: 'Kunden', titel: 'Kundenstruktur', hinweis: '' },
  { kurz: 'Wachstum', titel: 'Wachstumspotenzial und Wettbewerbssituation', hinweis: '' },
  { kurz: 'Lösungen', titel: 'Schwerpunkte bei Lösungen', hinweis: '' },
  { kurz: 'Partner', titel: 'Wichtigste Lieferanten & Partner', hinweis: '' },
  { kurz: 'Verkaufsgründe', titel: 'Gründe für die Suche nach einem Käufer', hinweis: '' },
  { kurz: 'Übergabe', titel: 'Feinheiten der Übergabe', hinweis: '' },
]

const dokumente = [
  'Bilanzen der letzten 3 Jahre (direkt vom Steuerberater)',
  'BWAs der letzten 3 Jahre',
  'Kundenliste (anonymisiert), sortiert nach Umsatz/Ertrag',
  'Vertragsliste (anonymisiert), sortiert nach Umsatz/Ertrag',
  'Liste der Vertragsarten mit typischen Laufzeiten, Inhalten',
  'Mitarbeiterliste (anonymisiert): Gehälter, Zugehörigkeit, Qualifizierung, Alter, Aufgaben',
  'Preisliste für eigene IT-Dienstleistungen',
]

const loesungen = [
  'IT Service (Zeit gegen Geld)', 'Managed IT Services', 'IT Infrastruktur',
  'IT Security', 'Telefonanlagen', 'Drucker/Kopierer', 'Anwendungssoftware'
]

const verkaufsgruende = [
  'Jetzigen Unternehmenswert zu Geld machen',
  'Wachsendes Unternehmen braucht kapitalstarken Partner',
  'Trennung von einem Gesellschafter / Geschäftspartner',
  'Fokussierung auf einen anderen Geschäftsbereich',
  'Berufliche Interessen haben sich verändert',
  'Altersnachfolge gesucht',
  'Perspektive des Unternehmens schwierig',
  'Finanzielle Engpässe',
  'Persönliche Gründe (z.B. Gesundheit, Wohnortwechsel)',
]

const data = ref({
  unternehmensname: '', gesellschaftsform: '',
  gesellschafter1: '', gesellschafter2: '', gesellschafter3: '',
  gf1: '', gf2: '', gruendungsjahr: '', plzOrt: '', stammkapital: '',
  gf1Alter: '', gesellschafter1Alter: '',
  besitzgesellschaft: false, besitzgesellschaftName: '',
  eigeneImmobilie: false,
  dokumenteStatus: {},
  wartungUmsatz: {}, wartungGeschaetzt: {},
  anzahlGf: '',
  personal: {
    technikVollzeit:'', technikAzubis:'', technikAushilfen:'', technikAufgaben:'',
    vertriebVollzeit:'', vertriebAzubis:'', vertriebAushilfen:'', vertriebAufgaben:'',
    innendienstVollzeit:'', innendienstAzubis:'', innendienstAushilfen:'', innendienstAufgaben:'',
  },
  zeitGf: { 1: { technik:'', vertrieb:'', innendienst:'', geschaeftsfuehrung:'' },
            2: { technik:'', vertrieb:'', innendienst:'', geschaeftsfuehrung:'' } },
  aktiveGeschaeftskunden: '', privatkundenAnteil: '',
  branchenschwerpunkte: '', typischeArbeitsplaetze: '', kundenRegionen: '',
  wachstumspotenzial: '', wettbewerbssituation: '',
  loesungen: {}, loesungenSonstiges: '',
  partner: [],
  verkaufsgruende: {}, verkaufsgruendeSonstige: '',
  verbleibImUnternehmen: false, verbleibDetails: '',
  uebergabeVerfuegbarkeit: '', assetDealDetails: '',
})

const activeSection = ref(0)
const currentSection = computed(() => sections[activeSection.value])

function sumZeit(gf) {
  const z = data.value.zeitGf[gf]
  return ['technik','vertrieb','innendienst','geschaeftsfuehrung']
    .reduce((s, k) => s + (parseFloat(z[k]) || 0), 0)
}

// Sehr grobe Fortschritts-Schätzung
const allFieldKeys = ['unternehmensname','gesellschaftsform','gesellschafter1','gf1','gruendungsjahr','plzOrt','stammkapital',
  'anzahlGf','aktiveGeschaeftskunden','wachstumspotenzial','wettbewerbssituation','uebergabeVerfuegbarkeit']
const totalFields = ref(60)
const filledCount = computed(() => {
  let c = 0
  for (const k of allFieldKeys) if ((data.value[k]||'').toString().trim()) c++
  // Wartungsumsatz
  c += Object.values(data.value.wartungUmsatz).filter(v => v && v !== '').length
  // Personal
  c += Object.values(data.value.personal).filter(v => v && v !== '').length
  // Loesungen
  c += Object.keys(data.value.loesungen).length
  // Verkaufsgruende
  c += Object.keys(data.value.verkaufsgruende).length
  // Partner
  c += data.value.partner.length
  // Zeit GF
  c += [1,2].reduce((s,g) => s + Object.values(data.value.zeitGf[g]).filter(v => v).length, 0)
  return c
})
const progress = computed(() => Math.min(100, Math.round((filledCount.value / totalFields.value) * 100)))

function sectionDone(idx) {
  // sehr grob: nur wenn Pflichtfelder dieser Sektion gefüllt
  if (idx === 0) return !!(data.value.unternehmensname && data.value.gesellschaftsform)
  if (idx === 4) return sumZeit(1) === 100 && sumZeit(2) === 100
  if (idx === 6) return !!(data.value.wachstumspotenzial && data.value.wettbewerbssituation)
  return false
}

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch('/target-update', { method: 'POST', data: { id: props.targetId,  fragebogenJson: JSON.stringify(data.value)  } })
    } catch (e) { console.error(e) }
  }, 600)
}

onMounted(async () => {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (t.fragebogenJson) {
      try {
        const parsed = JSON.parse(t.fragebogenJson)
        // Sicheres Merge
        data.value = { ...data.value, ...parsed,
          personal: { ...data.value.personal, ...(parsed.personal || {}) },
          zeitGf: { 1: { ...data.value.zeitGf[1], ...(parsed.zeitGf?.[1] || {}) },
                    2: { ...data.value.zeitGf[2], ...(parsed.zeitGf?.[2] || {}) } },
          dokumenteStatus: { ...data.value.dokumenteStatus, ...(parsed.dokumenteStatus || {}) },
          wartungUmsatz: { ...data.value.wartungUmsatz, ...(parsed.wartungUmsatz || {}) },
          wartungGeschaetzt: { ...data.value.wartungGeschaetzt, ...(parsed.wartungGeschaetzt || {}) },
          loesungen: { ...data.value.loesungen, ...(parsed.loesungen || {}) },
          verkaufsgruende: { ...data.value.verkaufsgruende, ...(parsed.verkaufsgruende || {}) },
          partner: parsed.partner || [],
        }
      } catch (e) { console.error(e) }
    }
  } catch (e) { console.error(e) }
})

// Mini-Komponenten
const Feld = defineComponent({
  props: ['modelValue', 'label', 'type', 'placeholder'],
  emits: ['update:modelValue', 'blur'],
  setup(props, { emit }) {
    return () => h('div', [
      h('label', { class: 'lbl' }, props.label),
      h('input', {
        type: props.type || 'text',
        value: props.modelValue,
        placeholder: props.placeholder || '',
        onInput: e => emit('update:modelValue', e.target.value),
        onBlur: () => emit('blur'),
        class: 'input'
      })
    ])
  }
})

const FeldText = defineComponent({
  props: ['modelValue', 'label', 'placeholder', 'rows'],
  emits: ['update:modelValue', 'blur'],
  setup(props, { emit }) {
    return () => h('div', [
      h('label', { class: 'lbl' }, props.label),
      h('textarea', {
        value: props.modelValue,
        rows: props.rows || 2,
        placeholder: props.placeholder || '',
        onInput: e => emit('update:modelValue', e.target.value),
        onBlur: () => emit('blur'),
        class: 'input resize-none'
      })
    ])
  }
})

const ToggleFeld = defineComponent({
  props: ['modelValue', 'label'],
  emits: ['update:modelValue', 'blur'],
  setup(props, { emit }) {
    return () => h('label', { class: 'flex items-center gap-2 cursor-pointer text-sm' }, [
      h('input', {
        type: 'checkbox',
        checked: props.modelValue,
        onChange: e => { emit('update:modelValue', e.target.checked); emit('blur') },
        class: 'rounded border-gray-300 text-[#097e92] focus:ring-[#097e92]/30'
      }),
      h('span', { class: 'text-gray-700' }, props.label)
    ])
  }
})

const SkalaFeld = defineComponent({
  props: ['modelValue', 'label'],
  emits: ['update:modelValue', 'blur'],
  setup(props, { emit }) {
    return () => h('div', { class: 'flex items-center gap-3 py-1.5' }, [
      h('div', { class: 'flex-1 text-sm text-gray-700' }, props.label),
      h('div', { class: 'flex gap-1' },
        Array.from({ length: 10 }, (_, i) => i + 1).map(n =>
          h('button', {
            type: 'button',
            onClick: () => { emit('update:modelValue', n); emit('blur') },
            class: `w-7 h-7 rounded text-xs font-medium ${props.modelValue >= n ? 'bg-[#097e92] text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`
          }, n)
        )
      )
    ])
  }
})
</script>

<style scoped>
@reference "tailwindcss";
.lbl { @apply block text-xs font-medium text-gray-600 mb-1; }
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]; }
</style>
