param environment string
param location string
param tags object

var accountName = 'cosmos-nexus-${environment}'

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: accountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    capabilities: [{ name: 'EnableGremlin' }]
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    locations: [{ locationName: location, failoverPriority: 0 }]
    enableFreeTier: false
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/gremlinDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: 'nexus'
  properties: {
    resource: { id: 'nexus' }
    options: { throughput: 400 }
  }
}

resource container 'Microsoft.DocumentDB/databaseAccounts/gremlinDatabases/graphs@2024-05-15' = {
  parent: database
  name: 'main'
  properties: {
    resource: {
      id: 'main'
      partitionKey: { paths: ['/partitionKey'], kind: 'Hash' }
      indexingPolicy: { indexingMode: 'consistent', automatic: true }
    }
  }
}

output gremlinEndpoint string = 'wss://${cosmosAccount.name}.gremlin.cosmos.azure.com:443/gremlin'
output accountName string = cosmosAccount.name
