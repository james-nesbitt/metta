variable "cluster_name" {
  default = "mke"
}

variable "azure_region" {
  default = "uswest"
}

variable "azure_environment" {
  default = "public"
}

variable "vnet_name" {
  default = "virtualNet"
}

variable "vnet_cidr" {
  default = "172.31.0.0/16"
}

variable "address_space" {
  default = "172.31.0.0/16"
}

variable "admin_password" {
  default = "orcaorcaorca"
}

variable "master_count" {
  default = 1
}

variable "worker_count" {
  default = 3
}

variable "windows_worker_count" {
  default = 0
}

variable "master_type" {
  default = "Standard_DS3_v2"
}

variable "worker_type" {
  default = "Standard_DS3_v2"
}

variable "master_volume_size" {
  default = 100
}

variable "worker_volume_size" {
  default = 100
}

variable "image_ubuntu1804" {
  description = "Default Ubuntu 18.04 LTS Image"
  type        = map
  default = {
    "offer"     = "UbuntuServer"
    "publisher" = "Canonical"
    "sku"       = "18.04-LTS"
    "version"   = "latest"
  }
}

variable "image_windows2019" {
  description = "Default Windows 2019 Server Image"
  type        = map
  default = {
    "offer"     = "WindowsServer"
    "publisher" = "MicrosoftWindowsServer"
    "sku"       = "2019-Datacenter"
    "version"   = "latest"
  }
}

variable "windows_admin_username" {
  default = "DockerAdmin"
}

variable "tags" {
  type = map
  default = {
    "Owner" = "Launchpad"
  }
}

variable "fault_domain_count" {
  description = "Specifies the number of fault domains that are used"
  default     = 2
}

variable "update_domain_count" {
  description = "Specifies the number of update domains that are used"
  default     = 2
}
