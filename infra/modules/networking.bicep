param environment string
param location string
param tags object

var vnetName = 'vnet-nexus-${environment}'

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: { addressPrefixes: ['10.0.0.0/16'] }
    subnets: [
      {
        name: 'apps'
        properties: { addressPrefix: '10.0.1.0/24' }
      }
      {
        name: 'data'
        properties: { addressPrefix: '10.0.2.0/24' }
      }
    ]
  }
}

output vnetId string = vnet.id
output appsSubnetId string = vnet.properties.subnets[0].id
output dataSubnetId string = vnet.properties.subnets[1].id
