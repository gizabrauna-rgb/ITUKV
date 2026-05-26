import { ref } from 'vue'

const toasts = ref([])
let nextId = 1

export function useToast() {
  function show(message, type = 'info', durationMs = 3500) {
    const id = nextId++
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, durationMs)
  }
  return {
    toasts,
    success: (m) => show(m, 'success', 3000),
    error:   (m) => show(m, 'error', 5000),
    info:    (m) => show(m, 'info', 3000),
    warn:    (m) => show(m, 'warn', 4000),
  }
}

// Globaler Shortcut – einfach in jeder Komponente importierbar
export const toast = useToast()
