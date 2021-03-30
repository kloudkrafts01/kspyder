resource "azurerm_app_service_plan" "appsvc" {

  name                = "appsvc-${var.name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "Linux"
  reserved            = true

  sku {
    tier = var.app_tier
    size = var.app_sku
  }
}

resource "azurerm_function_app" "appfunc" {

  name                       = var.app_name
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  app_service_plan_id        = azurerm_app_service_plan.appsvc.id
  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key
  enabled                    = true
  os_type                    = "linux"
  # this parameter is badly needed, otherwise function runtime will not work
  version                    = "~3"

  # assign a system-managed Service Principal
  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "KSPYDER_ENVIRONMENT" = "prod"
    "KSPYDER_CONF" = var.name
    "AZURE_VAULT_NAME" = azurerm_key_vault.kvault.name
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = true
    "WEBSITE_ENABLE_SYNC_UPDATE_SITE" = true
    "WEBSITE_RUN_FROM_PACKAGE" = "1"
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.appinsight.instrumentation_key
    # setting to force the app to route all in/out traffic through the associated VNET; Useful to get a static outbound IP (see network submodule)
    "WEBSITE_VNET_ROUTE_ALL" = "1"
  }

  site_config {
    linux_fx_version= "Python|${var.python_version}"        
    ftps_state = "Disabled"
    use_32_bit_worker_process = false
    always_on = true
  }

  tags = {
    purpose = var.name
  }

}

resource "azurerm_function_app_slot" "dev-appslot" {

  # Create one dev App Slot : the Default slot will be the Production slot

  name                       = "dev"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  app_service_plan_id        = azurerm_app_service_plan.appsvc.id
  function_app_name          = azurerm_function_app.appfunc.name
  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key
  os_type                    = "linux"
  version                    = "~3"
  enabled                    = true

  app_settings = {
    "KSPYDER_ENVIRONMENT" = "dev"
    "KSPYDER_CONF" = var.name
    "AZURE_VAULT_NAME" = azurerm_key_vault.kvault.name
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = true
    "WEBSITE_ENABLE_SYNC_UPDATE_SITE" = true
    "WEBSITE_RUN_FROM_PACKAGE" = "1"
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.appinsight.instrumentation_key
    # setting to force the app to route all in/out traffic through the associated VNET; Useful to get a static outbound IP (see network submodule)
    "WEBSITE_VNET_ROUTE_ALL" = "1"
  }

  # assign a system-managed Service Principal
  identity {
    type = "SystemAssigned"
  }

  tags = {
    env = "dev"
  }

}