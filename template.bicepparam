using 'template.bicep'

var prefix = readEnvironmentVariable('RESOURCE_PREFIX')
var sanitizedPrefix = replace(prefix, '-', '')
param isDevelopment = true
param apiImageName = 'tunnistamo'
param apiInternalUrl = '${prefix}-api.azurewebsites.net'
param apiUrl = (isDevelopment) ? 'testitunnistamo.turku.fi' : 'tunnistamo.turku.fi'
param apiWebAppName = '${prefix}-api'
param appInsightsName =  '${prefix}-appinsights'
param cacheName =  '${prefix}-cache'
param containerRegistryName =  '${sanitizedPrefix}registry'
param dbName =  'tunnistamo'
param dbServerName =  '${prefix}-db'
param dbAdminUsername =  'turkuadmin'
param dbUsername =  (isDevelopment) ? 'tunnistamo-qa' : 'tunnistamo-prod'
param keyvaultName =  '${prefix}kv'
param serverfarmPlanName =  'serviceplan'
param storageAccountName =  '${sanitizedPrefix}sa'
param apiOutboundIpName = (isDevelopment) ? 'turku-test-tunnistamo-outbound-ip' : 'turku-prod-tunnistamo-outbound-ip'
param natGatewayName = '${prefix}-nat'
param vnetName =  '${prefix}-vnet'
param workspaceName = '${prefix}-workspace'
