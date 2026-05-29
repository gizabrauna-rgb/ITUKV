/* ITUKV Service Worker — handles Web Push notifications */
self.addEventListener('install', (e) => { self.skipWaiting() })
self.addEventListener('activate', (e) => { e.waitUntil(self.clients.claim()) })

self.addEventListener('push', (event) => {
  let data = {}
  try { data = event.data ? event.data.json() : {} } catch { data = { title: 'ITUKV', body: event.data?.text() || '' } }
  const title = data.title || 'ITUKV Dashboard'
  const options = {
    body: data.body || '',
    icon: data.icon || '/Logo_mibeca_Start.png',
    badge: data.badge || '/Logo_mibeca_Start.png',
    tag: data.tag || 'itukv',
    data: { url: data.url || '/' },
    requireInteraction: false,
  }
  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = event.notification.data?.url || '/'
  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      // Falls Tab schon offen ist -> fokussieren
      for (const c of clients) {
        if (c.url.startsWith(self.location.origin) && 'focus' in c) {
          c.navigate(url)
          return c.focus()
        }
      }
      // Sonst neuen Tab oeffnen
      if (self.clients.openWindow) return self.clients.openWindow(url)
    })
  )
})
