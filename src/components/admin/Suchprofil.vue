<template>
  <div>
    <div class="mb-5">
      <h2 class="text-xl font-bold text-gray-900">Suchprofil</h2>
      <p class="text-sm text-gray-500 mt-1">Welche Targets sucht der Käufer? Diese Kriterien werden für die automatische Long-List genutzt.</p>
    </div>

    <div class="bg-white rounded-xl border border-gray-100 p-5 space-y-4">
      <!-- Region -->
      <div>
        <h3 class="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
          <MapPin class="w-4 h-4 text-[#0088ba]" /> Region / Geographie
        </h3>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-gray-600 mb-1 block">PLZ-Mittelpunkt</label>
            <input v-model="form.zentralPlz" placeholder="z.B. 50667" maxlength="5" class="input" @blur="save" />
          </div>
          <div>
            <label class="text-xs text-gray-600 mb-1 block">Umkreis (km)</label>
            <input v-model.number="form.umkreisKm" type="number" placeholder="z.B. 150" class="input" @blur="save" />
          </div>
          <div class="col-span-2">
            <label class="text-xs text-gray-600 mb-1 block">Erlaubte Bundesländer / Regionen</label>
            <input v-model="form.regionen" placeholder="z.B. NRW, Hessen, BaWü (Komma-getrennt)" class="input" @blur="save" />
          </div>
          <div class="col-span-2">
            <label class="text-xs text-gray-600 mb-1 block">Ausschluss-Regionen</label>
            <input v-model="form.regionenAusschluss" placeholder="z.B. Bayern (wenn bereits abgedeckt)" class="input" @blur="save" />
          </div>
        </div>
      </div>

      <!-- Größe -->
      <div class="pt-3 border-t border-gray-100">
        <h3 class="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
          <Users class="w-4 h-4 text-[#0088ba]" /> Unternehmensgröße
        </h3>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-gray-600 mb-1 block">Mitarbeiter von</label>
            <input v-model.number="form.maMin" type="number" placeholder="z.B. 10" class="input" @blur="save" />
          </div>
          <div>
            <label class="text-xs text-gray-600 mb-1 block">Mitarbeiter bis</label>
            <input v-model.number="form.maMax" type="number" placeholder="z.B. 100" class="input" @blur="save" />
          </div>
          <div>
            <label class="text-xs text-gray-600 mb-1 block">Umsatz von (TEUR)</label>
            <input v-model.number="form.umsatzMin" type="number" placeholder="z.B. 500" class="input" @blur="save" />
          </div>
          <div>
            <label class="text-xs text-gray-600 mb-1 block">Umsatz bis (TEUR)</label>
            <input v-model.number="form.umsatzMax" type="number" placeholder="z.B. 15000" class="input" @blur="save" />
          </div>
          <div>
            <label class="text-xs text-gray-600 mb-1 block">EBIT-Marge min. (%)</label>
            <input v-model.number="form.ebitMargeMin" type="number" step="0.5" placeholder="z.B. 8" class="input" @blur="save" />
          </div>
          <div>
            <label class="text-xs text-gray-600 mb-1 block">Wiederkehrende Umsätze min. (%)</label>
            <input v-model.number="form.recurringMin" type="number" placeholder="z.B. 30" class="input" @blur="save" />
          </div>
        </div>
      </div>

      <!-- IT-Fokus -->
      <div class="pt-3 border-t border-gray-100">
        <h3 class="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
          <Cpu class="w-4 h-4 text-[#0088ba]" /> IT-Fokus / Spezialisierung
        </h3>
        <div class="flex flex-wrap gap-2 mb-2">
          <label v-for="t in itFokusOptionen" :key="t" class="flex items-center gap-1.5 text-xs px-3 py-1.5 border rounded-xl cursor-pointer hover:bg-gray-50"
            :class="form.itFokus?.includes(t) ? 'border-[#0088ba] bg-[#0088ba]/5 text-[#0088ba]' : 'border-gray-200 text-gray-600'">
            <input type="checkbox" :checked="form.itFokus?.includes(t)" @change="toggleFokus(t)" class="sr-only" />
            {{ t }}
          </label>
        </div>
        <input v-model="form.itFokusSonstige" placeholder="Weitere Schwerpunkte (z.B. DATEV Systempartner, SAP)" class="input" @blur="save" />
      </div>

      <!-- Sonstige Kriterien -->
      <div class="pt-3 border-t border-gray-100">
        <h3 class="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
          <Filter class="w-4 h-4 text-[#0088ba]" /> Weitere Kriterien
        </h3>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-gray-600 mb-1 block">Pflichtkriterien (Must-Have)</label>
            <textarea v-model="form.mustHave" rows="2" placeholder="z.B. mind. 2 Jahre Altersnachfolge möglich, GmbH" class="input resize-y" @blur="save"></textarea>
          </div>
          <div>
            <label class="text-xs text-gray-600 mb-1 block">Ausschluss-Kriterien</label>
            <textarea v-model="form.ausschluss" rows="2" placeholder="z.B. eigene Immobilie, > 5 Gesellschafter" class="input resize-y" @blur="save"></textarea>
          </div>
          <div>
            <label class="text-xs text-gray-600 mb-1 block">Notizen / Sonstiges</label>
            <textarea v-model="form.notizen" rows="3" placeholder="Freitext" class="input resize-y" @blur="save"></textarea>
          </div>
        </div>
      </div>
    </div>

    <p v-if="lastSaved" class="text-xs text-gray-400 mt-3 text-center">Zuletzt gespeichert: {{ lastSavedHuman }}</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { MapPin, Users, Cpu, Filter } from '@lucide/vue'
import { authFetch } from '../../api.js'

const props = defineProps({ targetId: String })

const itFokusOptionen = ['MSP / Managed Services', 'IT-Security', 'Cloud (Azure/AWS)', 'ERP / SAP', 'Software-Entwicklung', 'Telefonanlagen', 'Drucker/Kopierer', 'Netzwerk', 'Beratung / Consulting']

const form = ref({
  zentralPlz: '', umkreisKm: 0,
  regionen: '', regionenAusschluss: '',
  maMin: 0, maMax: 0, umsatzMin: 0, umsatzMax: 0,
  ebitMargeMin: 0, recurringMin: 0,
  itFokus: [], itFokusSonstige: '',
  mustHave: '', ausschluss: '', notizen: '',
})
const lastSaved = ref(null)

function toggleFokus(t) {
  if (!form.value.itFokus) form.value.itFokus = []
  const i = form.value.itFokus.indexOf(t)
  if (i >= 0) form.value.itFokus.splice(i, 1)
  else form.value.itFokus.push(t)
  save()
}

let saveTimer = null
async function save() {
  if (!props.targetId) return
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await authFetch('/target-update', { method: 'POST', data: { id: props.targetId, suchprofilJson: JSON.stringify(form.value) } })
      lastSaved.value = new Date().toISOString()
    } catch (e) { console.error(e) }
  }, 600)
}

const lastSavedHuman = computed(() => lastSaved.value ? new Date(lastSaved.value).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) : '')

onMounted(async () => {
  if (!props.targetId) return
  try {
    const t = await authFetch('/target-get', { method: 'POST', data: { id: props.targetId } })
    if (t.suchprofilJson) {
      try { Object.assign(form.value, JSON.parse(t.suchprofilJson)) } catch {}
    }
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
</style>
