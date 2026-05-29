<template>
  <div :class="['flex items-center gap-3 p-3 rounded-xl border', subscribed ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50']">
    <div :class="['w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0', subscribed ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600']">
      <Bell class="w-4 h-4" />
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-semibold text-gray-800">Browser-Benachrichtigungen</div>
      <div class="text-xs text-gray-500">
        <template v-if="!supported">Dein Browser unterstützt das nicht.</template>
        <template v-else-if="permission === 'denied'">Vom Browser blockiert. Bitte in den Browser-Einstellungen erlauben.</template>
        <template v-else-if="subscribed">Aktiviert – du wirst über neue Nachrichten benachrichtigt.</template>
        <template v-else>Aktivieren, um sofort über neue Nachrichten informiert zu werden.</template>
      </div>
    </div>
    <button v-if="supported && permission !== 'denied'" @click="toggle" :disabled="busy"
      :class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0',
               subscribed ? 'bg-green-500' : 'bg-gray-300', busy ? 'opacity-50' : '']">
      <span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                     subscribed ? 'translate-x-6' : 'translate-x-1']"></span>
    </button>
    <button v-if="subscribed" @click="doTest" :disabled="busy"
      class="text-xs px-2 py-1 border border-gray-200 rounded-lg hover:bg-white">
      Test
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Bell } from '@lucide/vue'
import { isPushSupported, getPushStatus, enablePush, disablePush, testPush } from '../lib/push.js'
import { toast } from '../composables/useToast.js'

const supported = ref(false)
const permission = ref('default')
const subscribed = ref(false)
const busy = ref(false)

async function refresh() {
  const s = await getPushStatus()
  supported.value = !!s.supported
  permission.value = s.permission || 'default'
  subscribed.value = !!s.subscribed
}
onMounted(refresh)

async function toggle() {
  busy.value = true
  try {
    if (subscribed.value) {
      await disablePush()
      toast.success('Benachrichtigungen deaktiviert')
    } else {
      await enablePush()
      toast.success('Benachrichtigungen aktiviert')
    }
    await refresh()
  } catch (e) {
    toast.error(e.message || 'Fehler')
  } finally { busy.value = false }
}

async function doTest() {
  busy.value = true
  try {
    const r = await testPush()
    toast.success(`Test-Push verschickt (${r.sent || 0})`)
  } catch (e) {
    toast.error(e?.response?.data?.error || e.message)
  } finally { busy.value = false }
}
</script>
