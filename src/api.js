import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:7071/api'
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

// Targets (Mandate)
export const getTargets = () => authFetch('/targets')
export const getTarget = (id) => authFetch(`/targets/${id}`)
export const createTarget = (data) => authFetch('/targets', { method: 'POST', data })
export const updateTarget = (id, data) => authFetch(`/targets/${id}`, { method: 'PATCH', data })

// Interessenten
export const getInteressenten = (targetId) => authFetch(`/targets/${targetId}/interessenten`)
export const updateInteressent = (targetId, id, data) => authFetch(`/targets/${targetId}/interessenten/${id}`, { method: 'PATCH', data })

// CRM / Kontakte
export const getKontakte = (params) => authFetch('/kontakte', { params })
export const createKontakt = (data) => authFetch('/kontakte', { method: 'POST', data })
export const updateKontakt = (id, data) => authFetch(`/kontakte/${id}`, { method: 'PATCH', data })
export const importKontakte = (data) => authFetch('/kontakte/import', { method: 'POST', data })
export const exportKontakte = (params) => authFetch('/kontakte/export', { params })

// Ausschreibungen
export const getAusschreibungen = () => authFetch('/ausschreibungen')
export const getAusschreibung = (id) => authFetch(`/ausschreibungen/${id}`)
export const requestExpose = (id, data) => authFetch(`/ausschreibungen/${id}/expose`, { method: 'POST', data })

// NDA
export const getNdaStatus = (ausschreibungId) => authFetch(`/nda/${ausschreibungId}`)
export const sendNda = (data) => authFetch('/nda/send', { method: 'POST', data })

// Dokumente
export const getDokumente = (targetId) => authFetch(`/targets/${targetId}/dokumente`)
export const uploadDokument = (targetId, formData) => authFetch(`/targets/${targetId}/dokumente`, { method: 'POST', data: formData, headers: { 'Content-Type': 'multipart/form-data' } })
