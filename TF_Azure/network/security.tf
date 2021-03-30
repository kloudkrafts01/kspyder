resource "azurerm_network_security_group" "nsg" {
  name                = "nsg-${var.name}"
  location            = var.rg.location
  resource_group_name = var.rg.name
}

resource "azurerm_network_security_rule" "in_rule" {

  for_each = { for rule in var.inbound_rules : rule.reason => [rule.IP, rule.priority]}

  priority                    = each.value[1]
  name                        = each.key
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "*"
  source_address_prefix       = each.value[0]
  destination_address_prefix  = "*"
  resource_group_name         = var.rg.name
  network_security_group_name = azurerm_network_security_group.nsg.name
}

resource "azurerm_subnet_network_security_group_association" "subnet_nsg_assoc" {

  subnet_id                 = azurerm_subnet.subnet.id
  network_security_group_id = azurerm_network_security_group.nsg.id
  
}