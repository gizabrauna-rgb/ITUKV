<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  kontakte: { type: Array, default: () => [] },
})

const mapEl = ref(null)
let mapInstance = null
let markersLayer = null

const TYP_COLORS = {
  'PE': '#a855f7',
  'Systemhausgruppe': '#3498db',
  'Strategisch': '#097e92',
  'Verkäufer-Interesse': '#c8b274',
  'Sonstige': '#64748b',
}

function makeIcon(typ) {
  const color = TYP_COLORS[typ] || '#097e92'
  return L.divIcon({
    className: 'itukv-pin',
    html: `<div style="width:10px;height:10px;border-radius:50%;background:${color};border:1.5px solid white;box-shadow:0 1px 2px rgba(0,0,0,0.3)"></div>`,
    iconSize: [10, 10],
    iconAnchor: [5, 5],
    popupAnchor: [0, -8],
  })
}

function escapeHtml(s) {
  return String(s ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#39;')
}

function renderMarkers() {
  if (!mapInstance || !markersLayer) return
  markersLayer.clearLayers()
  for (const k of props.kontakte) {
    if (k.lat == null || k.lon == null) continue
    const mailLink = k.email ? `<a href="mailto:${escapeHtml(k.email)}" style="color:#097e92;text-decoration:none;font-size:11px">${escapeHtml(k.email)}</a>` : ''
    const popupHtml = `
      <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; min-width: 180px;">
        <p style="font-weight: 600; color: #161e2a; margin: 0 0 4px 0; font-size: 14px;">${escapeHtml(k.firma)}</p>
        ${k.name ? `<p style="margin: 0 0 4px 0; color: #475569; font-size: 12px;">${escapeHtml(k.name)}</p>` : ''}
        <p style="margin: 0 0 4px 0; color: #64748b; font-size: 12px;">
          ${k.plz ? escapeHtml(k.plz) + ' ' : ''}${escapeHtml(k.ort || '')}
        </p>
        ${mailLink ? `<p style="margin: 4px 0 0 0;">${mailLink}</p>` : ''}
        <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em;">${escapeHtml(k.typ || 'Kontakt')}</p>
      </div>`
    L.marker([k.lat, k.lon], { icon: makeIcon(k.typ) })
      .bindPopup(popupHtml)
      .addTo(markersLayer)
  }
}

onMounted(() => {
  if (!mapEl.value) return
  mapInstance = L.map(mapEl.value, {
    center: [50.0, 10.5],
    zoom: 5,
    minZoom: 4,
    maxZoom: 12,
    scrollWheelZoom: false,
    zoomControl: true,
  })
  L.tileLayer('https://{s}.tile.openstreetmap.de/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende',
    subdomains: 'abc',
    maxZoom: 18,
  }).addTo(mapInstance)

  markersLayer = L.layerGroup().addTo(mapInstance)
  renderMarkers()
  mapInstance.fitBounds(
    L.latLngBounds([[45.5, 5.5], [55.5, 17.5]]),
    { padding: [20, 20] }
  )
})

watch(() => props.kontakte, () => renderMarkers(), { deep: true })

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>

<template>
  <div ref="mapEl" class="w-full h-[520px] rounded-xl overflow-hidden border border-gray-100"
    style="background-color: #f1f3f5;"></div>
</template>

<style>
.leaflet-container {
  background-color: #f1f3f5;
}
.leaflet-popup-content-wrapper {
  border-radius: 8px;
}
</style>
