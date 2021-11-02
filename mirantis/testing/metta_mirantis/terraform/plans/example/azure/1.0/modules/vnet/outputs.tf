output "rg" {
  value = azurerm_resource_group.rg.name
}

output "id" {
  value = azurerm_virtual_network.vnet.id
}

output "subnet_name" {
  value = azurerm_subnet.subnet.name
}

output "subnet_id" {
  value = azurerm_subnet.subnet.id
}
