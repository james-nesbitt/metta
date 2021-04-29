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
  source      = "./modules/vpc"
  host_cidr   = var.vpc_cidr
  global_tags = local.global_tags
}

module "common" {
  source           = "./modules/common"
  cluster_name     = local.cluster_name
  vpc_id           = module.vpc.id
  ami_obj          = local.ami_obj
  ami_obj_win      = local.ami_obj_win
  key_path         = local.key_path
  open_sg_for_myip = var.open_sg_for_myip
  global_tags      = local.global_tags
}

module "elb_mke" {
  source          = "./modules/elb"
  component       = "mke"
  ports           = [local.controller_port,"6443"]
  machine_ids     = module.managers[0].machine_ids
  node_count      = var.manager_count
  globals         = local.globals
}

module "elb_msr" {
  source          = "./modules/elb"
  count           = var.msr_count == 0 ? 0 : 1
  component       = "msr"
  ports           = ["443"]
  machine_ids     = module.msrs[0].machine_ids
  node_count      = var.msr_count
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
  cluster_name       = var.cluster_name == "" ? random_string.random.result : var.cluster_name
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

  global_tags = merge(
    {
      "Name"                                        = local.cluster_name
      "kubernetes.io/cluster/${local.cluster_name}" = "shared"
      "project"                                     = var.project
      "platform"                                    = var.platform
      "expire"                                      = local.expire
      "username"                                    = var.username
      "task_name"                                   = var.task_name
    },
    var.extra_tags
  )

  globals = {
    tags                  = local.global_tags
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

  # convert MKE install flags into a map
  mke_opts = { for f in var.mke_install_flags : trimprefix(element(split("=", f), 0), "--") => element(split("=", f), 1) }
  # discover if there is a controller port override.
  controller_port = try(
    local.mke_opts.controller_port,
    "443"
  )
  # Pick a path for saving the RSA private key
  key_path = var.ssh_key_file_path == "" ? "./ssh_keys/${local.cluster_name}.pem" : var.ssh_key_file_path

}
