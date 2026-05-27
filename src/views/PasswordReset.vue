<template>
  <div class="min-h-screen bg-[#161e2a] flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <img src="/Logo_mibeca_Start.png" alt="mibeca" class="h-20 object-contain mx-auto" />
        <h1 class="text-2xl font-bold text-white mt-4">Neues Passwort setzen</h1>
      </div>

      <div class="bg-white rounded-2xl shadow-xl p-8">
        <div v-if="state === 'invalid'" class="text-center">
          <AlertCircle class="w-10 h-10 text-red-500 mx-auto mb-3" />
          <p class="text-gray-800 font-medium">Link ungültig</p>
          <p class="text-sm text-gray-500 mt-2">Der Reset-Link fehlt oder ist beschädigt. Bitte fordere einen neuen Link an.</p>
          <a href="/" class="inline-block mt-5 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium">Zur Anmeldung</a>
        </div>

        <div v-else-if="state === 'success'" class="text-center">
          <CheckCircle2 class="w-10 h-10 text-green-500 mx-auto mb-3" />
          <p class="text-gray-800 font-medium">Passwort aktualisiert</p>
          <p class="text-sm text-gray-500 mt-2">Du kannst dich jetzt mit deinem neuen Passwort anmelden.</p>
          <a href="/" class="inline-block mt-5 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium">Zur Anmeldung</a>
        </div>

        <form v-else @submit.prevent="submit" class="space-y-4">
          <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center gap-2">
            <AlertCircle class="w-4 h-4 flex-shrink-0" />
            {{ error }}
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Neues Passwort</label>
            <input
              v-model="password"
              type="password"
              required
              minlength="8"
              autocomplete="new-password"
              placeholder="mindestens 8 Zeichen"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Passwort wiederholen</label>
            <input
              v-model="password2"
              type="password"
              required
              minlength="8"
              autocomplete="new-password"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]"
            />
          </div>
          <button
            type="submit"
            :disabled="loading || !valid"
            class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#161e2a] text-white rounded-xl font-medium hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
            {{ loading ? 'Speichere…' : 'Passwort speichern' }}
          </button>
        </form>
      </div>

      <p class="text-center text-xs text-gray-500 mt-6">
        mibeca GmbH · M&amp;A Beratung für IT-Unternehmen
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { AlertCircle, CheckCircle2, Loader2 } from '@lucide/vue'
import { passwordResetConfirm } from '../api.js'

const params = new URLSearchParams(window.location.search)
const token = params.get('token') || ''

const password = ref('')
const password2 = ref('')
const loading = ref(false)
const error = ref('')
const state = ref(token ? 'form' : 'invalid')

const valid = computed(() => password.value.length >= 8 && password.value === password2.value)

async function submit() {
  if (!valid.value) {
    error.value = password.value.length < 8
      ? 'Passwort muss mindestens 8 Zeichen lang sein.'
      : 'Die Passwoerter stimmen nicht ueberein.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await passwordResetConfirm(token, password.value)
    state.value = 'success'
  } catch (e) {
    error.value = e?.response?.data?.error || 'Reset fehlgeschlagen. Link evtl. abgelaufen.'
  } finally {
    loading.value = false
  }
}
</script>
