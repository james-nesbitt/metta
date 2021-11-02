output "lb_dns_name" {
  value = azurerm_public_ip.mke_lb_pub_ip.fqdn
}

output "public_ips" {
  value = azurerm_public_ip.master_public_ips.*.ip_address
}

output "machines" {
  value = azurerm_virtual_machine.mke_master
}
