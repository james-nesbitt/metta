resource "random_string" "pub_ip_salt" {
  count   = 1
  length  = 4
  special = false

  keepers = {
    deployment = var.cluster_name
  }
}

#####
# NSG for Workers
#####
resource azurerm_network_security_group "worker_nsg" {
  name                = "${var.cluster_name}-worker-nsg"
  location            = var.location
  resource_group_name = var.rg

  tags = merge(
    tomap({
      "Name" = format("%s-worker-nsg", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# Rules for worker NSG
#####
resource "azurerm_network_security_rule" "worker_22" {
  name                        = "port_22_tcp"
  description                 = "Allow 22 tcp for worker"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "22"
  destination_address_prefix  = "*"
  resource_group_name         = var.rg
  network_security_group_name = azurerm_network_security_group.worker_nsg.name
}

resource "azurerm_network_security_rule" "worker_8080" {
  name                        = "port_8080_tcp"
  description                 = "Allow 8080 tcp for worker"
  priority                    = 110
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "8080"
  destination_address_prefix  = "*"
  resource_group_name         = var.rg
  network_security_group_name = azurerm_network_security_group.worker_nsg.name
}

resource "azurerm_network_security_rule" "worker_8443" {
  name                        = "port_8443_tcp"
  description                 = "Allow 8443 tcp for worker"
  priority                    = 120
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "8443"
  destination_address_prefix  = "*"
  resource_group_name         = var.rg
  network_security_group_name = azurerm_network_security_group.worker_nsg.name
}

#####
# Workers LB
#####
resource "azurerm_lb" "worker_public_lb" {
  name                = format("%s-worker-LB", var.cluster_name)
  location            = var.location
  resource_group_name = var.rg

  frontend_ip_configuration {
    name                 = "worker-LB-FrontendIP"
    public_ip_address_id = join("", azurerm_public_ip.worker_lb_pub_ip.*.id)
  }

  tags = merge(
    tomap({
      "Name" = format("%s-worker-LB", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

# create the load balancer backend pool
resource "azurerm_lb_backend_address_pool" "worker_lb_be_pool" {
  name                = "${var.cluster_name}-worker-be-pool"
  resource_group_name = var.rg
  loadbalancer_id     = azurerm_lb.worker_public_lb.id
}

# Associate the provided network interfaces with this backend pool
resource "azurerm_network_interface_backend_address_pool_association" "worker_lb_be_pool_assoc" {
  count                   = length(azurerm_network_interface.netif_public)
  network_interface_id    = azurerm_network_interface.netif_public[count.index].id
  ip_configuration_name   = format("%s-worker-Net-%s", var.cluster_name, count.index + 1)
  backend_address_pool_id = azurerm_lb_backend_address_pool.worker_lb_be_pool.id
}

# Add a health check probe for the backend instances
resource "azurerm_lb_probe" "worker_lb_probe_8080" {
  resource_group_name = var.rg
  loadbalancer_id     = azurerm_lb.worker_public_lb.id
  name                = "probe_worker_8080"
  protocol            = "TCP"
  port                = 8080
  interval_in_seconds = 5
  number_of_probes    = 2
}

resource "azurerm_lb_probe" "worker_lb_probe_8443" {
  resource_group_name = var.rg
  loadbalancer_id     = azurerm_lb.worker_public_lb.id
  name                = "probe_worker_8443"
  protocol            = "TCP"
  port                = 8443
  interval_in_seconds = 5
  number_of_probes    = 2
}

# Add rules for the worker loadbalancer
resource "azurerm_lb_rule" "worker_lb_rule_8080" {
  resource_group_name            = var.rg
  loadbalancer_id                = azurerm_lb.worker_public_lb.id
  name                           = format("%s-worker-8080-8080", var.cluster_name)
  protocol                       = "TCP"
  frontend_port                  = 8080
  backend_port                   = 8080
  frontend_ip_configuration_name = "worker-LB-FrontendIP"
  enable_floating_ip             = false
  backend_address_pool_id        = azurerm_lb_backend_address_pool.worker_lb_be_pool.id
  idle_timeout_in_minutes        = 5
  probe_id                       = azurerm_lb_probe.worker_lb_probe_8080.id
}

resource "azurerm_lb_rule" "worker_lb_rule_8443" {
  resource_group_name            = var.rg
  loadbalancer_id                = azurerm_lb.worker_public_lb.id
  name                           = format("%s-worker-8443-8443", var.cluster_name)
  protocol                       = "TCP"
  frontend_port                  = 8443
  backend_port                   = 8443
  frontend_ip_configuration_name = "worker-LB-FrontendIP"
  enable_floating_ip             = false
  backend_address_pool_id        = azurerm_lb_backend_address_pool.worker_lb_be_pool.id
  idle_timeout_in_minutes        = 5
  probe_id                       = azurerm_lb_probe.worker_lb_probe_8443.id
}

# Add public ip for worker loadbalancer
resource "azurerm_public_ip" "worker_lb_pub_ip" {
  name                = "worker-LB-FrontendIP"
  location            = var.location
  resource_group_name = var.rg

  allocation_method = "Static"
  domain_name_label = format("worker-%s-%s", lower(replace(var.rg, "/[^a-zA-Z0-9]/", "")), lower(random_string.pub_ip_salt[0].result))

  tags = merge(
    tomap({
      "Name" = "worker-LB-FrontendIP",
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# Network Interfaces for VMs
#####
resource "azurerm_network_interface" "netif_public" {
  count               = var.worker_count
  name                = format("%s-worker-Net-%s", var.cluster_name, count.index + 1)
  location            = var.location
  resource_group_name = var.rg

  ip_configuration {
    name      = format("%s-worker-Net-%s", var.cluster_name, count.index + 1)
    subnet_id = var.subnet_id

    public_ip_address_id          = azurerm_public_ip.worker_public_ips[count.index].id
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
      "Name" = format("%s-worker-Net-%s", var.cluster_name, count.index + 1),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

resource "azurerm_network_interface_security_group_association" "worker" {
  count                     = length(azurerm_network_interface.netif_public)
  network_interface_id      = azurerm_network_interface.netif_public[count.index].id
  network_security_group_id = azurerm_network_security_group.worker_nsg.id
}

#####
# Public IP addressing for VMs
#####
resource "azurerm_public_ip" "worker_public_ips" {
  count               = var.worker_count
  name                = format("%s-worker-PublicIP-%d", var.cluster_name, count.index + 1)
  location            = var.location
  resource_group_name = var.rg
  allocation_method   = "Static"

  tags = merge(
    tomap({
      "Name" = format("%s-worker-PublicIP-%d", var.cluster_name, count.index + 1),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# AVSet for worker
# NOTE: The number of Fault & Update Domains varies depending on which Azure Region you're using.
#####
resource "azurerm_availability_set" "worker_avset" {
  name                         = "${var.cluster_name}-worker"
  location                     = var.location
  resource_group_name          = var.rg
  platform_fault_domain_count  = var.fault_domain_count
  platform_update_domain_count = var.update_domain_count
  managed                      = true
  tags = merge(
    tomap({
      "Name" = format("%s-worker-avset", var.cluster_name),
      "Environment" = format("%s", var.rg)
    }),
    var.tags
  )
}

#####
# Worker VMs
#####
resource "azurerm_virtual_machine" "worker" {
  count = var.worker_count

  name                = format("%s%03d", "worker-", (count.index + 1))
  location            = var.location
  resource_group_name = var.rg
  vm_size             = var.worker_type

  network_interface_ids        = [azurerm_network_interface.netif_public[count.index].id]
  primary_network_interface_id = azurerm_network_interface.netif_public[count.index].id

  availability_set_id = azurerm_availability_set.worker_avset.id

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
    name              = format("%s%03d-OSDisk", "worker-", (count.index + 1))
    create_option     = "FromImage"
    caching           = "None"
    disk_size_gb      = var.worker_os_volume_size
    managed_disk_type = "Premium_LRS"
  }

  storage_data_disk {
    name              = format("%s%03d-DataDisk", "worker-", (count.index + 1))
    create_option     = "Empty"
    lun               = 0
    caching           = "None"
    disk_size_gb      = var.worker_data_volume_size
    managed_disk_type = "Standard_LRS"
  }

  os_profile {
    computer_name  = format("%s%03d", "worker-", (count.index + 1))
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
      "Name" = format("%s%03d", "worker-", (count.index + 1)),
      "Environment" = format("%s", var.rg),
      "Role" = "worker",
    }),
    var.tags
  )
}
