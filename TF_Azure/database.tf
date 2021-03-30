resource "azurerm_mssql_server" "msql" {
  name                         = var.name
  resource_group_name          = azurerm_resource_group.rg.name
  location                     = azurerm_resource_group.rg.location
  version                      = "12.0"
  administrator_login          = var.admin_username
  administrator_login_password = var.admin_password
  minimum_tls_version          = "1.2"

  # assign AD administrator
  azuread_administrator {
    login_username = var.aad_admin
    object_id      = var.aad_admin_id
  }

  tags = {
    purpose = var.name
  }
}

resource "azurerm_mssql_server_extended_auditing_policy" "serverauditpolicy" {
  server_id                               = azurerm_mssql_server.msql.id
  storage_endpoint                        = azurerm_storage_account.storage.primary_blob_endpoint
  storage_account_access_key              = azurerm_storage_account.storage.primary_access_key
  storage_account_access_key_is_secondary = true
  retention_in_days                       = 6
}

resource "azurerm_mssql_database" "db" {

  # will create two identical database instances : DEV and PROD
  for_each = var.db_sku

  name           = "${var.name}-${each.key}"
  server_id      = azurerm_mssql_server.msql.id
  sku_name       = each.value

  long_term_retention_policy {
      monthly_retention = "P1Y"
      week_of_year      = 1
      weekly_retention  = "P1M"
      yearly_retention  = "P5Y"
  }

  short_term_retention_policy {
      retention_days = 7
  }

  tags = {
    env = each.key
    purpose = var.name
    type = "mssql"
  }

}

resource "azurerm_mssql_firewall_rule" "mssql_FW_rule" {
  
  for_each = { for rule in var.inbound_rules : rule.reason => [rule.IP, rule.priority]}
  
  name             = each.key
  server_id        = azurerm_mssql_server.msql.id
  start_ip_address = each.value[0]
  end_ip_address   = each.value[0]
  
}