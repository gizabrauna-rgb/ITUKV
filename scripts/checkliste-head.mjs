// Setzt in der gebauten dist/index.html die Vorschau-Informationen (Titel,
// Beschreibung, Open-Graph-/Twitter-Karte) fuer die oeffentliche Checkliste.
// Wird NUR im Deploy der eigenen Checkliste-App (itukv-checkliste) ausgefuehrt,
// damit checkliste.itukv.de beim Teilen eine eigene Vorschau bekommt.
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const indexPath = resolve(__dirname, '..', 'dist', 'index.html')

const TITEL = 'Was ist Dein IT-Unternehmen wert? – ITUKV'
const BESCHREIBUNG =
  'Finde in wenigen Minuten heraus, wie verkaufsfähig Dein IT-Unternehmen ist und welchen Wert es hat – kostenlos und unverbindlich.'
const URL = 'https://checkliste.itukv.de/'
const BILD = 'https://checkliste.itukv.de/og-checkliste.jpg'

// Open-Graph-/Twitter-Tags, die Link-Vorschauen (WhatsApp, LinkedIn, E-Mail) lesen
const metaTags = `
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="ITUKV" />
    <meta property="og:locale" content="de_DE" />
    <meta property="og:title" content="${TITEL}" />
    <meta property="og:description" content="${BESCHREIBUNG}" />
    <meta property="og:url" content="${URL}" />
    <meta property="og:image" content="${BILD}" />
    <meta property="og:image:width" content="1080" />
    <meta property="og:image:height" content="1080" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="${TITEL}" />
    <meta name="twitter:description" content="${BESCHREIBUNG}" />
    <meta name="twitter:image" content="${BILD}" />
`

let html = readFileSync(indexPath, 'utf8')

// Titel setzen (egal was vorher drin stand)
html = html.replace(/<title>[\s\S]*?<\/title>/i, `<title>${TITEL}</title>`)

// Beschreibung setzen bzw. ergaenzen
if (/<meta\s+name="description"[^>]*>/i.test(html)) {
  html = html.replace(
    /<meta\s+name="description"[^>]*>/i,
    `<meta name="description" content="${BESCHREIBUNG}" />`,
  )
} else {
  html = html.replace(/<\/title>/i, `</title>\n    <meta name="description" content="${BESCHREIBUNG}" />`)
}

// Vorhandene OG/Twitter-Tags entfernen (falls erneut ausgefuehrt), dann neu einsetzen
html = html.replace(/\s*<meta\s+(?:property="og:[^"]*"|name="twitter:[^"]*")[^>]*>/gi, '')
html = html.replace(/<\/head>/i, `${metaTags}  </head>`)

writeFileSync(indexPath, html, 'utf8')
console.log('checkliste-head: Vorschau-Tags in dist/index.html gesetzt.')
