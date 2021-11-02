#####
# Resource Group
#####
resource "azurerm_resource_group" "rg" {
  name     = "${var.cluster_name}-rg"
  location = var.location

  tags = merge(
    tomap({
      "Name" = format("%s-rg", var.cluster_name)
    }),
    var.tags
  )

  lifecycle {
    ignore_changes = [tags]
  }
}

##### 
# Network VNET, Subnet
#####
resource "azurerm_virtual_network" "vnet" {
  name                = "${var.cluster_name}-vnet"
  location            = var.location
  address_space       = [var.host_cidr]
  resource_group_name = azurerm_resource_group.rg.name

  tags = merge(
    tomap({
      "Name" = format("%s-vnet", var.cluster_name),
      "Environment" = format("%s", azurerm_resource_group.rg.name)
    }),
    var.tags
  )
}

resource "azurerm_subnet" "subnet" {
  name                 = "${var.cluster_name}-subnet"
  virtual_network_name = azurerm_virtual_network.vnet.name
  resource_group_name  = azurerm_resource_group.rg.name
  address_prefixes     = [var.subnet_cidr]
}
