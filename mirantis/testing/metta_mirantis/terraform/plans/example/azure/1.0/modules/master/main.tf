resource "random_string" "pub_ip_salt" {
  count   = 1
  length  = 4
  special = false

  keepers = {
    deployment = var.cluster_name
  }
}

#####
# NSG for Masters
#####
resource azurerm_network_security_group "master_nsg" {
  name                = "${var.cluster_name}-master-nsg"
  location            = var.location
  resource_group_name = var.rg

  tags = merge(
    tomap({
      "Name" = format("%s-master-nsg", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# Rules for master NSG
#####
resource "azurerm_network_security_rule" "master_22" {
  name                        = "port_22_tcp"
  description                 = "Allow 22 tcp for master"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "22"
  destination_address_prefix  = "*"
  resource_group_name         = var.rg
  network_security_group_name = azurerm_network_security_group.master_nsg.name
}

resource "azurerm_network_security_rule" "master_443" {
  name                        = "port_443_tcp"
  description                 = "Allow 443 tcp for master"
  priority                    = 110
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "443"
  destination_address_prefix  = "*"
  resource_group_name         = var.rg
  network_security_group_name = azurerm_network_security_group.master_nsg.name
}

resource "azurerm_network_security_rule" "master_6443" {
  name                        = "port_6443_tcp"
  description                 = "Allow 6443 tcp for master"
  priority                    = 120
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "6443"
  destination_address_prefix  = "*"
  resource_group_name         = var.rg
  network_security_group_name = azurerm_network_security_group.master_nsg.name
}

#####
# Master LB
#####
resource "azurerm_lb" "master_public_lb" {
  name                = format("%s-mke-LB", var.cluster_name)
  location            = var.location
  resource_group_name = var.rg

  frontend_ip_configuration {
    name                 = "mke-LB-FrontendIP"
    public_ip_address_id = join("", azurerm_public_ip.mke_lb_pub_ip.*.id)
  }

  tags = merge(
    tomap({
      "Name" = format("%s-mke-LB", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

# create the load balancer backend pool
resource "azurerm_lb_backend_address_pool" "mke_lb_be_pool" {
  name                = "${var.cluster_name}-mke-be-pool"
  resource_group_name = var.rg
  loadbalancer_id     = azurerm_lb.master_public_lb.id
}

# Associate the provided network interfaces with this backend pool
resource "azurerm_network_interface_backend_address_pool_association" "mke_lb_be_pool_assoc" {
  count                   = length(azurerm_network_interface.netif_public)
  network_interface_id    = azurerm_network_interface.netif_public[count.index].id
  ip_configuration_name   = format("%s-master-Net-%s", var.cluster_name, count.index + 1)
  backend_address_pool_id = azurerm_lb_backend_address_pool.mke_lb_be_pool.id
}

# Add a health check probe for the backend instances
resource "azurerm_lb_probe" "mke_lb_probe_443" {
  resource_group_name = var.rg
  loadbalancer_id     = azurerm_lb.master_public_lb.id
  name                = "probe_mke_443"
  protocol            = "TCP"
  port                = 443
  interval_in_seconds = 5
  number_of_probes    = 2
}

resource "azurerm_lb_probe" "mke_lb_probe_6443" {
  resource_group_name = var.rg
  loadbalancer_id     = azurerm_lb.master_public_lb.id
  name                = "probe_mke_6443"
  protocol            = "TCP"
  port                = 6443
  interval_in_seconds = 5
  number_of_probes    = 2
}

# Add rules for the master loadbalancer
resource "azurerm_lb_rule" "mke_lb_rule_443" {
  resource_group_name            = var.rg
  loadbalancer_id                = azurerm_lb.master_public_lb.id
  name                           = format("%s-mke-443-443", var.cluster_name)
  protocol                       = "TCP"
  frontend_port                  = 443
  backend_port                   = 443
  frontend_ip_configuration_name = "mke-LB-FrontendIP"
  enable_floating_ip             = false
  backend_address_pool_id        = azurerm_lb_backend_address_pool.mke_lb_be_pool.id
  idle_timeout_in_minutes        = 5
  probe_id                       = azurerm_lb_probe.mke_lb_probe_443.id
}

resource "azurerm_lb_rule" "mke_lb_rule_6443" {
  resource_group_name            = var.rg
  loadbalancer_id                = azurerm_lb.master_public_lb.id
  name                           = format("%s-mke-6443-6443", var.cluster_name)
  protocol                       = "TCP"
  frontend_port                  = 6443
  backend_port                   = 6443
  frontend_ip_configuration_name = "mke-LB-FrontendIP"
  enable_floating_ip             = false
  backend_address_pool_id        = azurerm_lb_backend_address_pool.mke_lb_be_pool.id
  idle_timeout_in_minutes        = 5
  probe_id                       = azurerm_lb_probe.mke_lb_probe_6443.id
}

# Add public ip for master loadbalancer
resource "azurerm_public_ip" "mke_lb_pub_ip" {
  name                = "mke-LB-FrontendIP"
  location            = var.location
  resource_group_name = var.rg

  allocation_method = "Static"
  domain_name_label = format("mke-%s-%s", lower(replace(var.rg, "/[^a-zA-Z0-9]/", "")), lower(random_string.pub_ip_salt[0].result))

  tags = merge(
    tomap({
      "Name" = "mke-LB-FrontendIP",
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# Network Interfaces for VMs
#####
resource "azurerm_network_interface" "netif_public" {
  count               = var.master_count
  name                = format("%s-master-Net-%s", var.cluster_name, count.index + 1)
  location            = var.location
  resource_group_name = var.rg

  ip_configuration {
    name      = format("%s-master-Net-%s", var.cluster_name, count.index + 1)
    subnet_id = var.subnet_id

    public_ip_address_id          = azurerm_public_ip.master_public_ips[count.index].id
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
      "Name" = format("%s-master-Net-%s", var.cluster_name, count.index + 1),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

resource "azurerm_network_interface_security_group_association" "master" {
  count                     = length(azurerm_network_interface.netif_public)
  network_interface_id      = azurerm_network_interface.netif_public[count.index].id
  network_security_group_id = azurerm_network_security_group.master_nsg.id
}

#####
# Public IP addressing for VMs
#####
resource "azurerm_public_ip" "master_public_ips" {
  count               = var.master_count
  name                = format("%s-master-PublicIP-%d", var.cluster_name, count.index + 1)
  location            = var.location
  resource_group_name = var.rg
  allocation_method   = "Static"

  tags = merge(
    tomap({
      "Name" = format("%s-master-PublicIP-%d", var.cluster_name, count.index + 1),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# AVSet for master
# NOTE: The number of Fault & Update Domains varies depending on which Azure Region you're using.
#####
resource "azurerm_availability_set" "master_avset" {
  name                         = "${var.cluster_name}-master"
  location                     = var.location
  resource_group_name          = var.rg
  platform_fault_domain_count  = var.fault_domain_count
  platform_update_domain_count = var.update_domain_count
  managed                      = true
  tags = merge(
    tomap({
      "Name" = format("%s-master-avset", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# Master VMs
#####
resource "azurerm_virtual_machine" "mke_master" {
  count = var.master_count

  name                = format("%s%03d", "master-", (count.index + 1))
  location            = var.location
  resource_group_name = var.rg
  vm_size             = var.master_type

  network_interface_ids        = [azurerm_network_interface.netif_public[count.index].id]
  primary_network_interface_id = azurerm_network_interface.netif_public[count.index].id

  availability_set_id = azurerm_availability_set.master_avset.id

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
    name              = format("%s%03d-OSDisk", "master-", (count.index + 1))
    create_option     = "FromImage"
    caching           = "None"
    disk_size_gb      = var.master_os_volume_size
    managed_disk_type = "Premium_LRS"
  }

  storage_data_disk {
    name              = format("%s%03d-DataDisk", "master-", (count.index + 1))
    create_option     = "Empty"
    lun               = 0
    caching           = "None"
    disk_size_gb      = var.master_data_volume_size
    managed_disk_type = "Standard_LRS"
  }

  os_profile {
    computer_name  = format("%s%03d", "master-", (count.index + 1))
    admin_username = "ubuntu"
    custom_data    = <<-EOF
#cloud-config
bootcmd:
 - >
   echo 'network: {config: disabled}' > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
EOF
  }

  os_profile_linux_config {
    disable_password_authentication = true

    ssh_keys {
      path     = "/home/ubuntu/.ssh/authorized_keys"
      key_data = var.ssh_key.public_key_openssh
    }
  }

  lifecycle {
    ignore_changes = [
      tags
    ]
  }

  tags = merge(
    tomap({
      "Name" = format("%s%03d", "master-", (count.index + 1)),
      "Environment" = format("%s", var.rg),
      "Role" = "master",
    }),
    var.tags
  )
}
