resource "azurerm_application_insights" "appinsight" {

  name                = "${var.app_name}-insights"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "other"

}