output "public_ips" {
  value = azurerm_public_ip.win_worker_public_ips.*.ip_address
}

output "machines" {
  value = azurerm_virtual_machine.win_worker
}

output "windows_password" {
  value = local.password
}
