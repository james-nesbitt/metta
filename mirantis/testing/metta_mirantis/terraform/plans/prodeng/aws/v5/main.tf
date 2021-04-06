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
  source           = "./modules/common"
  cluster_name     = local.cluster_name
  vpc_id           = module.vpc.id
  ami_obj          = local.ami_obj
  ami_obj_win      = local.ami_obj_win
  key_path         = local.key_path
  open_sg_for_myip = var.open_sg_for_myip
}

module "elb" {
  source          = "./modules/elb"
  controller_port = local.controller_port
  machine_ids     = module.managers[0].machine_ids
  manager_count   = var.manager_count
  globals         = local.globals
}

module "managers" {
  source             = "./modules/manager"
  count              = var.manager_count == 0 ? 0 : 1
  node_role          = "manager"
  node_count         = var.manager_count
  node_instance_type = var.manager_type
  node_volume_size   = var.manager_volume_size
  controller_port    = local.controller_port
  globals            = local.globals
}

module "workers" {
  source             = "./modules/worker"
  count              = var.worker_count == 0 ? 0 : 1
  node_role          = "worker"
  node_count         = var.worker_count
  node_instance_type = var.worker_type
  node_volume_size   = var.worker_volume_size
  globals            = local.globals
}

module "msrs" {
  source             = "./modules/msr"
  count              = var.msr_count == 0 ? 0 : 1
  node_role          = "msr"
  node_count         = var.msr_count
  node_instance_type = var.msr_type
  node_volume_size   = var.msr_volume_size
  globals            = local.globals
}

module "windows_workers" {
  source             = "./modules/windows_worker"
  count              = var.windows_worker_count == 0 ? 0 : 1
  node_role          = "worker"
  node_count         = var.windows_worker_count
  node_instance_type = var.worker_type
  image_id           = module.common.windows_2019_image_id
  win_admin_password = var.windows_administrator_password
  globals            = local.globals
}

locals {
  cluster_name       = var.cluster_name == "" ? "${var.username}-${var.task_name}-${random_string.random.result}" : var.cluster_name
  expire             = timeadd(timestamp(), var.expire_duration)
  kube_orchestration = var.kube_orchestration ? "--default-node-orchestrator=kubernetes" : ""
  ami_obj            = var.platforms[var.platform_repo][var.platform]
  ami_obj_win        = var.platforms[var.platform_repo]["windows_2019"]

  platform_details_map = {
    "centos" : "Linux/UNIX",
    "oracle" : "Linux/UNIX",
    "rhel" : "Red Hat Enterprise Linux",
    "sles" : "SUSE Linux",
    "ubuntu" : "Linux/UNIX",
    "windows" : "Windows"
  }
  distro = split("_", var.platform)[0]

  globals = {
    tags = {
      "Name"                                        = local.cluster_name
      "kubernetes.io/cluster/${local.cluster_name}" = "shared"
      "project"                                     = var.project
      "platform"                                    = var.platform
      "expire"                                      = local.expire
    }
    distro                = local.distro
    platform_details      = local.platform_details_map[local.distro]
    subnet_count          = length(module.vpc.public_subnet_ids)
    az_names_count        = length(module.vpc.az_names)
    spot_price_multiplier = 1 + (var.pct_over_spot_price / 100)
    pct_over_spot_price   = var.pct_over_spot_price
    vpc_id                = module.vpc.id
    cluster_name          = local.cluster_name
    subnet_ids            = module.vpc.public_subnet_ids
    az_names              = module.vpc.az_names
    security_group_id     = module.common.security_group_id
    image_id              = module.common.image_id
    root_device_name      = module.common.root_device_name
    ssh_key               = local.cluster_name
    instance_profile_name = module.common.instance_profile_name
    project               = var.project
    platform              = var.platform
    expire                = local.expire
    iam_fleet_role        = "arn:aws:iam::546848686991:role/aws-ec2-spot-fleet-role"
  }

  mke_install_flags = concat([
    "--admin-username=${var.admin_username}",
    "--admin-password=${var.admin_password}",
    local.kube_orchestration,
    "--san=${module.elb.lb_dns_name}",
    ],
    var.mke_install_flags
  )
  mke_upgrade_flags = concat([
    "--force-recent-backup",
    "--force-minimums",
    ]
  )
  mke_opts        = [for f in local.mke_install_flags : element(split("=", f), 1) if substr(f, 0, 18) == "--controller-port="]
  controller_port = local.mke_opts == [] ? "443" : element(local.mke_opts, 1)
  key_path        = var.ssh_key_file_path == "" ? "./ssh_keys/${local.cluster_name}.pem" : var.ssh_key_file_path

  hosts = concat(local.managers, local.workers, local.windows_workers, local.msrs)
  mcr = {
    version : var.mcr_version
    channel : var.mcr_channel
    repoURL : var.mcr_repo_url
    installURLLinux : var.mcr_install_url_linux
    installURLWindows : var.mcr_install_url_windows
  }
  mke = {
    version : var.mke_version
    imageRepo : var.mke_image_repo
    installFlags : local.mke_install_flags
    upgradeFlags : local.mke_upgrade_flags
  }
  msr = {
    version : var.msr_version
    imageRepo : var.msr_image_repo
    installFlags : var.msr_install_flags
    replicaIDs : var.msr_replica_config
  }

  managers = var.manager_count == 0 ? [] : [
    for host in module.managers[0].instances : {
      address = host.instance.public_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role = "manager"
      hooks = {
        apply = {
          before = var.hooks_apply_before
          after  = var.hooks_apply_after
        }
      }
    }
  ]
  _managers = var.manager_count == 0 ? [] : [
    for host in module.managers[0].instances : {
      address   = host.instance.public_ip
      privateIp = host.instance.private_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role = "manager"
    }
  ]

  workers = var.worker_count == 0 ? [] : [
    for host in module.workers[0].instances : {
      address = host.instance.public_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role = "worker"
      hooks = {
        apply = {
          before = var.hooks_apply_before
          after  = var.hooks_apply_after
        }
      }
    }
  ]
  _workers = var.worker_count == 0 ? [] : [
    for host in module.workers[0].instances : {
      address   = host.instance.public_ip
      privateIp = host.instance.private_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role = "worker"
    }
  ]
  msrs = var.msr_count == 0 ? [] : [
    for host in module.msrs[0].instances : {
      address = host.instance.public_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role = "msr"
      hooks = {
        apply = {
          before = var.hooks_apply_before
          after  = var.hooks_apply_after
        }
      }
    }
  ]
  _msrs = var.msr_count == 0 ? [] : [
    for host in module.msrs[0].instances : {
      address   = host.instance.public_ip
      privateIp = host.instance.private_ip
      ssh = {
        user    = local.ami_obj.user
        keyPath = local.key_path
      }
      role = "msr"
    }
  ]
  windows_workers = var.windows_worker_count == 0 ? [] : [
    for host in module.windows_workers[0].instances : {
      address = host.instance.public_ip
      winRM = {
        user     = local.ami_obj_win.user
        password = var.windows_administrator_password
        useHTTPS = true
        insecure = true
      }
      role = "worker"
    }
  ]
  _windows_workers = var.windows_worker_count == 0 ? [] : [
    for host in module.windows_workers[0].instances : {
      address   = host.instance.public_ip
      privateIp = host.instance.private_ip
      winRM = {
        user     = local.ami_obj_win.user
        password = var.windows_administrator_password
        useHTTPS = true
        insecure = true
      }
      role = "worker"
    }
  ]

  mke_cluster = {
    apiVersion = "launchpad.mirantis.com/mke/v1.2"
    kind       = "mke"
    spec = {
      hosts = local.hosts,
      mcr   = local.mcr,
      mke   = local.mke,
      msr   = local.msr
    }
  }
  _mke_cluster = concat(local._managers, local._workers, local._windows_workers, local._msrs)
}

# Write configs to YAML files

resource "local_file" "launchpad_yaml" {
  content  = yamlencode(local.mke_cluster)
  filename = "launchpad.yaml"
}

resource "local_file" "nodes_yaml" {
  content  = yamlencode(local._mke_cluster)
  filename = "nodes.yaml"
}

# Create Ansible inventory file
resource "local_file" "ansible_inventory" {
  content = templatefile("modules/templates/inventory.tmpl",
    {
      user      = local.ami_obj.user,
      key_file  = local.key_path,
      mgr_hosts = var.manager_count == 0 ? [] : module.managers[0].instances,
      mgr_idxs  = range(var.manager_count),
      wkr_hosts = var.worker_count == 0 ? [] : module.workers[0].instances,
      wkr_idxs  = range(var.worker_count),
      msr_hosts = var.msr_count == 0 ? [] : module.msrs[0].instances,
      msr_idxs  = range(var.msr_count)
    }
  )
  filename = "hosts.ini"
}

output "mke_cluster" {
  value = local.mke_cluster
}

output "_mke_cluster" {
  value = local._mke_cluster
}

output "cluster_name" {
  value = local.cluster_name
}

output "mke_lb" {
  value = "https://${module.elb.lb_dns_name}"
}
