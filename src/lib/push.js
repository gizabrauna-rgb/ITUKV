// Browser-Push: Service-Worker registrieren + Subscription verwalten
import { authFetch } from '../api.js'

function urlBase64ToUint8Array(base64) {
  const padding = '='.repeat((4 - base64.length % 4) % 4)
  const b64 = (base64 + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(b64)
  const out = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i)
  return out
}

export function isPushSupported() {
  return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
}

export async function getPushStatus() {
  if (!isPushSupported()) return { supported: false }
  let permission = Notification.permission
  let subscribed = false
  try {
    const reg = await navigator.serviceWorker.getRegistration('/sw.js')
    if (reg) {
      const sub = await reg.pushManager.getSubscription()
      subscribed = !!sub
    }
  } catch {}
  return { supported: true, permission, subscribed }
}

export async function enablePush() {
  if (!isPushSupported()) throw new Error('Push wird vom Browser nicht unterstützt')
  // 1) Service Worker registrieren
  const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' })
  await navigator.serviceWorker.ready
  // 2) Permission anfragen
  const perm = await Notification.requestPermission()
  if (perm !== 'granted') throw new Error('Benachrichtigungen wurden abgelehnt')
  // 3) VAPID-Public-Key vom Backend holen
  const cfg = await authFetch('/push-config', { method: 'GET' })
  if (!cfg.publicKey) throw new Error('Server: VAPID-Schlüssel nicht konfiguriert')
  // 4) Subscription erstellen
  let sub = await reg.pushManager.getSubscription()
  if (!sub) {
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(cfg.publicKey),
    })
  }
  // 5) Subscription ans Backend
  const subJson = sub.toJSON()
  await authFetch('/push-subscribe', { method: 'POST', data: {
    endpoint: subJson.endpoint,
    keys: subJson.keys,
  }})
  return true
}

export async function disablePush() {
  if (!isPushSupported()) return
  try {
    const reg = await navigator.serviceWorker.getRegistration('/sw.js')
    if (!reg) return
    const sub = await reg.pushManager.getSubscription()
    if (sub) {
      const subJson = sub.toJSON()
      try {
        await authFetch('/push-unsubscribe', { method: 'POST', data: { endpoint: subJson.endpoint } })
      } catch {}
      await sub.unsubscribe()
    }
  } catch {}
}

export async function testPush() {
  return authFetch('/push-test', { method: 'POST', data: {} })
}
