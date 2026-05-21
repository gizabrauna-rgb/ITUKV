// MSAL (Microsoft Authentication Library) – Konfiguration
//
// Die Client-ID stammt aus der App Registration im Azure Portal.
// Sie ist NICHT geheim und kann auch direkt im Code stehen.
// In der Static Web App muss VITE_APP_REGISTRATION_CLIENTID gesetzt sein
// (oder im GitHub Actions Workflow aus APP_REGISTRATION_CLIENTID gemappt).

import { PublicClientApplication, LogLevel } from '@azure/msal-browser'

const CLIENT_ID = import.meta.env.VITE_APP_REGISTRATION_CLIENTID || '0e531dfd-9c67-460c-b9f5-c2d57c60cb83'

if (!CLIENT_ID) {
  // eslint-disable-next-line no-console
  console.error('[MSAL] VITE_APP_REGISTRATION_CLIENTID ist nicht gesetzt.')
}

function pickRedirectUri() {
  return `${window.location.origin}/`
}

export const msalConfig = {
  auth: {
    clientId: CLIENT_ID,
    // "organizations" passt zu App Reg signInAudience=AzureADMultipleOrgs
    authority: 'https://login.microsoftonline.com/organizations',
    redirectUri: pickRedirectUri(),
    postLogoutRedirectUri: window.location.origin,
    navigateToLoginRequestUrl: true,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message) => {
        if (level === LogLevel.Error) {
          // eslint-disable-next-line no-console
          console.error('[MSAL]', message)
        }
      },
      piiLoggingEnabled: false,
      logLevel: LogLevel.Warning,
    },
  },
}

export const loginRequest = {
  scopes: ['openid', 'profile', 'email', 'User.Read'],
}

export const apiTokenRequest = {
  scopes: ['openid', 'profile', 'email'],
}

export const msalInstance = new PublicClientApplication(msalConfig)
