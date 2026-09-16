// Kostenlose Azure Static Web App fuer checkliste.itukv.de mit eigener
// Link-Vorschau. Deployment erfolgt ueber GitHub Actions (Deploy-Token),
// daher hier kein repositoryUrl/branch (manuelles bzw. Token-Deployment).
//
// Anlegen/aktualisieren:
//   az deployment group create -g ITUKV --template-file infra/itukv-checkliste.bicep

@description('Name der Static Web App')
param name string = 'itukv-checkliste'

@description('Azure-Region der Static Web App')
@allowed([
  'westeurope'
  'northeurope'
])
param location string = 'westeurope'

@description('Optionale Custom Domain (z. B. checkliste.itukv.de). Leer = keine.')
param customDomain string = ''

resource swa 'Microsoft.Web/staticSites@2023-12-01' = {
  name: name
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    // Deployment via GitHub Actions Token, kein automatischer Build-Trigger
    allowConfigFileUpdates: true
  }
}

resource domain 'Microsoft.Web/staticSites/customDomains@2023-12-01' = if (!empty(customDomain)) {
  parent: swa
  name: customDomain
}

output defaultHostname string = swa.properties.defaultHostname
