import { createApp } from 'vue'
import { EventType } from '@azure/msal-browser'
import './style.css'
import App from './App.vue'
import { msalInstance } from './authConfig.js'

try {
  await msalInstance.initialize()
  const result = await msalInstance.handleRedirectPromise()

  // Stale interaction.status aufräumen
  for (const k of Object.keys(sessionStorage)) {
    if (k.includes('interaction.status')) sessionStorage.removeItem(k)
  }

  if (result?.account) {
    msalInstance.setActiveAccount(result.account)
    // Direkt nach Redirect-Login: Rolle vom Backend abholen
    try {
      const userEmail = (result.account.username || '').toLowerCase()
      const userName = result.account.name || userEmail
      const { resolveMsLogin } = await import('./api.js')
      const resolved = await resolveMsLogin({ email: userEmail, name: userName })
      sessionStorage.setItem('msalToken', result.idToken)
      sessionStorage.setItem('customerJwt', resolved.token)
      sessionStorage.setItem('userRole', resolved.role)
      sessionStorage.setItem('userName', resolved.name)
      sessionStorage.setItem('customerId', resolved.id)
      if (resolved.targetId) sessionStorage.setItem('targetId', resolved.targetId)
    } catch (e) {
      console.error('[boot] resolve role failed – fallback auf Admin', e)
      // Fallback: Microsoft-Login = Admin
      sessionStorage.setItem('msalToken', result.idToken)
      sessionStorage.setItem('userRole', 'admin')
      sessionStorage.setItem('userName', result.account.name || result.account.username)
    }
  } else {
    const accounts = msalInstance.getAllAccounts()
    if (accounts.length > 0) msalInstance.setActiveAccount(accounts[0])
  }

  msalInstance.addEventCallback((event) => {
    if (
      (event.eventType === EventType.LOGIN_SUCCESS ||
       event.eventType === EventType.ACQUIRE_TOKEN_SUCCESS) &&
      event.payload?.account
    ) {
      msalInstance.setActiveAccount(event.payload.account)
    }
  })

  if (window.location.hash.includes('code=')) {
    window.history.replaceState({}, '', window.location.pathname + window.location.search)
  }

  createApp(App).mount('#app')
} catch (err) {
  console.error('[boot] FATAL', err)
  const root = document.getElementById('app')
  if (root) {
    root.innerHTML = `<div style="padding:2rem;font-family:system-ui;color:#b91c1c">Fehler beim Laden: ${err?.message || err}<br><button onclick="sessionStorage.clear();location.reload()">Neu starten</button></div>`
  }
}
