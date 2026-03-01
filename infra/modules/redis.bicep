param environment string
param location string
param tags object

var cacheName = 'redis-nexus-${environment}'

resource redisCache 'Microsoft.Cache/redis@2024-03-01' = {
  name: cacheName
  location: location
  tags: tags
  properties: {
    sku: {
      name: environment == 'production' ? 'Standard' : 'Basic'
      family: 'C'
      capacity: environment == 'production' ? 1 : 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {
      'maxmemory-policy': 'allkeys-lru'
    }
  }
}

output hostName string = redisCache.properties.hostName
output port int = redisCache.properties.sslPort
output cacheName string = redisCache.name
