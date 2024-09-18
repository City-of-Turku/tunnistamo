using 'template-certs-keyvault.bicep'

var prefix = readEnvironmentVariable('RESOURCE_PREFIX')
param keyvaultName =  '${prefix}kv'
