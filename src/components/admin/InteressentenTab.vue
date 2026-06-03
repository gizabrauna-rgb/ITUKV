<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Interessenten</h3>
        <p class="text-xs text-gray-500">{{ items.length }} Interessent{{ items.length === 1 ? '' : 'en' }} · Spalten werden automatisch gespeichert</p>
      </div>
      <div class="flex gap-2">
        <button @click="kompakt = !kompakt" :class="['flex items-center gap-1.5 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50']">
          <component :is="kompakt ? Maximize2 : Minimize2" class="w-4 h-4" />
          {{ kompakt ? 'Volltabelle' : 'Kompakt' }}
        </button>
        <button @click="exportCsv" class="flex items-center gap-1.5 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
          <Download class="w-4 h-4" /> CSV
        </button>
      </div>
    </div>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-400 text-sm">Lade…</div>
    <div v-else-if="!items.length" class="bg-white rounded-xl border border-gray-100 p-10 text-center">
      <Users class="w-10 h-10 mx-auto mb-3 text-gray-200" />
      <h3 class="font-semibold text-gray-700 mb-1">Noch keine Interessenten</h3>
      <p class="text-sm text-gray-500">Sobald sich jemand über die Landing-Page einträgt, erscheint er hier.</p>
    </div>

    <div v-else class="bg-white rounded-xl border border-gray-100 overflow-x-auto">
      <table class="w-full text-xs">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap w-20">Datum</th>
            <th class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Firma</th>
            <th class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Vorname</th>
            <th class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Nachname</th>
            <th class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">E-Mail</th>
            <th class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Telefon</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Website</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">PLZ + Ort</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap w-48">Mitteilung</th>
            <th class="text-center px-2 py-2 font-semibold text-gray-500 whitespace-nowrap w-16">NDA</th>
            <th class="text-center px-2 py-2 font-semibold text-gray-500 whitespace-nowrap w-14">Rating</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Ansprache</th>
            <th v-if="!kompakt" class="text-center px-2 py-2 font-semibold text-gray-500 whitespace-nowrap w-16">VETO</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap w-40">Notizen</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap w-40">Bemerkungen MB/JK</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap w-40">TODO M&A</th>
            <th v-if="!kompakt" class="text-center px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Freigabe VK</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Kontakt gesendet</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Erst-Telefonat</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">VK-Termin</th>
            <th v-if="!kompakt" class="text-left px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Gebot angefordert</th>
            <th v-if="!kompakt" class="text-right px-2 py-2 font-semibold text-gray-500 whitespace-nowrap">Aktuelles Gebot</th>
            <th class="text-center px-2 py-2 font-semibold text-gray-500 whitespace-nowrap w-20">Status</th>
            <th class="px-2 py-2 w-8"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="i in sorted" :key="i.RowKey" :class="['hover:bg-gray-50/50', i.veto ? 'bg-red-50/50' : '', i.zusage ? 'bg-green-50/50' : '', i.absage ? 'opacity-60' : '']">
            <td class="px-2 py-1.5 text-gray-500 whitespace-nowrap" :title="i.createdAt">{{ shortDate(i.createdAt) }}</td>
            <td class="px-2 py-1.5 font-medium text-gray-800">{{ i.firma || '—' }}</td>
            <td class="px-2 py-1.5">{{ i.vorname || splitName(i.name).vorname }}</td>
            <td class="px-2 py-1.5">{{ i.nachname || splitName(i.name).nachname }}</td>
            <td class="px-2 py-1.5">
              <a v-if="i.email" :href="`mailto:${i.email}`" class="text-[#0088ba] hover:underline">{{ i.email }}</a>
            </td>
            <td class="px-2 py-1.5"><a v-if="i.telefon" :href="`tel:${i.telefon}`" class="text-[#0088ba] hover:underline">{{ i.telefon }}</a></td>
            <td v-if="!kompakt" class="px-2 py-1.5"><a v-if="i.website" :href="i.website" target="_blank" class="text-[#0088ba] hover:underline truncate inline-block max-w-[150px]" :title="i.website">{{ i.website?.replace(/^https?:\/\//, '') }}</a></td>
            <td v-if="!kompakt" class="px-2 py-1.5 whitespace-nowrap">{{ [i.plz, i.ort].filter(Boolean).join(' ') }}</td>
            <td v-if="!kompakt" class="px-2 py-1.5 max-w-[200px] truncate" :title="i.kommentar">{{ i.kommentar }}</td>
            <td class="px-2 py-1.5 text-center">
              <span v-if="i.ndaStatus === 'unterzeichnet'" class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-700" title="NDA da">
                <Check class="w-3.5 h-3.5" />
              </span>
              <span v-else class="text-gray-300">—</span>
            </td>
            <td class="px-2 py-1.5 text-center">
              <select :value="i.rating || 0" @change="patch(i, { rating: parseInt($event.target.value) })" class="cell-input text-center w-12">
                <option value="0">—</option>
                <option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option>
              </select>
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5">
              <select :value="i.ansprache || ''" @change="patch(i, { ansprache: $event.target.value })" class="cell-input">
                <option value="">—</option><option>Du</option><option>Sie</option>
              </select>
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5 text-center">
              <button @click="patch(i, { veto: !i.veto })" :class="['inline-flex items-center justify-center w-6 h-6 rounded text-[10px] font-bold', i.veto ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-400']">
                {{ i.veto ? 'VETO' : '—' }}
              </button>
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5">
              <input :value="i.notiz || ''" @blur="patch(i, { notiz: $event.target.value })" class="cell-input w-40" />
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5">
              <input :value="i.bemerkungenMibeca || ''" @blur="patch(i, { bemerkungenMibeca: $event.target.value })" class="cell-input w-40" />
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5">
              <input :value="i.todoMA || ''" @blur="patch(i, { todoMA: $event.target.value })" class="cell-input w-40" />
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5 text-center">
              <button @click="patch(i, { freigegebenFuerKontakt: !i.freigegebenFuerKontakt })" :class="['inline-flex items-center justify-center w-6 h-6 rounded text-[10px] font-bold', i.freigegebenFuerKontakt ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-400']">
                <Check v-if="i.freigegebenFuerKontakt" class="w-3 h-3" />
                <span v-else>—</span>
              </button>
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5">
              <input :value="i.kontaktdatenGesendetAm || ''" type="date" @change="patch(i, { kontaktdatenGesendetAm: $event.target.value })" class="cell-input" />
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5">
              <input :value="i.erstesTelefonatAm || ''" type="date" @change="patch(i, { erstesTelefonatAm: $event.target.value })" class="cell-input" />
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5">
              <input :value="i.verkaeuferTerminAm || ''" type="date" @change="patch(i, { verkaeuferTerminAm: $event.target.value })" class="cell-input" />
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5">
              <input :value="i.gebotAngefordertAm || ''" type="date" @change="patch(i, { gebotAngefordertAm: $event.target.value })" class="cell-input" />
            </td>
            <td v-if="!kompakt" class="px-2 py-1.5 text-right">
              <input :value="i.aktuellesGebot || ''" @blur="patch(i, { aktuellesGebot: $event.target.value })" class="cell-input text-right w-24" placeholder="€" />
            </td>
            <td class="px-2 py-1.5 text-center">
              <div class="flex flex-col gap-0.5 items-stretch">
                <button @click="patch(i, { zusage: !i.zusage, absage: false })" :class="['text-[10px] font-bold rounded px-1.5 py-0.5', i.zusage ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-400 hover:bg-green-100']">Zusage</button>
                <button @click="patch(i, { absage: !i.absage, zusage: false })" :class="['text-[10px] font-bold rounded px-1.5 py-0.5', i.absage ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-400 hover:bg-red-100']">Absage</button>
              </div>
            </td>
            <td class="px-2 py-1.5">
              <button @click="openDetail(i)" class="text-gray-400 hover:text-[#0088ba] p-1" title="Detail">
                <ChevronRight class="w-3.5 h-3.5" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detail-Slide-Over -->
    <Teleport to="body">
      <div v-if="detail" class="fixed inset-0 z-50 flex">
        <div class="flex-1 bg-black/40" @click="detail = null"></div>
        <aside class="w-full max-w-xl bg-white shadow-2xl flex flex-col h-full overflow-hidden">
          <header class="px-6 py-4 border-b border-gray-100 flex items-start justify-between">
            <div>
              <h3 class="text-lg font-bold text-gray-900">{{ detail.firma || '—' }}</h3>
              <p class="text-sm text-gray-500">{{ detail.vorname || splitName(detail.name).vorname }} {{ detail.nachname || splitName(detail.name).nachname }} · {{ detail.email }}</p>
            </div>
            <div class="flex items-center gap-1">
              <button @click="loeschen(detail)" class="p-1.5 hover:bg-red-50 rounded-lg text-red-500" title="Interessent löschen">
                <Trash2 class="w-4 h-4" />
              </button>
              <button @click="detail = null" class="p-1.5 hover:bg-gray-100 rounded-lg"><X class="w-5 h-5" /></button>
            </div>
          </header>
          <div class="flex-1 overflow-y-auto p-6 space-y-4 text-sm">
            <div class="grid grid-cols-2 gap-3">
              <div><div class="text-xs text-gray-400 mb-0.5">Telefon</div><div>{{ detail.telefon || '—' }}</div></div>
              <div><div class="text-xs text-gray-400 mb-0.5">Website</div><div><a v-if="detail.website" :href="detail.website" target="_blank" class="text-[#0088ba] hover:underline">{{ detail.website?.replace(/^https?:\/\//, '') }}</a></div></div>
              <div><div class="text-xs text-gray-400 mb-0.5">PLZ + Ort</div><div>{{ [detail.plz, detail.ort].filter(Boolean).join(' ') }}</div></div>
              <div><div class="text-xs text-gray-400 mb-0.5">Eingegangen</div><div>{{ longDate(detail.createdAt) }}</div></div>
            </div>
            <div v-if="detail.kommentar">
              <div class="text-xs text-gray-400 mb-0.5">Mitteilung</div>
              <div class="bg-gray-50 rounded p-3 whitespace-pre-line">{{ detail.kommentar }}</div>
            </div>
            <div v-if="detail.enrichFirmenname || detail.enrichGeschaeftsfuehrer || detail.enrichStrasse" class="border border-emerald-200 bg-emerald-50 rounded-xl p-4">
              <div class="text-xs font-semibold text-emerald-700 uppercase mb-2">Angereicherte Daten (Impressum)</div>
              <dl class="space-y-1 text-xs">
                <div v-if="detail.enrichFirmenname"><dt class="inline text-emerald-700">Firmenname offiziell: </dt><dd class="inline">{{ detail.enrichFirmenname }}</dd></div>
                <div v-if="detail.enrichGeschaeftsfuehrer"><dt class="inline text-emerald-700">Geschäftsführer: </dt><dd class="inline">{{ detail.enrichGeschaeftsfuehrer }}</dd></div>
                <div v-if="detail.enrichStrasse"><dt class="inline text-emerald-700">Adresse: </dt><dd class="inline">{{ detail.enrichStrasse }}, {{ detail.enrichPLZ }} {{ detail.enrichOrt }}</dd></div>
                <div v-if="detail.enrichTelefon"><dt class="inline text-emerald-700">Festnetz: </dt><dd class="inline">{{ detail.enrichTelefon }}</dd></div>
                <div v-if="detail.enrichEmailImpressum"><dt class="inline text-emerald-700">Impressum-E-Mail: </dt><dd class="inline">{{ detail.enrichEmailImpressum }}</dd></div>
                <div v-if="detail.enrichUstId"><dt class="inline text-emerald-700">USt-ID: </dt><dd class="inline">{{ detail.enrichUstId }}</dd></div>
              </dl>
            </div>
            <div v-if="detail.ndaStatus === 'unterzeichnet'" class="border border-green-200 bg-green-50 rounded-xl p-4 text-sm">
              <div class="font-semibold text-green-900">NDA unterzeichnet</div>
              <div class="text-xs text-green-800 mt-1">am {{ longDate(detail.ndaUploadedAt) }} {{ detail.ndaSignedOnline ? '(online)' : '(per Upload)' }}</div>
            </div>

            <!-- Verlauf zu diesem Kontakt -->
            <div class="border border-gray-200 bg-white rounded-xl p-4">
              <div class="flex items-center gap-2 mb-3">
                <MessageSquare class="w-4 h-4 text-[#0088ba]" />
                <div class="font-semibold text-gray-800">Verlauf</div>
                <button @click="showAddReply = !showAddReply" class="ml-auto text-[10px] px-2 py-1 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-1">
                  <Plus class="w-3 h-3" /> Antwort / Notiz eintragen
                </button>
              </div>
              <div v-if="showAddReply" class="mb-3 p-3 bg-amber-50 border border-amber-100 rounded-lg space-y-2">
                <div class="grid grid-cols-3 gap-2">
                  <select v-model="newReplyTyp" class="text-xs px-2 py-1.5 border border-gray-200 rounded-lg col-span-1">
                    <option value="mail_in">Mail-Antwort</option>
                    <option value="anruf">Anruf</option>
                    <option value="notiz">Notiz</option>
                  </select>
                  <input v-model="newReplyBetreff" placeholder="Betreff / kurz" class="text-xs px-2 py-1.5 border border-gray-200 rounded-lg col-span-2" />
                </div>
                <textarea v-model="newReplyText" rows="4" placeholder="Inhalt der Antwort / Notiz (z.B. Mail-Text aus Outlook reinkopieren)…"
                  class="w-full text-xs px-2 py-1.5 border border-gray-200 rounded-lg resize-y"></textarea>
                <div class="flex gap-2 justify-end">
                  <button @click="showAddReply = false; newReplyText = ''; newReplyBetreff = ''" class="text-xs px-3 py-1.5 border border-gray-200 rounded-lg">Abbrechen</button>
                  <button @click="addReply" :disabled="!newReplyText.trim() || addingReply"
                    class="text-xs px-3 py-1.5 bg-[#0088ba] text-white rounded-lg font-medium disabled:opacity-50">
                    {{ addingReply ? 'Speichere…' : 'Eintragen' }}
                  </button>
                </div>
              </div>
              <ul class="space-y-2.5">
                <li v-for="ev in combinedVerlauf" :key="ev.id" class="text-xs">
                  <div class="flex items-center gap-2 mb-0.5">
                    <span :class="['inline-block w-1.5 h-1.5 rounded-full', ev.color || 'bg-gray-300']"></span>
                    <span class="font-semibold text-gray-800">{{ ev.betreff }}</span>
                    <span class="text-gray-400 ml-auto whitespace-nowrap">{{ longDate(ev.datum) }}</span>
                  </div>
                  <div v-if="ev.beschreibung" class="text-gray-600 pl-3.5 whitespace-pre-wrap line-clamp-3">{{ ev.beschreibung }}</div>
                </li>
                <li v-if="!combinedVerlauf.length" class="text-xs text-gray-400 italic">Noch keine Einträge.</li>
              </ul>
            </div>
            <div>
              <label class="text-xs text-gray-500 block mb-1">VETO-Begründung (wenn Veto gesetzt)</label>
              <textarea :value="detail.vetoBegruendung || ''" @blur="patch(detail, { vetoBegruendung: $event.target.value })" rows="2" class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30"></textarea>
            </div>

            <!-- Drip-Sequenz Steuerung -->
            <div class="border border-purple-100 bg-purple-50/40 rounded-xl p-4">
              <div class="flex items-center gap-2 mb-3">
                <Send class="w-4 h-4 text-purple-600" />
                <div class="font-semibold text-gray-800">Auto-Mail-Sequenz (Drip)</div>
              </div>
              <div v-if="detail.dripSequenzId && !detail.dripPausiert" class="text-xs space-y-1 mb-3">
                <div>Aktiv: <strong>{{ activeDripName(detail.dripSequenzId) }}</strong></div>
                <div>Gestartet: {{ longDate(detail.dripGestartetAm) }}</div>
                <div>Nächster Schritt: {{ (detail.dripNaechsterSchritt || 0) + 1 }} von {{ activeDripSchritte(detail.dripSequenzId).length }}</div>
                <div v-if="detail.dripLetzterVersandAm">Letzter Versand: {{ longDate(detail.dripLetzterVersandAm) }}</div>
              </div>
              <div v-else-if="detail.dripSequenzId && detail.dripPausiert" class="text-xs mb-3 text-amber-700">
                ⏸ Pausiert — <strong>{{ activeDripName(detail.dripSequenzId) }}</strong>
              </div>
              <div v-else class="text-xs text-gray-500 mb-3">Noch keine Sequenz gestartet</div>

              <div class="flex gap-2 flex-wrap">
                <select v-if="!detail.dripSequenzId" v-model="selectedSeqId" class="text-xs border border-gray-200 rounded-lg px-2 py-1.5 flex-1">
                  <option value="">— Sequenz wählen —</option>
                  <option v-for="s in dripSequenzen" :key="s.RowKey" :value="s.RowKey">{{ s.name }}</option>
                </select>
                <button v-if="!detail.dripSequenzId" @click="dripStart(detail)" :disabled="!selectedSeqId"
                  class="text-xs px-3 py-1.5 bg-purple-600 text-white rounded-lg font-medium disabled:opacity-50">Starten</button>
                <button v-if="detail.dripSequenzId && !detail.dripPausiert" @click="dripAction(detail, 'pause')"
                  class="text-xs px-3 py-1.5 border border-amber-300 text-amber-700 rounded-lg">Pausieren</button>
                <button v-if="detail.dripSequenzId && detail.dripPausiert" @click="dripAction(detail, 'resume')"
                  class="text-xs px-3 py-1.5 border border-green-300 text-green-700 rounded-lg">Fortsetzen</button>
                <button v-if="detail.dripSequenzId" @click="dripAction(detail, 'stop')"
                  class="text-xs px-3 py-1.5 border border-red-300 text-red-700 rounded-lg">Stoppen</button>
              </div>
              <p class="text-[10px] text-gray-400 mt-2">Mails gehen täglich um 08:00 UTC raus (passend zum konfigurierten Tag-Offset)</p>
            </div>
          </div>
        </aside>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Users, Check, ChevronRight, X, Download, Maximize2, Minimize2, Send, Trash2, FileText, ShieldCheck, MailCheck, MessageSquare, Plus } from '@lucide/vue'
import { authFetch, getDripSequenzen, startDrip, pauseDrip, deleteInteressent, getKontakte } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const props = defineProps({ targetId: String })

const items = ref([])
const loading = ref(true)
const kompakt = ref(true)
const detail = ref(null)

async function load() {
  if (!props.targetId) { loading.value = false; return }
  try {
    items.value = await authFetch('/interessenten', { method: 'POST', data: { targetId: props.targetId } })
  } catch (e) { toast.error('Laden fehlgeschlagen') }
  finally { loading.value = false }
}
// ============= Drip-Sequenzen =============
const dripSequenzen = ref([])
const selectedSeqId = ref('')

async function loadDrip() {
  try { dripSequenzen.value = await getDripSequenzen() } catch {}
}

function activeDripName(sid) {
  return dripSequenzen.value.find(s => s.RowKey === sid)?.name || '?'
}
function activeDripSchritte(sid) {
  return dripSequenzen.value.find(s => s.RowKey === sid)?.schritte || []
}

async function dripStart(i) {
  if (!selectedSeqId.value) return
  try {
    await startDrip(i.RowKey, selectedSeqId.value)
    Object.assign(i, {
      dripSequenzId: selectedSeqId.value,
      dripGestartetAm: new Date().toISOString(),
      dripNaechsterSchritt: 0,
      dripPausiert: false,
    })
    selectedSeqId.value = ''
    toast.success('Drip-Sequenz gestartet')
  } catch (e) { toast.error('Start fehlgeschlagen') }
}

async function dripAction(i, action) {
  try {
    await pauseDrip(i.RowKey, action)
    if (action === 'pause') i.dripPausiert = true
    if (action === 'resume') i.dripPausiert = false
    if (action === 'stop') i.dripSequenzId = ''
    toast.success(action === 'pause' ? 'Pausiert' : action === 'resume' ? 'Fortgesetzt' : 'Gestoppt')
  } catch (e) { toast.error('Aktion fehlgeschlagen') }
}

onMounted(() => { load(); loadDrip() })

const sorted = computed(() => [...items.value].sort((a, b) => (b.createdAt || '').localeCompare(a.createdAt || '')))

async function patch(i, updates) {
  Object.assign(i, updates)
  try {
    await authFetch('/interessent-update', { method: 'POST', data: { id: i.RowKey, ...updates } })
  } catch (e) { toast.error('Speichern fehlgeschlagen') }
}

async function openDetail(i) {
  detail.value = i
  // Kontakt-Verlauf laden (kontakte.verlaufJson dieses Empfaengers)
  kontaktVerlauf.value = []
  try {
    const alle = await getKontakte()
    const mailLc = (i.email || '').toLowerCase()
    const k = (alle || []).find(x => (x.email || '').toLowerCase() === mailLc)
    if (k && k.verlaufJson) {
      try { kontaktVerlauf.value = JSON.parse(k.verlaufJson) || [] } catch {}
    }
  } catch {}
}

const kontaktVerlauf = ref([])

// Kombinierter Verlauf: Synthese aus Interessenten-Record (Stammereignisse) + Kontakt-Verlauf
const combinedVerlauf = computed(() => {
  const out = []
  const i = detail.value
  if (!i) return []
  // Stammereignisse aus dem Interessenten-Record
  if (i.createdAt) {
    out.push({
      id: 'evt-anmeldung',
      betreff: 'Exposé angefragt (Landing-Page)',
      beschreibung: `Über Landing-Page eingetragen. E-Mail: ${i.email || '—'}${i.kommentar ? '\n\nMitteilung: ' + i.kommentar : ''}`,
      datum: i.createdAt,
      color: 'bg-blue-500',
    })
  }
  if (i.ndaUploadedAt) {
    out.push({
      id: 'evt-nda',
      betreff: i.ndaSignedOnline ? 'NDA online signiert' : 'NDA hochgeladen',
      beschreibung: `Vertraulichkeitsvereinbarung gegengezeichnet${i.ndaSigIp ? ' (IP: ' + i.ndaSigIp + ')' : ''}.`,
      datum: i.ndaUploadedAt,
      color: 'bg-green-500',
    })
  }
  if (i.kontaktdatenGesendetAm) {
    out.push({
      id: 'evt-kontakt-gesendet',
      betreff: 'Kontaktdaten an Verkäufer freigegeben',
      beschreibung: '',
      datum: i.kontaktdatenGesendetAm,
      color: 'bg-amber-500',
    })
  }
  if (i.erstesTelefonatAm) {
    out.push({
      id: 'evt-tel',
      betreff: 'Erstes Telefonat',
      beschreibung: '',
      datum: i.erstesTelefonatAm,
      color: 'bg-purple-500',
    })
  }
  if (i.verkaeuferTerminAm) {
    out.push({
      id: 'evt-termin',
      betreff: 'Termin mit Verkäufer',
      beschreibung: '',
      datum: i.verkaeuferTerminAm,
      color: 'bg-purple-500',
    })
  }
  if (i.gebotAngefordertAm) {
    out.push({
      id: 'evt-gebot',
      betreff: 'Gebot angefordert',
      beschreibung: i.aktuellesGebot ? `Gebot: ${i.aktuellesGebot}` : '',
      datum: i.gebotAngefordertAm,
      color: 'bg-amber-600',
    })
  }
  // Eintraege aus dem Kontakt-Verlauf (Mass-Mails, manuelle Antworten etc.)
  for (const ev of kontaktVerlauf.value || []) {
    out.push({
      id: ev.id || 'k-' + Math.random().toString(36).slice(2),
      betreff: ev.betreff || ev.typ || 'Eintrag',
      beschreibung: ev.beschreibung || '',
      datum: ev.datum,
      color: ev.typ === 'mail_out' ? 'bg-blue-400' : ev.typ === 'mail_in' ? 'bg-orange-500' : 'bg-gray-400',
    })
  }
  // Sortieren neueste zuerst
  return out.sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
})

// Manuelle Antwort/Notiz an Kontakt-Verlauf anhaengen
const showAddReply = ref(false)
const newReplyTyp = ref('mail_in')
const newReplyBetreff = ref('')
const newReplyText = ref('')
const addingReply = ref(false)
async function addReply() {
  if (!detail.value || !newReplyText.value.trim()) return
  addingReply.value = true
  try {
    const r = await authFetch('/kontakt-verlauf-add', { method: 'POST', data: {
      email: detail.value.email,
      eintrag: {
        typ: newReplyTyp.value,
        betreff: newReplyBetreff.value.trim() || (newReplyTyp.value === 'mail_in' ? 'Antwort eingegangen' : 'Notiz'),
        beschreibung: newReplyText.value.trim(),
      },
    }})
    if (r?.entry) kontaktVerlauf.value.push(r.entry)
    showAddReply.value = false
    newReplyText.value = ''; newReplyBetreff.value = ''
    toast.success('Eintrag gespeichert')
  } catch (e) {
    toast.error('Speichern fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally { addingReply.value = false }
}

async function loeschen(i) {
  if (!confirm(`Interessent „${i.firma || i.name || i.email}" wirklich löschen? Das kann nicht rückgängig gemacht werden.`)) return
  try {
    await deleteInteressent(i.RowKey)
    items.value = items.value.filter(x => x.RowKey !== i.RowKey)
    detail.value = null
    toast.success('Interessent gelöscht')
  } catch (e) {
    toast.error('Löschen fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  }
}

function splitName(name) {
  if (!name) return { vorname: '', nachname: '' }
  const parts = name.trim().split(/\s+/)
  return { vorname: parts[0] || '', nachname: parts.slice(1).join(' ') }
}
function shortDate(iso) { if (!iso) return ''; try { return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' }) } catch { return '' } }
function longDate(iso) { if (!iso) return ''; try { return new Date(iso).toLocaleDateString('de-DE') } catch { return '' } }

function exportCsv() {
  const cols = ['createdAt','firma','vorname','nachname','email','telefon','website','plz','ort','kommentar','ndaStatus','rating','ansprache','veto','vetoBegruendung','notiz','bemerkungenMibeca','todoMA','freigegebenFuerKontakt','kontaktdatenGesendetAm','erstesTelefonatAm','verkaeuferTerminAm','gebotAngefordertAm','absage','zusage','aktuellesGebot']
  const labels = { createdAt: 'Datum', firma: 'Firma', vorname: 'Vorname', nachname: 'Nachname', email: 'E-Mail', telefon: 'Telefon', website: 'Website', plz: 'PLZ', ort: 'Ort', kommentar: 'Mitteilung', ndaStatus: 'NDA', rating: 'Rating', ansprache: 'Ansprache', veto: 'VETO', vetoBegruendung: 'VETO-Begründung', notiz: 'Notizen', bemerkungenMibeca: 'Bemerkungen MB/JK', todoMA: 'TODO M&A', freigegebenFuerKontakt: 'Freigabe Verkäufer', kontaktdatenGesendetAm: 'Kontakt gesendet', erstesTelefonatAm: 'Erst-Telefonat', verkaeuferTerminAm: 'Verkäufer-Termin', gebotAngefordertAm: 'Gebot angefordert', absage: 'Absage', zusage: 'Zusage', aktuellesGebot: 'Aktuelles Gebot' }
  const csv = [cols.map(c => '"' + labels[c] + '"').join(';'), ...sorted.value.map(i => cols.map(c => '"' + String(i[c] ?? '').replace(/"/g, '""') + '"').join(';'))].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `Interessenten_${props.targetId}.csv`
  a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>

<style scoped>
@reference "tailwindcss";
.cell-input { @apply text-xs px-1 py-0.5 border border-transparent hover:border-gray-200 focus:border-[#0088ba] rounded bg-transparent focus:bg-white focus:outline-none; }
</style>
