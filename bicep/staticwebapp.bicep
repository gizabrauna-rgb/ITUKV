param name string = 'itukv-dashboard'
param location string = 'westeurope'
param repositoryUrl string = 'https://github.com/gizabrauna-rgb/ITUKV'
param branch string = 'main'
param repositoryToken string

resource staticWebApp 'Microsoft.Web/staticSites@2022-03-01' = {
  name: name
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    repositoryUrl: repositoryUrl
    branch: branch
    repositoryToken: repositoryToken
    buildProperties: {
      appLocation: '/'
      outputLocation: 'dist'
    }
  }
}

output defaultHostname string = staticWebApp.properties.defaultHostname
