resource "azurerm_nat_gateway" "nat" {
  name                = "nat-${var.name}"
  location            = var.rg.location
  resource_group_name = var.rg.name
  sku_name            = var.nat_sku
}

resource "azurerm_subnet_nat_gateway_association" "nat_subnet" {
  
  subnet_id      = azurerm_subnet.subnet.id
  nat_gateway_id = azurerm_nat_gateway.nat.id

}

resource "azurerm_public_ip" "ip" {

  name                = "ip-${var.name}"
  resource_group_name = var.rg.name
  location            = var.rg.location
  allocation_method   = "Static"
  sku                 = var.ip_sku

}

resource "azurerm_nat_gateway_public_ip_association" "nat_ip" {
  
  nat_gateway_id       = azurerm_nat_gateway.nat.id
  public_ip_address_id = azurerm_public_ip.ip.id
  
}