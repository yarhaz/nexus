targetScope = 'subscription'

@description('Environment name (staging, production)')
param environment string = 'staging'

@description('Azure region')
param location string = 'eastus'

var resourceGroupName = 'rg-nexus-${environment}'
var tags = {
  application: 'nexus-idp'
  environment: environment
  managedBy: 'bicep'
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module networking 'modules/networking.bicep' = {
  scope: rg
  name: 'networking'
  params: {
    environment: environment
    location: location
    tags: tags
  }
}

module cosmos 'modules/cosmos.bicep' = {
  scope: rg
  name: 'cosmos'
  params: {
    environment: environment
    location: location
    tags: tags
  }
}

module redis 'modules/redis.bicep' = {
  scope: rg
  name: 'redis'
  params: {
    environment: environment
    location: location
    tags: tags
  }
}

module containerApps 'modules/container-apps.bicep' = {
  scope: rg
  name: 'container-apps'
  params: {
    environment: environment
    location: location
    tags: tags
    cosmosEndpoint: cosmos.outputs.gremlinEndpoint
    redisHost: redis.outputs.hostName
    subnetId: networking.outputs.appsSubnetId
  }
}

output resourceGroupName string = rg.name
output backendUrl string = containerApps.outputs.backendUrl
output frontendUrl string = containerApps.outputs.frontendUrl
