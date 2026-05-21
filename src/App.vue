<template>
  <!-- Impersonation Banner (nur als Admin sichtbar wenn aktiv) -->
  <div v-if="impersonating" class="bg-[#c8b274] text-[#161e2a] px-6 py-2 flex items-center justify-between text-sm font-medium">
    <div class="flex items-center gap-2">
      <Eye class="w-4 h-4" />
      <span>Du siehst gerade die <strong>{{ impersonating }}</strong>-Ansicht als Admin</span>
    </div>
    <button @click="stopImpersonation" class="flex items-center gap-1.5 px-3 py-1 bg-[#161e2a] text-white rounded-lg text-xs hover:bg-black">
      <X class="w-3.5 h-3.5" />
      Zurück zum Admin-Bereich
    </button>
  </div>

  <component
    :is="currentView"
    :user-name="userName"
    :projekttyp="impersonating || ''"
    :impersonating="!!impersonating"
    @logged-in="onLoggedIn"
    @logout="onLogout"
    @switch-view="switchView"
  />
</template>

<script setup>
import { ref, computed } from 'vue'
import { Eye, X } from '@lucide/vue'
import Login from './views/Login.vue'
import AdminDashboard from './views/AdminDashboard.vue'
import TargetDashboard from './views/TargetDashboard.vue'
import InvestorDashboard from './views/InvestorDashboard.vue'
import { msalInstance } from './authConfig.js'

const role = ref(sessionStorage.getItem('userRole') || '')
const userName = ref(sessionStorage.getItem('userName') || '')
const impersonating = ref(sessionStorage.getItem('impersonateAs') || '')

// Projekttypen, die Verkäufer/Target-Seite sehen
const TARGET_TYPS = ['UVE Target', 'Projekt Target', 'MC Target']
const INVESTOR_TYPS = ['Projekt Investoren', 'MC Investoren']

const currentView = computed(() => {
  if (!role.value) return Login
  // Admin testet eine bestimmte Projekttyp-Ansicht
  if (role.value === 'admin' && TARGET_TYPS.includes(impersonating.value)) return TargetDashboard
  if (role.value === 'admin' && INVESTOR_TYPS.includes(impersonating.value)) return InvestorDashboard
  if (role.value === 'admin') return AdminDashboard
  if (role.value === 'target') return TargetDashboard
  if (role.value === 'investor') return InvestorDashboard
  return Login
})

function onLoggedIn(user) {
  role.value = user.role
  userName.value = user.name
}

async function onLogout() {
  sessionStorage.clear()
  localStorage.clear()
  role.value = ''
  userName.value = ''
  impersonating.value = ''
  // Auch Microsoft-Session beenden, sonst loggt sich der User automatisch wieder ein
  try {
    const account = msalInstance.getActiveAccount() || msalInstance.getAllAccounts()[0]
    if (account) {
      await msalInstance.logoutRedirect({ account, postLogoutRedirectUri: window.location.origin })
      return
    }
  } catch (e) { console.error('logout', e) }
  window.location.reload()
}

function switchView(viewType) {
  // viewType: 'admin' | 'UVE Target' | 'Projekt Target' | 'MC Target' | 'Projekt Investoren' | 'MC Investoren'
  if (viewType === 'admin' || !viewType) {
    sessionStorage.removeItem('impersonateAs')
    impersonating.value = ''
  } else {
    sessionStorage.setItem('impersonateAs', viewType)
    impersonating.value = viewType
  }
}

function stopImpersonation() {
  switchView('admin')
}
</script>
