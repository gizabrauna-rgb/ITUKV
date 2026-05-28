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

  <ToastHost />
</template>

<script setup>
import { ref, computed } from 'vue'
import { Eye, X } from '@lucide/vue'
import Login from './views/Login.vue'
import AdminDashboard from './views/AdminDashboard.vue'
import TargetDashboard from './views/TargetDashboard.vue'
import SignPage from './SignPage.vue'
import LandingPage from './LandingPage.vue'
import ExposeBuyerPage from './ExposeBuyerPage.vue'
import PasswordReset from './views/PasswordReset.vue'
import ToastHost from './components/ToastHost.vue'
import { msalInstance } from './authConfig.js'

// Oeffentliche Routen ohne Login
const isSignRoute = /^\/sign\/[^/?#]+/.test(window.location.pathname)
const isLandingRoute = /^\/mb-[^/?#]+/i.test(window.location.pathname)
const isExposeBuyerRoute = /^\/expose-[^/]+\/[^/?#]+/i.test(window.location.pathname)
const isResetRoute = /^\/reset(\/|$|\?)/.test(window.location.pathname)

const role = ref(sessionStorage.getItem('userRole') || '')
const userName = ref(sessionStorage.getItem('userName') || '')
const impersonating = ref(sessionStorage.getItem('impersonateAs') || '')

// Projekttypen, die Verkäufer/Target-Seite sehen
const TARGET_TYPS = ['UVE Target', 'Projekt Target', 'MC Target']
// Investoren-Projekttypen sind semantisch Kauf-Mandate -> auch TargetDashboard
// (mit dem kauf-mandat-Tab-Set: Suchprofil, Target-Vorschlaege, Vertraege)
const KAUF_MANDAT_TYPS = ['Projekt Investoren', 'MC Investoren', 'Kauf-Mandat']
const INVESTOR_TYPS = []  // Legacy: leer (alte Liste bleibt fuer Abwaertskompatibilitaet)

const currentView = computed(() => {
  if (isResetRoute) return PasswordReset
  if (isSignRoute) return SignPage
  if (isExposeBuyerRoute) return ExposeBuyerPage
  if (isLandingRoute) return LandingPage
  if (!role.value) return Login
  // Admin testet eine bestimmte Projekttyp-Ansicht
  if (role.value === 'admin' && TARGET_TYPS.includes(impersonating.value)) return TargetDashboard
  if (role.value === 'admin' && KAUF_MANDAT_TYPS.includes(impersonating.value)) return TargetDashboard
  if (role.value === 'admin') return AdminDashboard
  if (role.value === 'target') return TargetDashboard
  // Käufer/Investoren bekommen ebenfalls TargetDashboard - dort wird
  // automatisch der Kauf-Mandat-Tab-Set angezeigt (Suchprofil, Vorschlaege, etc.)
  if (role.value === 'investor') return TargetDashboard
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
