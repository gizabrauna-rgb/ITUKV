<template>
  <div class="min-h-screen bg-[#161e2a] flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <!-- Logo / Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-white rounded-2xl mb-4 shadow-lg p-3">
          <img src="/favicon.svg" alt="ITUKV" class="w-full h-full" />
        </div>
        <h1 class="text-2xl font-bold text-white">ITUKV Dashboard</h1>
        <p class="text-gray-400 text-sm mt-1">IT-Unternehmen kaufen &amp; verkaufen · mibeca GmbH</p>
      </div>

      <!-- Login Card -->
      <div class="bg-white rounded-2xl shadow-xl p-8">

        <!-- Fehler -->
        <div v-if="error" class="mb-5 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center gap-2">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          {{ error }}
        </div>

        <!-- Microsoft Login -->
        <button
          @click="loginMicrosoft"
          :disabled="loading"
          class="w-full flex items-center justify-center gap-3 px-4 py-3.5 bg-[#097e92] text-white rounded-xl font-semibold hover:bg-[#0a9aaf] transition-colors disabled:opacity-50 mb-2"
        >
          <component :is="loading && loginType === 'microsoft' ? Loader2 : MicrosoftIcon" class="w-5 h-5" :class="loading && loginType === 'microsoft' ? 'animate-spin' : ''" />
          Mit Microsoft anmelden
        </button>
        <p class="text-xs text-gray-400 text-center mb-6">Für mibeca-Team und Kunden mit Microsoft-Konto</p>

        <div class="relative my-5">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-100"></div>
          </div>
          <div class="relative flex justify-center">
            <span class="text-xs text-gray-400 bg-white px-3">oder mit E-Mail &amp; Passwort</span>
          </div>
        </div>

        <!-- E-Mail / Passwort -->
        <form @submit.prevent="loginKunde" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">E-Mail-Adresse</label>
            <input
              v-model="email"
              type="email"
              required
              placeholder="ihre@email.de"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Passwort</label>
            <input
              v-model="password"
              type="password"
              required
              placeholder="••••••••"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#097e92]/30 focus:border-[#097e92]"
            />
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#161e2a] text-white rounded-xl font-medium hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            <Loader2 v-if="loading && loginType === 'customer'" class="w-4 h-4 animate-spin" />
            <LogIn v-else class="w-4 h-4" />
            {{ loading && loginType === 'customer' ? 'Anmelden…' : 'Anmelden' }}
          </button>
        </form>
      </div>

      <p class="text-center text-xs text-gray-500 mt-6">
        mibeca GmbH · M&A Beratung für IT-Unternehmen
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, defineComponent, h } from 'vue'
import { Building2, LogIn, AlertCircle, Loader2 } from '@lucide/vue'
import { msalInstance, loginRequest } from '../authConfig.js'
import { loginCustomer } from '../api.js'

const emit = defineEmits(['logged-in'])

// Microsoft-Icon als einfache SVG-Komponente
const MicrosoftIcon = defineComponent({
  render() {
    return h('svg', { viewBox: '0 0 21 21', width: 20, height: 20, fill: 'currentColor' }, [
      h('rect', { x: 1, y: 1, width: 9, height: 9, fill: '#f25022' }),
      h('rect', { x: 11, y: 1, width: 9, height: 9, fill: '#7fba00' }),
      h('rect', { x: 1, y: 11, width: 9, height: 9, fill: '#00a4ef' }),
      h('rect', { x: 11, y: 11, width: 9, height: 9, fill: '#ffb900' }),
    ])
  }
})

const email = ref('')
const password = ref('')
const loading = ref(false)
const loginType = ref('')
const error = ref('')

async function loginMicrosoft() {
  loading.value = true
  loginType.value = 'microsoft'
  error.value = ''
  console.log('[Login] click → loginRedirect…')
  try {
    await msalInstance.loginRedirect(loginRequest)
  } catch (e) {
    console.error('[Login] FAILED', e)
    error.value = 'Anmeldung fehlgeschlagen: ' + (e.message || e)
    loading.value = false
    loginType.value = ''
  }
}

async function loginKunde() {
  loading.value = true
  loginType.value = 'customer'
  error.value = ''
  try {
    const result = await loginCustomer({ email: email.value, password: password.value })
    sessionStorage.setItem('customerJwt', result.token)
    sessionStorage.setItem('userRole', result.role)
    sessionStorage.setItem('userName', result.name)
    sessionStorage.setItem('customerId', result.id)
    if (result.targetId) sessionStorage.setItem('targetId', result.targetId)
    emit('logged-in', { role: result.role, name: result.name })
  } catch {
    error.value = 'E-Mail oder Passwort nicht korrekt.'
  } finally {
    loading.value = false
    loginType.value = ''
  }
}
</script>
