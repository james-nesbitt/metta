provider "azurerm" {
  features {}
  environment = var.azure_environment
}

module "vnet" {
  source               = "./modules/vnet"
  location             = var.azure_region
  cluster_name         = var.cluster_name
  host_cidr            = var.vnet_cidr
  subnet_cidr          = var.address_space
  virtual_network_name = var.vnet_name
  tags                 = var.tags
}

module "common" {
  source       = "./modules/common"
  location     = var.azure_region
  cluster_name = var.cluster_name
  rg           = module.vnet.rg
  vnet_id      = module.vnet.id
  subnet_id    = module.vnet.subnet_id
  tags         = var.tags
}

module "masters" {
  source              = "./modules/master"
  master_count        = var.master_count
  vnet_id             = module.vnet.id
  rg                  = module.vnet.rg
  cluster_name        = var.cluster_name
  location            = var.azure_region
  subnet_id           = module.vnet.subnet_id
  ssh_key             = module.common.ssh_key
  image               = var.image_ubuntu1804
  master_type         = var.master_type
  tags                = var.tags
  fault_domain_count  = var.fault_domain_count
  update_domain_count = var.update_domain_count

}

module "workers" {
  source              = "./modules/worker"
  worker_count        = var.worker_count
  vnet_id             = module.vnet.id
  rg                  = module.vnet.rg
  cluster_name        = var.cluster_name
  location            = var.azure_region
  subnet_id           = module.vnet.subnet_id
  ssh_key             = module.common.ssh_key
  image               = var.image_ubuntu1804
  worker_type         = var.worker_type
  tags                = var.tags
  fault_domain_count  = var.fault_domain_count
  update_domain_count = var.update_domain_count
}

module "windows_workers" {
  source              = "./modules/windows_worker"
  worker_count        = var.windows_worker_count
  vnet_id             = module.vnet.id
  rg                  = module.vnet.rg
  cluster_name        = var.cluster_name
  location            = var.azure_region
  subnet_id           = module.vnet.subnet_id
  ssh_key             = module.common.ssh_key
  image               = var.image_windows2019
  worker_type         = var.worker_type
  username            = var.windows_admin_username
  tags                = var.tags
  fault_domain_count  = var.fault_domain_count
  update_domain_count = var.update_domain_count
}

locals {
  managers = [
    for ip in module.masters.public_ips : {
      ssh = {
        address = ip
        user    = "ubuntu"
        keyPath = "./ssh_keys/${var.cluster_name}.pem"
      }
      privateInterface = "eth0"
      role             = "manager"
    }
  ]
  workers = [
    for ip in module.workers.public_ips : {
      ssh = {
        address = ip
        user    = "ubuntu"
        keyPath = "./ssh_keys/${var.cluster_name}.pem"
      }
      privateInterface = "eth0"
      role             = "worker"
    }
  ]
  windows_workers = [
    for ip in module.windows_workers.public_ips : {
      winRM = {
        address = ip
        user     = var.windows_admin_username
        password = module.windows_workers.windows_password
        useHTTPS = true
        insecure = true
      }
      privateInterface = "Ethernet"
      role             = "worker"
    }
  ]
}

locals {
  launchpad_tmpl = {
    apiVersion = "launchpad.mirantis.com/mke/v1.3"
    kind       = "mke"
    metadata = {
      name = var.cluster_name
    }
    spec = {
      mke = {
        adminUsername = "admin"
        adminPassword = var.admin_password
        installFlags : [
          "--default-node-orchestrator=kubernetes",
          "--san=${module.masters.lb_dns_name}",
        ]
      }
      hosts = concat(local.managers, local.workers, local.windows_workers)
    }
  }
}

output "mke_cluster" {
  value = yamlencode(local.launchpad_tmpl)
}

output "loadbalancers" {
  value = {
    MasterLB  = module.masters.lb_dns_name
    WorkersLB = module.workers.lb_dns_name
  }
}
