<template>
  <Teleport to="body">
    <div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      <transition-group name="toast">
        <div v-for="t in toast.toasts.value" :key="t.id"
          :class="['pointer-events-auto px-4 py-3 rounded-xl shadow-lg border min-w-[280px] max-w-md flex items-start gap-3 text-sm', toastClass(t.type)]">
          <component :is="iconFor(t.type)" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div class="flex-1 leading-snug">{{ t.message }}</div>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<script setup>
import { CheckCircle2, XCircle, Info, AlertTriangle } from '@lucide/vue'
import { toast } from '../composables/useToast.js'

function toastClass(t) {
  if (t === 'success') return 'bg-green-50 border-green-200 text-green-900'
  if (t === 'error')   return 'bg-red-50 border-red-200 text-red-900'
  if (t === 'warn')    return 'bg-amber-50 border-amber-200 text-amber-900'
  return 'bg-white border-gray-200 text-gray-800'
}
function iconFor(t) {
  if (t === 'success') return CheckCircle2
  if (t === 'error')   return XCircle
  if (t === 'warn')    return AlertTriangle
  return Info
}
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all .25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to { opacity: 0; transform: translateX(20px); }
</style>
