resource "random_string" "random" {
  length      = 6
  special     = false
  lower       = false
  min_upper   = 2
  min_numeric = 2
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source       = "./modules/vpc"
  cluster_name = local.cluster_name
  host_cidr    = var.vpc_cidr
  project      = var.project
  expire       = local.expire
}

module "common" {
  source       = "./modules/common"
  cluster_name = local.cluster_name
  vpc_id       = module.vpc.id
  ami_obj      = local.ami_obj
  ami_obj_win  = local.ami_obj_win
  key_path     = local.key_path
}

module "managers" {
  source                = "./modules/manager"
  manager_count         = var.manager_count
  vpc_id                = module.vpc.id
  cluster_name          = local.cluster_name
  subnet_ids            = module.vpc.public_subnet_ids
  security_group_id     = module.common.security_group_id
  image_id              = module.common.image_id
  kube_cluster_tag      = module.common.kube_cluster_tag
  ssh_key               = local.cluster_name
  instance_profile_name = module.common.instance_profile_name
  project               = var.project
  platform              = var.platform
  expire                = local.expire
  controller_port       = local.controller_port
}

module "workers" {
  source                = "./modules/worker"
  worker_count          = var.worker_count
  vpc_id                = module.vpc.id
  cluster_name          = local.cluster_name
  subnet_ids            = module.vpc.public_subnet_ids
  security_group_id     = module.common.security_group_id
  image_id              = module.common.image_id
  kube_cluster_tag      = module.common.kube_cluster_tag
  ssh_key               = local.cluster_name
  instance_profile_name = module.common.instance_profile_name
  worker_type           = var.worker_type
  project               = var.project
  platform              = var.platform
  expire                = local.expire
}

module "dtrs" {
  source                = "./modules/dtr"
  dtr_count             = var.dtr_count
  vpc_id                = module.vpc.id
  cluster_name          = local.cluster_name
  subnet_ids            = module.vpc.public_subnet_ids
  security_group_id     = module.common.security_group_id
  image_id              = module.common.image_id
  kube_cluster_tag      = module.common.kube_cluster_tag
  ssh_key               = local.cluster_name
  instance_profile_name = module.common.instance_profile_name
  dtr_type              = var.dtr_type
  project               = var.project
  platform              = var.platform
  expire                = local.expire
}

module "windows_workers" {
  source                         = "./modules/windows_worker"
  worker_count                   = var.windows_worker_count
  vpc_id                         = module.vpc.id
  cluster_name                   = local.cluster_name
  subnet_ids                     = module.vpc.public_subnet_ids
  security_group_id              = module.common.security_group_id
  image_id                       = module.common.windows_2019_image_id
  kube_cluster_tag               = module.common.kube_cluster_tag
  instance_profile_name          = module.common.instance_profile_name
  worker_type                    = var.worker_type
  project                        = var.project
  platform                       = "Windows"
  expire                         = local.expire
  windows_administrator_password = var.windows_administrator_password
}

locals {
  cluster_name       = "${var.username}-${var.task_name}-${random_string.random.result}"
  expire             = timeadd(timestamp(), var.expire_duration)
  kube_orchestration = var.kube_orchestration ? "--default-node-orchestrator=kubernetes" : ""
  ami_obj            = var.platforms[var.platform_repo][var.platform]
  ami_obj_win        = var.platforms[var.platform_repo]["windows_2019"]
  ucp_install_flags  = concat([
      "--admin-username=${var.admin_username}",
      "--admin-password=${var.admin_password}",
      local.kube_orchestration,
      "--san=${module.managers.lb_dns_name}",
    ],
    var.ucp_install_flags
  )
  ucp_opts = [for f in local.ucp_install_flags : element(split("=", f), 1) if substr(f, 0, 18) == "--controller-port="]
  controller_port = local.ucp_opts == [] ? "443" : element(local.ucp_opts, 1)
  key_path = var.ssh_key_file_path == "" ? "./ssh_keys/${local.cluster_name}.pem" : var.ssh_key_file_path
  managers = [
    for host in module.managers.machines : {
      address = host.public_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role             = host.tags["Role"]
      privateInterface = local.ami_obj.interface
      hooks = {
        apply = {
          before = var.hooks_apply_before
          after = var.hooks_apply_after
        }
      }
    }
  ]
  _managers = [
    for host in module.managers.machines : {
      address = host.public_ip
      privateIp = host.private_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role             = host.tags["Role"]
    }
  ]
  workers = [
    for host in module.workers.machines : {
      address = host.public_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role             = host.tags["Role"]
      privateInterface = local.ami_obj.interface
      hooks = {
        apply = {
          before = var.hooks_apply_before
          after = var.hooks_apply_after
        }
      }
    }
  ]
  _workers = [
    for host in module.workers.machines : {
      address = host.public_ip
      privateIp = host.private_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role             = host.tags["Role"]
    }
  ]
  dtrs = [
    for host in module.dtrs.machines : {
      address = host.public_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role             = host.tags["Role"]
      privateInterface = local.ami_obj.interface
      hooks = {
        apply = {
          before = var.hooks_apply_before
          after = var.hooks_apply_after
        }
      }
    }
  ]
  _dtrs = [
    for host in module.dtrs.machines : {
      address = host.public_ip
      privateIp = host.private_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role             = host.tags["Role"]
    }
  ]
  windows_workers = [
    for host in module.windows_workers.machines : {
      address = host.public_ip
      winRM = {
        user     = local.ami_obj_win.user
        password = var.windows_administrator_password
        useHTTPS = true
        insecure = true
      }
      role = host.tags["Role"]
      privateInterface = local.ami_obj_win.interface
    }
  ]
  _windows_workers = [
    for host in module.windows_workers.machines : {
      address = host.public_ip
      privateIp = host.private_ip
      winRM = {
        user     = local.ami_obj_win.user
        password = var.windows_administrator_password
        useHTTPS = true
        insecure = true
      }
      role = host.tags["Role"]
    }
  ]
}

output "ucp_cluster" {
  value = {
    apiVersion = "launchpad.mirantis.com/v1"
    kind       = "DockerEnterprise"
    spec = {
      ucp = {
        version : var.ucp_version
        imageRepo : var.ucp_image_repo
        installFlags : local.ucp_install_flags
      }
      dtr = {
        version : var.dtr_version
        imageRepo : var.dtr_image_repo
        installFlags : var.dtr_install_flags
        replicaConfig : var.dtr_replica_config
      }
      engine = {
        version : var.engine_version
        channel : var.engine_channel
      }
      hosts = concat(local.managers, local.workers, local.windows_workers, local.dtrs)
    }
  }
}

output "_ucp_cluster" {
  value = {
    hosts = concat(local._managers, local._workers, local._windows_workers, local._dtrs)
  }
}

output "cluster_name" {
  value = local.cluster_name
}
