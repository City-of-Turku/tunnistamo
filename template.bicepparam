using 'template.bicep'

var prefix = readEnvironmentVariable('RESOURCE_PREFIX')
var sanitizedPrefix = replace(prefix, '-', '')
param isProduction = false
param apiImageName = 'tunnistamo:latest'
param apiInternalUrl = '${prefix}-api.azurewebsites.net'
param apiUrl = (isProduction) ? 'tunnistamo.turku.fi' : 'testitunnistamo.turku.fi'
param apiWebAppName = '${prefix}-api'
param appInsightsName =  '${prefix}-appinsights'
param cacheName =  '${prefix}-cache'
param containerRegistryName =  '${sanitizedPrefix}registry'
param dbName =  'tunnistamo'
param dbServerName =  '${prefix}-db'
param dbAdminUsername =  'turkuadmin'
param dbUsername =  (isProduction) ? 'tunnistamo-prod' : 'tunnistamo-qa'
param keyvaultName =  '${prefix}kv'
param serverfarmPlanName =  'serviceplan'
param storageAccountName =  '${sanitizedPrefix}sa'
param apiOutboundIpName = (isProduction) ? 'turku-prod-tunnistamo-outbound-ip' : 'turku-test-tunnistamo-outbound-ip'
param natGatewayName = '${prefix}-nat'
param vnetName =  '${prefix}-vnet'
param workspaceName = '${prefix}-workspace'
