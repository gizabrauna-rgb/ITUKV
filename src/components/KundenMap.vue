<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  kontakte: { type: Array, default: () => [] },
  targets: { type: Array, default: () => [] },
  centerPlz: { type: String, default: '' },
  centerCoords: { type: Object, default: null },
  radiusKm: { type: Number, default: 0 },
  colorByProdukt: { type: String, default: '' },  // wenn gesetzt: Pin-Farbe nach diesem Produkt
})

// Hex-Farben pro Produkt (für die Karte)
const PRODUKT_COLORS = {
  hatUC: '#ef4444',          // rot
  hatUCS: '#a855f7',         // lila
  hatMC: '#eab308',          // gelb
  hatFKE: '#d97706',         // bernstein
  hatUVE: '#ec4899',         // pink
  hatVME: '#57534e',         // steingrau
  hatKIwerkOne: '#10b981',   // smaragd
  hatMSQ: '#6366f1',         // indigo
  hatKMQ: '#0891b2',         // cyan
  hatKIT: '#d946ef',         // fuchsia
  hatKK: '#e11d48',          // rose
  imITUKV: '#097e92',        // teal
}

const mapEl = ref(null)
let mapInstance = null
let markersLayer = null
let circleLayer = null

// Farb-Konvention:
// - Target (Verkäufer): orange
// - Investor / strategischer Käufer: grün
// - Sonstiger Kunde: teal
const TYP_COLORS = {
  'TARGET': '#f97316',         // orange
  'INVESTOR': '#22c55e',       // grün
  'PE': '#22c55e',
  'Systemhausgruppe': '#22c55e',
  'Strategisch': '#22c55e',
  'Verkäufer-Interesse': '#c8b274',
  'Kunde': '#60a5fa',          // hellblau (Bestandskunde)
  'Ex-Kunde': '#475569',       // dunkles slate
  'Sonstige': '#94a3b8',
}

function colorForKontakt(k) {
  // Wenn nach einem Produkt gefiltert wird → Pin-Farbe nach Produkt
  if (props.colorByProdukt && PRODUKT_COLORS[props.colorByProdukt]) {
    return PRODUKT_COLORS[props.colorByProdukt]
  }
  // Investor-Status
  if (['PE','Systemhausgruppe','Strategisch','INVESTOR'].includes(k.typ)) return TYP_COLORS.INVESTOR
  if (k.typ === 'Verkäufer-Interesse') return TYP_COLORS['Verkäufer-Interesse']
  if (k.kundenstatus === 'Ex-Kunde') return TYP_COLORS['Ex-Kunde']
  return TYP_COLORS.Kunde
}

function makeIcon(color, size = 10) {
  return L.divIcon({
    className: 'itukv-pin',
    html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:${color};border:1.5px solid white;box-shadow:0 1px 2px rgba(0,0,0,0.3)"></div>`,
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
    popupAnchor: [0, -size/2 - 2],
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

  // Kontakte (Bestand, Investoren)
  for (const k of props.kontakte) {
    if (k.lat == null || k.lon == null) continue
    const color = colorForKontakt(k)
    const mailLink = k.email ? `<a href="mailto:${escapeHtml(k.email)}" style="color:${color};text-decoration:none;font-size:11px">${escapeHtml(k.email)}</a>` : ''
    const popupHtml = `
      <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; min-width: 180px;">
        <p style="font-weight: 600; color: #161e2a; margin: 0 0 4px 0; font-size: 14px;">${escapeHtml(k.firma)}</p>
        ${k.name ? `<p style="margin: 0 0 4px 0; color: #475569; font-size: 12px;">${escapeHtml(k.name)}</p>` : ''}
        <p style="margin: 0 0 4px 0; color: #64748b; font-size: 12px;">${k.plz ? escapeHtml(k.plz) + ' ' : ''}${escapeHtml(k.ort || '')}</p>
        ${mailLink ? `<p style="margin: 4px 0 0 0;">${mailLink}</p>` : ''}
        <p style="margin: 6px 0 0 0; color: ${color}; font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">${escapeHtml(k.typ || k.kundenstatus || 'Kontakt')}</p>
      </div>`
    L.marker([k.lat, k.lon], { icon: makeIcon(color, 10) })
      .bindPopup(popupHtml)
      .addTo(markersLayer)
  }

  // Targets (Verkäufer) – größer und orange
  for (const t of props.targets) {
    if (t.lat == null || t.lon == null) continue
    const popupHtml = `
      <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; min-width: 200px;">
        <span style="display:inline-block;font-family:monospace;background:#f9731620;color:#f97316;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:600">${escapeHtml(t.mbNr)}</span>
        <p style="font-weight: 600; color: #161e2a; margin: 6px 0 4px 0; font-size: 14px;">${escapeHtml(t.verkaueferName || t.firma)}</p>
        <p style="margin: 0; color: #64748b; font-size: 12px;">${t.plz ? escapeHtml(t.plz) + ' ' : ''}${escapeHtml(t.region || t.ort || '')}</p>
        <p style="margin: 6px 0 0 0; color: #f97316; font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">TARGET (Verkäufer)</p>
      </div>`
    L.marker([t.lat, t.lon], { icon: makeIcon('#f97316', 14) })
      .bindPopup(popupHtml)
      .addTo(markersLayer)
  }

  // Radius-Kreis
  if (circleLayer) {
    mapInstance.removeLayer(circleLayer)
    circleLayer = null
  }
  if (props.radiusKm > 0 && props.centerCoords?.lat && props.centerCoords?.lon) {
    circleLayer = L.circle([props.centerCoords.lat, props.centerCoords.lon], {
      radius: props.radiusKm * 1000,
      color: '#f97316',
      fillColor: '#f97316',
      fillOpacity: 0.08,
      weight: 2,
    }).addTo(mapInstance)
    // Optional: Karte auf Kreis-Bereich einzoomen
    mapInstance.fitBounds(circleLayer.getBounds(), { padding: [40, 40], maxZoom: 10 })
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

watch(() => [props.kontakte, props.targets, props.centerPlz, props.radiusKm, props.centerCoords],
  () => renderMarkers(), { deep: true })

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
.leaflet-container { background-color: #f1f3f5; }
.leaflet-popup-content-wrapper { border-radius: 8px; }
</style>
