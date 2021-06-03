
locals {

  # Build a list of all machine hosts used in the cluster.
  # @NOTE This list is a meta structure that contains all of the host info used
  #    to build constructs such as the ansible hosts file, the launchpad yaml
  #    or the PRODENG toolbox config
  #
  hosts = concat(
    var.manager_count == 0 ? [] : [
      for host in module.managers[0].instances : {
        instance = host.instance
        ami : local.ami_obj
        role = "manager"
        # @TODO put this into the template, not here
        ssh = {
          address = host.instance.public_ip
          user    = local.ami_obj.user
          keyPath = local.key_path
        }
        hooks = {
          apply = {
            before = var.hooks_apply_before
            after  = var.hooks_apply_after
          }
        }
      }
    ],
    var.worker_count == 0 ? [] : [
      for host in module.workers[0].instances : {
        instance = host.instance
        ami : local.ami_obj
        role = "worker"
        # @TODO put this into the template, not here
        ssh = {
          address = host.instance.public_ip
          user    = local.ami_obj.user
          keyPath = local.key_path
        }
        hooks = {
          apply = {
            before = var.hooks_apply_before
            after  = var.hooks_apply_after
          }
        }
      }
    ],
    var.msr_count == 0 ? [] : [
      for host in module.msrs[0].instances : {
        instance = host.instance
        ami : local.ami_obj
        role = "msr"
        # @TODO put this into the template, not here
        ssh = {
          address = host.instance.public_ip
          user    = local.ami_obj.user
          keyPath = local.key_path
        }
        hooks = {
          apply = {
            before = var.hooks_apply_before
            after  = var.hooks_apply_after
          }
        }
      }
    ],
    var.windows_worker_count == 0 ? [] : [
      for host in module.windows_workers[0].instances : {
        instance = host.instance
        ami : local.ami_obj_win
        role = "worker"
        # @TODO put this into the template, not here
        winrm = {
          address  = host.instance.public_ip
          user     = local.ami_obj_win.user
          password = var.windows_administrator_password
          useHTTPS = true
          insecure = true
        }
      }
    ]
  )

  # Launchpad config object which could be output to yaml.
  # @NOTE we use an object so that it can be interpreted in parts, and read as
  #    using `terraform output -json`
  launchpad_1_3 = yamldecode(templatefile("${path.module}/templates/mke_cluster.1_3.tpl",
    {
      cluster_name = local.cluster_name
      key_path     = local.key_path

      hosts = local.hosts

      mcr_version           = var.mcr_version
      mcr_channel           = var.mcr_channel
      mcr_repoURL           = var.mcr_repo_url
      mcr_installURLLinux   = var.mcr_install_url_linux
      mcr_installURLWindows = var.mcr_install_url_windows

      mke_version            = var.mke_version
      mke_image_repo         = var.mke_image_repo
      mke_admin_username     = var.admin_username
      mke_admin_password     = var.admin_password
      mke_san                = module.elb_mke.lb_dns_name
      mke_kube_orchestration = var.kube_orchestration
      mke_installFlags       = var.mke_install_flags
      mke_upgradeFlags       = []

      msr_version        = var.msr_version
      msr_image_repo     = var.msr_image_repo
      msr_count          = var.msr_count
      msr_installFlags   = var.msr_install_flags
      msr_replica_config = var.msr_replica_config

      cluster_prune = false
    }
  ))

  # toolbox config object which could be output to yaml.
  # @NOTE we use an object so that it can be interpreted in parts, and read as
  #    using `terraform output -json`
  nodes = yamldecode(templatefile("${path.module}/templates/nodes_yaml.tpl",
    {
      key_path = local.key_path
      hosts    = local.hosts
    }
  ))

  # Ansible config object which could be output to yaml.
  # @NOTE we use an object so that it can be interpreted in parts, and read as
  #    using `terraform output -json`
  ansible_inventory = templatefile("${path.module}/templates/ansible_inventory.tpl",
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
}

# Various outputs for different format

output "hosts" {
  value = local.hosts
}

output "launchpad" {
  value = local.launchpad_1_3
}

output "mke_cluster" {
  value = yamlencode(local.launchpad_1_3)
}

output "nodes" {
  value = local.nodes
}

output "nodes_yaml" {
  value = yamlencode(local.nodes)
}

output "cluster_name" {
  value = local.cluster_name
}

output "mke_lb" {
  value = "https://${module.elb_mke.lb_dns_name}"
}

# Use this output is you are trying to build your own launchpad yaml and need
# the value for "--san={}
output "mke_san" {
  value = module.elb_mke.lb_dns_name
}

output "msr_lb" {
  # If no MSR replicas, then no LB should exist
  value = try("https://${module.elb_msr[0].lb_dns_name}", null)
}

output "ansible_inventory" {
  value = local.ansible_inventory
}

