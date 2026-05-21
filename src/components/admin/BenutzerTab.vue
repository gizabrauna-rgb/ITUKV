<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Benutzer-Verwaltung</h2>
      <button @click="openNew" class="flex items-center gap-2 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium hover:bg-[#0a9aaf]">
        <UserPlus class="w-4 h-4" /> Neuer Benutzer
      </button>
    </div>

    <!-- Filter -->
    <div class="flex gap-2 mb-4">
      <button v-for="r in roleFilters" :key="r.value" @click="filterRole = r.value"
        :class="['px-3 py-1.5 rounded-lg text-sm font-medium', filterRole === r.value ? 'bg-[#097e92] text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50']">
        {{ r.label }} <span class="opacity-60 ml-1">({{ countRole(r.value) }})</span>
      </button>
    </div>

    <!-- Tabelle -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-400 text-sm">Lade Benutzer…</div>
      <div v-else-if="!filtered.length" class="p-8 text-center text-gray-400 text-sm">Keine Benutzer gefunden.</div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Name / E-Mail</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Rolle</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Zuordnung</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Login via</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Angelegt</th>
            <th class="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Aktionen</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="u in filtered" :key="u.RowKey" class="hover:bg-gray-50">
            <td class="px-4 py-3">
              <div class="font-medium text-sm text-gray-800">{{ u.name || '—' }}</div>
              <div class="text-xs text-gray-400">{{ u.email }}</div>
            </td>
            <td class="px-4 py-3">
              <span :class="roleClass(u.role)" class="text-xs font-medium px-2 py-0.5 rounded-full">{{ roleLabel(u.role) }}</span>
            </td>
            <td class="px-4 py-3 text-sm">
              <span v-if="u.role === 'target' && u.targetId" class="font-mono text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                {{ targetMbNrById(u.targetId) || u.targetId.slice(0,8) }}
              </span>
              <span v-else class="text-gray-400 text-xs">—</span>
            </td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ u.loginVia || 'password' }}</td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ formatDate(u.createdAt) }}</td>
            <td class="px-4 py-3 text-right">
              <div class="flex justify-end gap-1">
                <button @click="openEdit(u)" class="p-1.5 hover:bg-gray-100 rounded text-gray-500" title="Bearbeiten">
                  <Pencil class="w-3.5 h-3.5" />
                </button>
                <button @click="resetPwd(u)" class="p-1.5 hover:bg-gray-100 rounded text-gray-500" title="Passwort zurücksetzen">
                  <KeyRound class="w-3.5 h-3.5" />
                </button>
                <button @click="deleteIt(u)" class="p-1.5 hover:bg-red-50 rounded text-red-500" title="Löschen">
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal: Neu / Bearbeiten -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-lg">
        <div class="flex items-center justify-between mb-5">
          <h3 class="font-bold text-gray-900">{{ editing ? 'Benutzer bearbeiten' : 'Neuer Benutzer' }}</h3>
          <button @click="closeModal"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Name</label>
              <input v-model="form.name" placeholder="Vorname Nachname" class="input" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">E-Mail *</label>
              <input v-model="form.email" type="email" :disabled="editing" placeholder="user@example.de" class="input" />
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Rolle *</label>
            <select v-model="form.role" class="input">
              <option value="admin">Admin (mibeca-Team) – voller Zugriff</option>
              <option value="target">Target (Verkäufer) – nur eigenes Projekt</option>
              <option value="investor">Investor (Käufer) – Ausschreibungen + eigene NDAs</option>
            </select>
          </div>
          <div v-if="form.role === 'target'">
            <label class="block text-xs font-medium text-gray-600 mb-1">Verknüpftes Target (mb-Nummer)</label>
            <select v-model="form.targetId" class="input">
              <option value="">— Target auswählen —</option>
              <option v-for="t in targets" :key="t.RowKey" :value="t.RowKey">{{ t.mbNr }} · {{ t.verkaueferName }}</option>
            </select>
          </div>
          <div v-if="!editing">
            <label class="block text-xs font-medium text-gray-600 mb-1">Initial-Passwort (leer = automatisch generieren)</label>
            <input v-model="form.password" type="text" placeholder="leer lassen für Zufallspasswort" class="input" />
          </div>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="closeModal" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl hover:bg-gray-50">Abbrechen</button>
          <button @click="save" :disabled="saving || !form.email" class="flex-1 px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium disabled:opacity-50">
            {{ saving ? 'Speichern…' : 'Speichern' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Passwort-Anzeige Modal -->
    <div v-if="passwordReveal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <div class="text-center mb-4">
          <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <KeyRound class="w-6 h-6 text-green-600" />
          </div>
          <h3 class="font-bold text-gray-900">{{ passwordReveal.title }}</h3>
          <p class="text-sm text-gray-500 mt-1">Bitte gib es dem Benutzer weiter. Aus Sicherheitsgründen wird es nur einmal angezeigt.</p>
        </div>
        <div class="bg-gray-50 border border-gray-200 rounded-xl p-3 mb-3">
          <div class="text-xs text-gray-400 mb-1">E-Mail</div>
          <div class="font-mono text-sm text-gray-800">{{ passwordReveal.email }}</div>
        </div>
        <div class="bg-gray-50 border border-gray-200 rounded-xl p-3 mb-4 flex items-center justify-between">
          <div>
            <div class="text-xs text-gray-400 mb-1">Passwort</div>
            <div class="font-mono text-sm text-gray-800">{{ passwordReveal.password }}</div>
          </div>
          <button @click="copyPassword" class="px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-white text-xs flex items-center gap-1">
            <Check v-if="copied" class="w-3 h-3 text-green-500" />
            <Copy v-else class="w-3 h-3" /> Kopieren
          </button>
        </div>
        <button @click="passwordReveal = null" class="w-full px-4 py-2 bg-[#097e92] text-white rounded-xl text-sm font-medium">Verstanden</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { UserPlus, X, Pencil, Trash2, KeyRound, Copy, Check } from '@lucide/vue'
import { getUsers, createUser, updateUser, deleteUser, resetUserPassword, getTargets } from '../../api.js'

const users = ref([])
const targets = ref([])
const loading = ref(true)
const showModal = ref(false)
const editing = ref(null)
const saving = ref(false)
const filterRole = ref('')
const passwordReveal = ref(null)
const copied = ref(false)

const form = ref({ name: '', email: '', role: 'target', targetId: '', password: '' })

const roleFilters = [
  { value: '', label: 'Alle' },
  { value: 'admin', label: 'Admin' },
  { value: 'target', label: 'Verkäufer' },
  { value: 'investor', label: 'Investoren' },
]

const filtered = computed(() => filterRole.value ? users.value.filter(u => u.role === filterRole.value) : users.value)

function countRole(role) {
  return role ? users.value.filter(u => u.role === role).length : users.value.length
}

function roleClass(r) {
  if (r === 'admin') return 'bg-[#097e92]/10 text-[#097e92]'
  if (r === 'target') return 'bg-blue-100 text-blue-700'
  return 'bg-purple-100 text-purple-700'
}
function roleLabel(r) {
  return { admin: 'Admin', target: 'Verkäufer', investor: 'Investor' }[r] || r
}

function targetMbNrById(id) {
  const t = targets.value.find(t => t.RowKey === id)
  return t?.mbNr || ''
}

function formatDate(iso) {
  return iso ? new Date(iso).toLocaleDateString('de-DE') : ''
}

onMounted(async () => {
  try {
    [users.value, targets.value] = await Promise.all([getUsers(), getTargets()])
  } finally { loading.value = false }
})

function openNew() {
  editing.value = null
  form.value = { name: '', email: '', role: 'target', targetId: '', password: '' }
  showModal.value = true
}

function openEdit(u) {
  editing.value = u
  form.value = { name: u.name || '', email: u.email, role: u.role, targetId: u.targetId || '', password: '' }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editing.value = null
}

async function save() {
  saving.value = true
  try {
    if (editing.value) {
      const updated = await updateUser(editing.value.RowKey, {
        name: form.value.name,
        role: form.value.role,
        targetId: form.value.targetId,
      })
      const idx = users.value.findIndex(u => u.RowKey === updated.RowKey)
      if (idx >= 0) users.value[idx] = updated
      closeModal()
    } else {
      const created = await createUser(form.value)
      users.value.unshift(created)
      closeModal()
      // Wenn ein Initial-Passwort generiert wurde, zeigen
      if (created.initialPassword) {
        passwordReveal.value = { title: 'Benutzer angelegt – Initial-Passwort', email: created.email, password: created.initialPassword }
      }
    }
  } catch (e) {
    alert('Fehler: ' + (e.response?.data?.error || e.message))
  } finally { saving.value = false }
}

async function resetPwd(u) {
  if (!confirm(`Passwort für ${u.email} zurücksetzen?`)) return
  try {
    const result = await resetUserPassword(u.RowKey)
    passwordReveal.value = { title: 'Neues Passwort generiert', email: result.email, password: result.newPassword }
  } catch (e) {
    alert('Fehler: ' + e.message)
  }
}

async function deleteIt(u) {
  if (!confirm(`Benutzer ${u.email} wirklich löschen?`)) return
  await deleteUser(u.RowKey)
  users.value = users.value.filter(x => x.RowKey !== u.RowKey)
}

async function copyPassword() {
  try {
    await navigator.clipboard.writeText(passwordReveal.value.password)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {}
}
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92] disabled:bg-gray-50 disabled:text-gray-400; }
</style>
