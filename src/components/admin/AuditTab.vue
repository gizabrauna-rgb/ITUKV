<template>
  <div>
    <div class="mb-6">
      <h2 class="text-xl font-bold text-gray-900">Audit-Log &amp; Backups</h2>
      <p class="text-sm text-gray-500 mt-1">Wer hat was geändert · Sicherungen der Datenbank</p>
    </div>

    <!-- Backups -->
    <section class="bg-white rounded-xl border border-gray-100 p-5 mb-5">
      <div class="flex items-start justify-between mb-3">
        <div>
          <h3 class="font-semibold text-gray-800 text-sm flex items-center gap-2">
            <ShieldCheck class="w-4 h-4 text-[#0088ba]" /> Backups
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">Automatischer Wochen-Snapshot jeden Sonntag 03:00 UTC. 12 Wochen werden vorgehalten.</p>
        </div>
        <button @click="doTrigger" :disabled="triggering"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-[#0088ba] text-white rounded-lg text-xs font-medium hover:bg-[#00a0d8] disabled:opacity-50">
          <RefreshCw :class="['w-3.5 h-3.5', triggering ? 'animate-spin' : '']" />
          {{ triggering ? 'Sichere…' : 'Jetzt sichern' }}
        </button>
      </div>
      <div v-if="loadingBackups" class="text-xs text-gray-400 py-3 text-center">Lade…</div>
      <div v-else-if="!backups.length" class="text-xs text-gray-400 py-3 text-center">Noch keine Sicherungen vorhanden. Klick „Jetzt sichern".</div>
      <table v-else class="w-full text-xs">
        <thead class="border-b border-gray-100 text-left text-[11px] uppercase tracking-wide text-gray-400">
          <tr><th class="py-2 pr-3">Name</th><th class="py-2 pr-3">Erstellt</th><th class="py-2 pr-3 text-right">Größe</th><th class="py-2"></th></tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="b in backups" :key="b.name">
            <td class="py-2 pr-3 font-mono">{{ b.name }}</td>
            <td class="py-2 pr-3 text-gray-600">{{ formatDate(b.createdAt) }}</td>
            <td class="py-2 pr-3 text-right text-gray-600">{{ b.sizeKb }} KB</td>
            <td class="py-2 text-right">
              <a :href="b.downloadUrl" :download="b.name" target="_blank" class="text-[#0088ba] hover:underline inline-flex items-center gap-1">
                <Download class="w-3 h-3" /> Download
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Audit Log -->
    <section class="bg-white rounded-xl border border-gray-100 p-5">
      <div class="flex items-start justify-between mb-3">
        <div>
          <h3 class="font-semibold text-gray-800 text-sm flex items-center gap-2">
            <FileText class="w-4 h-4 text-[#0088ba]" /> Audit-Log
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">Letzte {{ items.length }} Aktionen. Schreibvorgänge an Mandaten, Kontakten, Usern werden hier protokolliert.</p>
        </div>
        <button @click="loadAudit" class="px-3 py-1.5 border border-gray-200 rounded-lg text-xs hover:bg-gray-50">
          <RefreshCw class="w-3.5 h-3.5 inline -mt-0.5" /> Aktualisieren
        </button>
      </div>
      <div v-if="loadingAudit" class="text-xs text-gray-400 py-3 text-center">Lade…</div>
      <div v-else-if="!items.length" class="text-xs text-gray-400 py-6 text-center">Noch keine Audit-Einträge.</div>
      <table v-else class="w-full text-xs">
        <thead class="border-b border-gray-100 text-left text-[11px] uppercase tracking-wide text-gray-400">
          <tr>
            <th class="py-2 pr-3">Zeit</th>
            <th class="py-2 pr-3">User</th>
            <th class="py-2 pr-3">Aktion</th>
            <th class="py-2 pr-3">Objekt</th>
            <th class="py-2">Details</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="e in items" :key="e.RowKey" class="hover:bg-gray-50">
            <td class="py-2 pr-3 text-gray-600 whitespace-nowrap">{{ formatDate(e.ts) }}</td>
            <td class="py-2 pr-3">
              <span class="font-medium">{{ e.userName || '?' }}</span>
              <span class="text-gray-400 ml-1 text-[10px]">{{ e.userRole }}</span>
            </td>
            <td class="py-2 pr-3">
              <span :class="actionClass(e.action)" class="text-[10px] px-1.5 py-0.5 rounded font-medium uppercase">{{ e.action }}</span>
            </td>
            <td class="py-2 pr-3">
              <span class="font-mono text-[10px] bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded">{{ e.targetType }}</span>
              <span v-if="e.targetId" class="text-gray-400 text-[10px] ml-1">{{ e.targetId.slice(0, 8) }}</span>
            </td>
            <td class="py-2 text-gray-500">
              <code v-if="e.details" class="text-[10px] truncate block max-w-md">{{ e.details }}</code>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ShieldCheck, FileText, RefreshCw, Download } from '@lucide/vue'
import { getAuditLog, listBackups, triggerBackup } from '../../api.js'
import { toast } from '../../composables/useToast.js'

const items = ref([])
const backups = ref([])
const loadingAudit = ref(false)
const loadingBackups = ref(false)
const triggering = ref(false)

function actionClass(a) {
  if (a === 'create') return 'bg-green-100 text-green-700'
  if (a === 'update') return 'bg-blue-100 text-blue-700'
  if (a === 'delete') return 'bg-red-100 text-red-700'
  if (a === 'ai_update') return 'bg-purple-100 text-purple-700'
  if (a === 'backup_manual') return 'bg-amber-100 text-amber-700'
  return 'bg-gray-100 text-gray-600'
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadAudit() {
  loadingAudit.value = true
  try {
    const r = await getAuditLog({ limit: 200 })
    items.value = r.items || []
  } catch (e) { toast.error('Audit-Log nicht abrufbar') }
  finally { loadingAudit.value = false }
}

async function loadBackupsList() {
  loadingBackups.value = true
  try {
    const r = await listBackups()
    backups.value = r.backups || []
  } catch (e) { /* leiser fail */ }
  finally { loadingBackups.value = false }
}

async function doTrigger() {
  triggering.value = true
  try {
    await triggerBackup()
    toast.success('Backup gestartet — taucht in wenigen Sekunden in der Liste auf')
    setTimeout(loadBackupsList, 3000)
  } catch (e) {
    toast.error('Backup fehlgeschlagen')
  } finally { triggering.value = false }
}

onMounted(() => {
  loadAudit()
  loadBackupsList()
})
</script>
