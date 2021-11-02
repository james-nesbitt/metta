
#####
# Create new SSH Key
#
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = "4096"
}

resource "local_file" "ssh_public_key" {
  content  = tls_private_key.ssh_key.private_key_pem
  filename = "ssh_keys/${var.cluster_name}.pem"
  provisioner "local-exec" {
    command = "chmod 0600 ${local_file.ssh_public_key.filename}"
  }
}

#####
# Cluster wide NSG
#####
resource azurerm_network_security_group "cluster_nsg" {
  name                = "${var.cluster_name}-cluster-nsg"
  location            = var.location
  resource_group_name = var.rg

  tags = merge(
    tomap({
      "Name" = format("%s-cluster-nsg", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

# associate network security group for the cluster to the subnet
resource azurerm_subnet_network_security_group_association "cluster_subnet_nsg" {
  subnet_id                 = var.subnet_id
  network_security_group_id = azurerm_network_security_group.cluster_nsg.id
}

#####
# Rules for master NSG
#####
resource "azurerm_network_security_rule" "cluster" {
  name                        = "allow"
  description                 = "Allow all"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "*"
  destination_address_prefix  = "*"
  resource_group_name         = var.rg
  network_security_group_name = azurerm_network_security_group.cluster_nsg.name
}

#####
# Storage account for kubernetes
#####
resource "azurerm_storage_account" "kubernetes_storage" {
  name                     = format("%skube", substr(replace(lower(var.cluster_name), "-", ""), 0, 23))
  resource_group_name      = var.rg
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = merge(
    tomap({
      "Name" = format("%s-kube-storage", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}
