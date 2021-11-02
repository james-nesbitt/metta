variable "cluster_name" {}

variable "location" {}

variable "rg" {}

variable "vnet_id" {}

variable "subnet_id" {}

variable "ssh_key" {}

variable "master_count" {
  default = 3
}

variable "master_type" {
  default = "Standard_DS3_v2"
}

variable "master_data_volume_size" {
  default = 100
}

variable "master_os_volume_size" {
  default = 40
}

variable "tags" {
  description = "Additional tags to apply to all resources"
}

variable "image" {}

variable "fault_domain_count" {}

variable "update_domain_count" {}
