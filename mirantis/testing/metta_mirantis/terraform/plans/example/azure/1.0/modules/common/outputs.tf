output "cluster_nsg_id" {
  value = azurerm_network_security_group.cluster_nsg.id
}

output "ssh_key" {
  value = tls_private_key.ssh_key
}
