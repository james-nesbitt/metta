variable "username" {
  type        = string
  default     = "UNDEFINED"
  description = "A short name/initials which represents the engineer running the test."
}

variable "task_name" {
  type        = string
  default     = "UNDEFINED"
  description = "An arbitrary yet unique string which represents the deployment, eg, 'refactor', 'unicorn', 'stresstest'."
}

variable "project" {
  type        = string
  default     = "UNDEFINED"
  description = "One of the official cost-tracking project names. Without this, your cluster may get terminated without warning."
}

variable "cluster_name" {
  type        = string
  default     = ""
  description = "Global cluster name. Use this to override a dynamically created name."
}

variable "expire_duration" {
  type        = string
  default     = "72h"
  description = "The max time to allow this cluster to avoid early termination. Can use 'h', 'm', 's' in sane combinations, eg, '15h37m18s'."
}

variable "aws_region" {
  type        = string
  default     = "us-west-2"
  description = "The AWS region to deploy to."
}

variable "vpc_cidr" {
  type        = string
  default     = "172.31.0.0/16"
  description = "The CIDR to use when creating the VPC."
}

variable "admin_username" {
  type        = string
  default     = "admin"
  description = "The UCP admin username to use."
}

variable "admin_password" {
  type        = string
  default     = "orcaorcaorca"
  description = "The UCP admin password to use."
}

variable "manager_count" {
  type        = number
  default     = 1
  description = "The number of UCP managers to create."
}

variable "worker_count" {
  type        = number
  default     = 3
  description = "The number of UCP Linux workers to create."
}

variable "msr_count" {
  type        = number
  default     = 0
  description = "The number of DTR replicas to create."
}

variable "windows_worker_count" {
  type        = number
  default     = 0
  description = "The number of UCP Windows workers to create."
}

variable "manager_type" {
  type        = string
  default     = "m5.xlarge"
  description = "The AWS instance type to use for manager nodes."
}

variable "worker_type" {
  type        = string
  default     = "m5.large"
  description = "The AWS instance type to use for Linux/Windows worker nodes."
}

variable "msr_type" {
  type        = string
  default     = "m5.xlarge"
  description = "The AWS instance type to use for DTR replica nodes."
}

variable "manager_volume_size" {
  type        = number
  default     = 100
  description = "The volume size (in GB) to use for manager nodes."
}

variable "worker_volume_size" {
  type        = number
  default     = 100
  description = "The volume size (in GB) to use for worker nodes."
}

variable "msr_volume_size" {
  type        = number
  default     = 100
  description = "The volume size (in GB) to use for DTR replica nodes."
}

variable "windows_administrator_password" {
  type        = string
  default     = "tfaws,,ABC..Example"
  description = "The Windows Administrator password to use."
}

variable "platform" {
  type        = string
  default     = "ubuntu_18.04"
  description = "The Linux platform to use for manager/worker/DTR replica nodes"
}

variable "mcr_version" {
  type        = string
  default     = "19.03.12"
  description = "The mcr version to deploy across all nodes in the cluster."
}

variable "mcr_channel" {
  type        = string
  default     = "stable"
  description = "The channel to pull the mcr installer from."
}

variable "mcr_repo_url" {
  type        = string
  default     = "https://repos-stage.mirantis.com/"
  description = "The repository to source the mcr installer."
}

variable "mcr_install_url_linux" {
  type        = string
  default     = "https://get.mirantis.com/"
  description = "Location of Linux installer script."
}

variable "mcr_install_url_windows" {
  type        = string
  default     = "https://get.mirantis.com/install.ps1"
  description = "Location of Windows installer script."
}

variable "mke_version" {
  type        = string
  default     = "3.3.3"
  description = "The UCP version to deploy."
}

variable "mke_image_repo" {
  type        = string
  default     = "docker.io/mirantis"
  description = "The repository to pull the UCP images from."
}

variable "mke_install_flags" {
  type        = list(string)
  default     = []
  description = "The UCP installer flags to use."
}

variable "kube_orchestration" {
  type        = bool
  default     = false
  description = "The option to enable/disable Kubernetes as the default orchestrator."
}

variable "msr_version" {
  type        = string
  default     = "2.8.3"
  description = "The DTR version to deploy."
}

variable "msr_image_repo" {
  type        = string
  default     = "docker.io/mirantis"
  description = "The repository to pull the DTR images from."
}

variable "msr_install_flags" {
  type        = list(string)
  default     = ["--ucp-insecure-tls"]
  description = "The DTR installer flags to use."
}

variable "msr_replica_config" {
  type        = string
  default     = "sequential"
  description = "Set to 'sequential' to generate sequential replica id's for cluster members, for example 000000000001, 000000000002, etc. ('random' otherwise)"
}

variable "platforms" {
  type = map(
    map(
      object({
        ami_name  = string
        owner     = string
        user      = string
        interface = string
      })
    )
  )
  description = "The JSON which describes AMI collections (see filename 'platforms.auto.tfvars.json' for details)"
}

variable "platform_repo" {
  type        = string
  default     = "public"
  description = "The selector for the applicable AMI subcollection (ie, 'public' vs 'mirantis')."
}

variable "hooks_apply_before" {
  type        = list(string)
  default     = [""]
  description = "A list of strings (shell commands) to be run before stages."
}

variable "hooks_apply_after" {
  type        = list(string)
  default     = [""]
  description = "A list of strings (shell commands) to be run after stages."
}

variable "ssh_key_file_path" {
  type        = string
  default     = ""
  description = "If non-empty, use this path/filename as the ssh key file instead of generating automatically."
}

variable "open_sg_for_myip" {
  type        = bool
  default     = false
  description = "If true, allow ALL traffic, ANY protocol, originating from the terraform execution source IP. Use sparingly."
}
