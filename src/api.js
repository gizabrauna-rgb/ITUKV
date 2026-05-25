import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'
const FUNC_KEY = import.meta.env.VITE_FUNC_KEY || ''

function getToken() {
  return sessionStorage.getItem('customerJwt') || sessionStorage.getItem('msalToken') || ''
}

export async function authFetch(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(FUNC_KEY && { 'x-functions-key': FUNC_KEY }),
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  }
  const response = await axios({
    url: `${API_BASE}${path}`,
    ...options,
    headers,
  })
  return response.data
}

// Auth
export const loginCustomer = (data) => authFetch('/login', { method: 'POST', data })
export const resolveMsLogin = (data) => authFetch('/auth/resolve', { method: 'POST', data })

// User Management (KIwerk-style: separate Endpoints statt REST)
export const getUsers = () => authFetch('/users')
export const createUser = (data) => authFetch('/user-create', { method: 'POST', data })
export const deleteUser = (id) => authFetch('/user-delete', { method: 'POST', data: { id } })
export const resetUserPassword = (id, data = {}) => authFetch('/user-reset-password', { method: 'POST', data: { id, ...data } })
export const updateUser = (id, data) => createUser(data)

// Targets (Mandate) – KIwerk-Style action endpoints
export const getTargets = () => authFetch('/targets')
export const getTarget = (id) => authFetch('/target-get', { method: 'POST', data: { id } })
export const createTarget = (data) => authFetch('/targets', { method: 'POST', data })
export const updateTarget = (id, data) => authFetch('/target-update', { method: 'POST', data: { id, ...data } })

// Interessenten
export const getInteressenten = (targetId) => authFetch('/interessenten', { method: 'POST', data: { targetId } })
export const createInteressent = (data) => authFetch('/interessent-create', { method: 'POST', data })
export const updateInteressent = (id, data) => authFetch('/interessent-update', { method: 'POST', data: { id, ...data } })
export const deleteInteressent = (id) => authFetch('/interessent-delete', { method: 'POST', data: { id } })

// CRM / Kontakte
export const getKontakte = (params) => authFetch('/kontakte', { params })
export const createKontakt = (data) => authFetch('/kontakte', { method: 'POST', data })
export const updateKontakt = (id, data) => authFetch(`/kontakte/${id}`, { method: 'PATCH', data })
export const importKontakte = (data) => authFetch('/kontakte/import', { method: 'POST', data })
export const exportKontakte = (params) => authFetch('/kontakte/export', { params })

// Ausschreibungen
export const getAusschreibungen = () => authFetch('/ausschreibungen')
export const createAusschreibung = (data) => authFetch('/ausschreibungen', { method: 'POST', data })
export const updateAusschreibung = (id, data) => authFetch('/ausschreibung-update', { method: 'POST', data: { id, ...data } })
export const deleteAusschreibung = (id) => authFetch('/ausschreibung-delete', { method: 'POST', data: { id } })
export const requestExpose = (id, data) => authFetch(`/ausschreibungen/${id}/expose`, { method: 'POST', data })

// NDA
export const getNdaStatus = (ausschreibungId) => authFetch(`/nda/${ausschreibungId}`)
export const sendNda = (data) => authFetch('/nda/send', { method: 'POST', data })

// Erfolgsmeldungen / PR-Mitteilungen
export const getPrMitteilungen = () => authFetch('/pr-mitteilungen')
export const createPrMitteilung = (data) => authFetch('/pr-mitteilungen', { method: 'POST', data })
export const updatePrMitteilung = (id, data) => authFetch(`/pr-mitteilungen/${id}`, { method: 'PATCH', data })
export const deletePrMitteilung = (id) => authFetch(`/pr-mitteilungen/${id}`, { method: 'DELETE' })
export const generatePrText = (id, data) => authFetch(`/pr-mitteilungen/${id}/generate`, { method: 'POST', data })
export const sendPrMitteilung = (id, data) => authFetch(`/pr-mitteilungen/${id}/send`, { method: 'POST', data })

// Verteiler
export const getVerteiler = () => authFetch('/verteiler')
export const createVerteiler = (data) => authFetch('/verteiler', { method: 'POST', data })
export const updateVerteiler = (id, data) => authFetch(`/verteiler/${id}`, { method: 'PATCH', data })
export const deleteVerteiler = (id) => authFetch(`/verteiler/${id}`, { method: 'DELETE' })

// Dokumente
export const getDokumente = (targetId) => authFetch(`/targets/${targetId}/dokumente`)
export const uploadDokument = (targetId, formData) => authFetch(`/targets/${targetId}/dokumente`, { method: 'POST', data: formData, headers: { 'Content-Type': 'multipart/form-data' } })

// === Oeffentliche Signier-API (kein Auth, Token in URL) ===
export async function publicFetchSignInfo(token) {
  const res = await fetch(`${API_BASE}/sign-info?token=${encodeURIComponent(token)}`)
  if (!res.ok) { const d = await res.json().catch(()=>({})); const e = new Error(d.error || `HTTP ${res.status}`); e.status = res.status; throw e }
  return res.json()
}
export async function publicFetchSignPdfBlob(token) {
  const res = await fetch(`${API_BASE}/sign-pdf?token=${encodeURIComponent(token)}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return URL.createObjectURL(await res.blob())
}
export async function publicSendSignCode(token) {
  const res = await fetch(`${API_BASE}/sign-send-code`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ token }) })
  const d = await res.json().catch(()=>({}))
  if (!res.ok) throw new Error(d.error || `HTTP ${res.status}`)
  return d
}
export async function publicSubmitSignature(payload) {
  const res = await fetch(`${API_BASE}/sign-submit`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) })
  const d = await res.json().catch(()=>({}))
  if (!res.ok) throw new Error(d.error || `HTTP ${res.status}`)
  return d
}
