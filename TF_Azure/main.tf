# Configure the Azure provider
terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = ">= 2.26"
    }
  }
}

provider "azurerm" {
  features {}
}

# uncomment to use more elaborate networking resources
module "network"{
  source = "./network"
  
  # passing all relevant variables to the submodule
  rg = azurerm_resource_group.rg
  storage = azurerm_storage_account.storage
  sqlserver_name = azurerm_mssql_server.msql.name
  name = var.name
  app_name = var.app_name
  function_app_id = azurerm_function_app.appfunc.id
  env = var.env
  subnet_idx = var.subnet_idx
  inbound_rules = var.inbound_rules
  nat_sku = var.nat_sku
  ip_sku = var.ip_sku
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.name}"
  location = var.location

  tags = {
      purpose = var.name
  }
}

resource "azurerm_storage_account" "storage" {
  name                     = "storage${var.name}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = var.storage_tier
  account_replication_type = "LRS"
}