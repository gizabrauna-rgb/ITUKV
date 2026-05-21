import { PublicClientApplication } from '@azure/msal-browser'

export const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_APP_REGISTRATION_CLIENTID || '0e531dfd-9c67-460c-b9f5-c2d57c60cb83',
    authority: 'https://login.microsoftonline.com/common',
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
}

export const loginRequest = {
  scopes: ['openid', 'profile', 'email'],
}

export const msalInstance = new PublicClientApplication(msalConfig)
