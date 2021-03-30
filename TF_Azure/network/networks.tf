resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-${var.name}"
  location            = var.rg.location
  resource_group_name = var.rg.name
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "subnet" {
  
  name                 = "subnet-main"
  resource_group_name  = var.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]

  # service endpoints to allow internal access from Azure services
  service_endpoints = [
    "Microsoft.AzureActiveDirectory",
    "Microsoft.KeyVault",
    "Microsoft.Sql",
    "Microsoft.Storage"
  ]

  # Add service delegation so the subnet can be associated to Azure functions
  delegation {
    name = "delegation"

    service_delegation {
      name    = "Microsoft.Web/serverFarms"
    }
  }

}

resource "azurerm_subnet_service_endpoint_storage_policy" "subnet_storage_policy" {
  name                = "subnet_storage_policy"
  resource_group_name = var.rg.name
  location            = var.rg.location
  definition {
    name        = "policy"
    description = "Policy to associate subnet service endpoint to storage account"
    service_resources = [
      var.rg.id,
      var.storage.id
    ]
  }
}

# Associate the db server to teh main subnet
resource "azurerm_sql_virtual_network_rule" "sqlvnetrule" {
  
  name                = "sql-vnet-rule-main"
  resource_group_name = var.rg.name
  server_name         = var.sqlserver_name
  subnet_id           = azurerm_subnet.subnet.id
}

# Associate the App Service to the vnet so the traffic in and out of Azure functions goes through the NAT gateway

resource "azurerm_app_service_virtual_network_swift_connection" "app_vnet_co" {
  app_service_id = var.function_app_id
  subnet_id      = azurerm_subnet.subnet.id
}