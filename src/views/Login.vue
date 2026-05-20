<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <!-- Logo / Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-900 rounded-2xl mb-4">
          <Building2 class="w-8 h-8 text-white" />
        </div>
        <h1 class="text-2xl font-bold text-gray-900">ITUKV Dashboard</h1>
        <p class="text-gray-500 text-sm mt-1">IT-Unternehmen kaufen & verkaufen</p>
      </div>

      <!-- Login Card -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">

        <!-- Fehler -->
        <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {{ error }}
        </div>

        <!-- mibeca Login (Microsoft) -->
        <div class="mb-6">
          <button
            @click="loginMibeca"
            :disabled="loading"
            class="w-full flex items-center justify-center gap-3 px-4 py-3 bg-blue-900 text-white rounded-xl font-medium hover:bg-blue-800 transition-colors disabled:opacity-50"
          >
            <Shield class="w-5 h-5" />
            Anmelden als mibeca-Team
          </button>
          <p class="text-xs text-gray-400 text-center mt-2">Über Microsoft-Konto</p>
        </div>

        <div class="relative my-6">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-200"></div>
          </div>
          <div class="relative flex justify-center text-xs text-gray-400 bg-white px-3">oder als Kunde anmelden</div>
        </div>

        <!-- Kunden-Login (E-Mail + Passwort) -->
        <form @submit.prevent="loginKunde">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">E-Mail-Adresse</label>
            <input
              v-model="email"
              type="email"
              required
              placeholder="ihre@email.de"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-1">Passwort</label>
            <input
              v-model="password"
              type="password"
              required
              placeholder="••••••••"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-900 text-white rounded-xl font-medium hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            <LogIn class="w-4 h-4" />
            {{ loading ? 'Anmelden...' : 'Anmelden' }}
          </button>
        </form>
      </div>

      <p class="text-center text-xs text-gray-400 mt-6">
        mibeca GmbH · M&A Beratung für IT-Unternehmen
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Building2, Shield, LogIn } from '@lucide/vue'
import { msalInstance, loginRequest } from '../authConfig.js'
import { loginCustomer } from '../api.js'

const emit = defineEmits(['logged-in'])

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function loginMibeca() {
  loading.value = true
  error.value = ''
  try {
    await msalInstance.initialize()
    const result = await msalInstance.loginPopup(loginRequest)
    sessionStorage.setItem('msalToken', result.idToken)
    sessionStorage.setItem('userRole', 'admin')
    sessionStorage.setItem('userName', result.account.name)
    emit('logged-in', { role: 'admin', name: result.account.name })
  } catch (e) {
    error.value = 'Microsoft-Login fehlgeschlagen. Bitte erneut versuchen.'
  } finally {
    loading.value = false
  }
}

async function loginKunde() {
  loading.value = true
  error.value = ''
  try {
    const result = await loginCustomer({ email: email.value, password: password.value })
    sessionStorage.setItem('customerJwt', result.token)
    sessionStorage.setItem('userRole', result.role)
    sessionStorage.setItem('userName', result.name)
    sessionStorage.setItem('customerId', result.id)
    emit('logged-in', { role: result.role, name: result.name })
  } catch (e) {
    error.value = 'E-Mail oder Passwort falsch.'
  } finally {
    loading.value = false
  }
}
</script>
