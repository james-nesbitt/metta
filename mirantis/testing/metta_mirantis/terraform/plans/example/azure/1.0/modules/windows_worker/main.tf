resource "random_string" "windows_password" {
  length      = 16
  special     = false
  min_upper   = 1
  min_lower   = 1
  min_numeric = 1

  keepers = {
    deployment = var.cluster_name
  }
}

locals {
  password = "${random_string.windows_password.result}mT4!"
}

#####
# NSG for window workers
#####
resource azurerm_network_security_group "win_worker_nsg" {
  name                = "${var.cluster_name}-win-worker-nsg"
  location            = var.location
  resource_group_name = var.rg

  tags = merge(
    tomap({
      "Name" = format("%s-win-worker-nsg", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# Rules for window worker NSG
#####
resource "azurerm_network_security_rule" "win_worker_3389" {
  name                        = "port_3389_tcp"
  description                 = "Allow 3389 tcp for win-worker"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "3389"
  destination_address_prefix  = "*"
  resource_group_name         = var.rg
  network_security_group_name = azurerm_network_security_group.win_worker_nsg.name
}

resource "azurerm_network_security_rule" "win_worker_5986" {
  name                        = "port_5986_tcp"
  description                 = "Allow 5986 tcp for win-worker"
  priority                    = 110
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "5986"
  destination_address_prefix  = "*"
  resource_group_name         = var.rg
  network_security_group_name = azurerm_network_security_group.win_worker_nsg.name
}

#####
# Network Interfaces for VMs
#####
resource "azurerm_network_interface" "netif_public" {
  count               = var.worker_count
  name                = format("%s-win-worker-Net-%s", var.cluster_name, count.index + 1)
  location            = var.location
  resource_group_name = var.rg

  ip_configuration {
    name      = format("%s-win-worker-Net-%s", var.cluster_name, count.index + 1)
    subnet_id = var.subnet_id

    public_ip_address_id          = azurerm_public_ip.win_worker_public_ips[count.index].id
    private_ip_address_allocation = "Dynamic"
    primary                       = true
  }

  lifecycle {
    ignore_changes = [
      ip_configuration,
    ]
  }

  tags = merge(
    tomap({
      "Name" = format("%s-win-worker-Net-%s", var.cluster_name, count.index + 1),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

resource "azurerm_network_interface_security_group_association" "win-worker" {
  count                     = length(azurerm_network_interface.netif_public)
  network_interface_id      = azurerm_network_interface.netif_public[count.index].id
  network_security_group_id = azurerm_network_security_group.win_worker_nsg.id
}

#####
# Public IP addressing for VMs
#####
resource "azurerm_public_ip" "win_worker_public_ips" {
  count               = var.worker_count
  name                = format("%s-win-worker-PublicIP-%d", var.cluster_name, count.index + 1)
  location            = var.location
  resource_group_name = var.rg
  allocation_method   = "Static"

  tags = merge(
    tomap({
      "Name" = format("%s-win-worker-PublicIP-%d", var.cluster_name, count.index + 1),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# AVSet for win-worker
# NOTE: The number of Fault & Update Domains varies depending on which Azure Region you're using.
#####
resource "azurerm_availability_set" "win_worker_avset" {
  name                         = "${var.cluster_name}-win-worker"
  location                     = var.location
  resource_group_name          = var.rg
  platform_fault_domain_count  = var.fault_domain_count
  platform_update_domain_count = var.update_domain_count
  managed                      = true
  tags = merge(
    tomap({
      "Name" = format("%s-win-worker-avset", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# Windows Worker VMs
#####
resource "azurerm_virtual_machine" "win_worker" {
  count = var.worker_count

  name                = format("%s%03d", "win-worker-", (count.index + 1))
  location            = var.location
  resource_group_name = var.rg
  vm_size             = var.worker_type

  network_interface_ids        = [azurerm_network_interface.netif_public[count.index].id]
  primary_network_interface_id = azurerm_network_interface.netif_public[count.index].id

  availability_set_id = azurerm_availability_set.win_worker_avset.id

  # Uncomment this line to delete the data disks automatically when deleting the VM
  delete_data_disks_on_termination = true
  delete_os_disk_on_termination    = true

  storage_image_reference {
    publisher = var.image["publisher"]
    offer     = var.image["offer"]
    sku       = var.image["sku"]
    version   = var.image["version"]
  }

  storage_os_disk {
    name              = format("%s%03d-OSDisk", "win-worker-", (count.index + 1))
    create_option     = "FromImage"
    caching           = "None"
    managed_disk_type = "Premium_LRS"
  }

  storage_data_disk {
    name              = format("%s%03d-DataDisk", "win-worker-", (count.index + 1))
    create_option     = "Empty"
    lun               = 0
    caching           = "None"
    disk_size_gb      = var.worker_data_volume_size
    managed_disk_type = "Standard_LRS"
  }

  os_profile {
    computer_name  = format("%s%03d", "win-worker-", (count.index + 1))
    admin_username = var.username
    admin_password = local.password
    custom_data    = <<EOF
# Set Administrator password
([adsi]("WinNT://./administrator, user")).SetPassword("${local.password}")

# Snippet to enable WinRM over HTTPS with a self-signed certificate
# from https://gist.github.com/TechIsCool/d65017b8427cfa49d579a6d7b6e03c93
Write-Output "Disabling WinRM over HTTP..."
Disable-NetFirewallRule -Name "WINRM-HTTP-In-TCP"
Disable-NetFirewallRule -Name "WINRM-HTTP-In-TCP-PUBLIC"
Get-ChildItem WSMan:\Localhost\listener | Remove-Item -Recurse

Write-Output "Configuring WinRM for HTTPS..."
Set-Item -Path WSMan:\LocalHost\MaxTimeoutms -Value '1800000'
Set-Item -Path WSMan:\LocalHost\Shell\MaxMemoryPerShellMB -Value '1024'
Set-Item -Path WSMan:\LocalHost\Service\AllowUnencrypted -Value 'false'
Set-Item -Path WSMan:\LocalHost\Service\Auth\Basic -Value 'true'
Set-Item -Path WSMan:\LocalHost\Service\Auth\CredSSP -Value 'true'

New-NetFirewallRule -Name "WINRM-HTTPS-In-TCP" `
    -DisplayName "Windows Remote Management (HTTPS-In)" `
    -Description "Inbound rule for Windows Remote Management via WS-Management. [TCP 5986]" `
    -Group "Windows Remote Management" `
    -Program "System" `
    -Protocol TCP `
    -LocalPort "5986" `
    -Action Allow `
    -Profile Domain,Private

New-NetFirewallRule -Name "WINRM-HTTPS-In-TCP-PUBLIC" `
    -DisplayName "Windows Remote Management (HTTPS-In)" `
    -Description "Inbound rule for Windows Remote Management via WS-Management. [TCP 5986]" `
    -Group "Windows Remote Management" `
    -Program "System" `
    -Protocol TCP `
    -LocalPort "5986" `
    -Action Allow `
    -Profile Public

$Hostname = [System.Net.Dns]::GetHostByName((hostname)).HostName.ToUpper()
$pfx = New-SelfSignedCertificate -CertstoreLocation Cert:\LocalMachine\My -DnsName $Hostname
$certThumbprint = $pfx.Thumbprint
$certSubjectName = $pfx.SubjectName.Name.TrimStart("CN = ").Trim()

New-Item -Path WSMan:\LocalHost\Listener -Address * -Transport HTTPS -Hostname $certSubjectName -CertificateThumbPrint $certThumbprint -Port "5986" -force

Write-Output "Restarting WinRM Service..."
Stop-Service WinRM
Set-Service WinRM -StartupType "Automatic"
Start-Service WinRM
EOF
  }

  os_profile_windows_config {
    provision_vm_agent        = true
    enable_automatic_upgrades = true
  }

  tags = merge(
    tomap({
      "Name" = format("%s%03d", "win-worker-", (count.index + 1)),
      "Environment" = format("%s", var.rg),
      "Role" = "worker",
    }),
    var.tags
  )
}

resource "azurerm_virtual_machine_extension" "startup" {
  count                = var.worker_count
  name                 = format("%s%03d", "win-worker-", (count.index + 1))
  virtual_machine_id   = element(azurerm_virtual_machine.win_worker.*.id, count.index)
  publisher            = "Microsoft.Compute"
  type                 = "CustomScriptExtension"
  type_handler_version = "1.8"

  settings = <<SETTINGS
  {
    "commandToExecute": "powershell -ExecutionPolicy unrestricted -NoProfile -NonInteractive -command \"cp c:/azuredata/customdata.bin c:/azuredata/install.ps1; c:/azuredata/install.ps1\""
  }
SETTINGS
}
