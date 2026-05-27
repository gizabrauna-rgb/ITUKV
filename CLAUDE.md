# CLAUDE.md – ITUKV

Dieses Projekt ist das M&A-Dashboard für die **Mike Bergmann Akademie**.
Es ist vollständig getrennt vom KIwerk-Dashboard.

## Commands

```bash
npm run dev        # Dev-Server auf http://localhost:5173
npm run build      # Production Build → dist/
npm run preview    # Production Build vorschau

# Backend Deploy — IMMER über das Safety-Script, NIE direkt:
scripts/deploy-backend.sh
```

## ⚠️ Backend-Deploy-Regel (PFLICHT)

**Niemals** `az functionapp deployment source config-zip` direkt ausführen.

**Immer** `scripts/deploy-backend.sh` — das Script macht 4 Pre-Checks
(Python AST, requirements.txt, host.json, Route-Count) und einen
Post-Deploy-Health-Check gegen `/api/health`. Wenn irgendein Check
fehlschlägt, wird der Deploy abgebrochen und das Backend bleibt
unverändert.

Hintergrund: am 27.05.2026 wurde durch einen kaputten sed-Replace ein
Backtick statt Apostroph in einen f-String geschrieben. Python konnte
das Modul nicht laden, alle Routes lieferten 404, das Dashboard war
für ~30 Min unbenutzbar. Pre-AST-Check hätte das in 1 Sekunde
abgefangen.

## Stack

- Vue 3 + Vite
- Tailwind CSS v4
- Hosting: Azure Static Web Apps (Free Tier)

## Architektur

Routing manuell in `App.vue` über `window.location.pathname` (kein Vue Router).
Kleine wiederverwendbare Komponenten in `src/components/`.

## Environments

| | Production | Staging |
|---|---|---|
| Frontend | (noch nicht angelegt) | (noch nicht angelegt) |

Azure Resource Group: `ITUKV` (westeurope)

## Umgebungsvariablen

| Variable | Zweck |
|---|---|
| `VITE_APP_REGISTRATION_CLIENTID` | Microsoft Entra ID Client ID |
| `VITE_API_BASE` | Backend-URL |
| `VITE_FUNC_KEY` | Azure Function Key |
