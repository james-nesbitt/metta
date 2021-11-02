output "lb_dns_name" {
  value = azurerm_public_ip.worker_lb_pub_ip.fqdn
}

output "public_ips" {
  value = azurerm_public_ip.worker_public_ips.*.ip_address
}

output "machines" {
  value = azurerm_virtual_machine.worker
}
