# CLAUDE.md – ITUKV

Dieses Projekt ist das M&A-Dashboard für die **Mike Bergmann Akademie**.
Es ist vollständig getrennt vom KIwerk-Dashboard.

## Commands

```bash
npm run dev        # Dev-Server auf http://localhost:5173
npm run build      # Production Build → dist/
npm run preview    # Production Build vorschau
```

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
