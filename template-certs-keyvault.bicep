param location string = resourceGroup().location
@description('Key vault name. Must be globally unique. Lowercase and numbers only')
@maxLength(24)
@minLength(3)
param keyvaultName string

var goforeIps = {
  goforeKamppi: '81.175.255.179' // Gofore Kamppi egress
  goforeTampere: '82.141.89.43' // Gofore Tampere egress
  goforeVpn: '80.248.248.85' // Gofore VPN egress
}
var goforeNetworkAcls = {
  bypass: 'AzureServices'
  defaultAction: 'Deny'
  ipRules: map(items(goforeIps), ip => {
    value: ip.value
  })
}

resource keyvault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyvaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enabledForDeployment: true
    enabledForDiskEncryption: true
    enabledForTemplateDeployment: true
    enableRbacAuthorization: true
    enablePurgeProtection: true
    enableSoftDelete: true
    publicNetworkAccess: 'Enabled'
    networkAcls: goforeNetworkAcls
  }
}

@description('Key Vault Certificate User role')
resource keyvaultCertificateUserRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: resourceGroup()
  name: 'db79e9a7-68ee-4b58-9aeb-b90e7c24fcba'
}

@description('Grant the app service identity with key vault certificate user role permissions over the key vault. This lets Web Apps import certificates')
resource appServiceKeyvaultCertificateUserRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyvault
  name: guid(resourceGroup().id, '56dbcac3-c151-426b-b977-108e783be732', 'Key Vault Certificate User')
  properties: {
    roleDefinitionId: keyvaultCertificateUserRoleDefinition.id
    principalId: '56dbcac3-c151-426b-b977-108e783be732'
    principalType: 'ServicePrincipal'
  }
}
