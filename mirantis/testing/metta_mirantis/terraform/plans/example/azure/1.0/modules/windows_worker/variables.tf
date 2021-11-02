variable "cluster_name" {}

variable "location" {}

variable "rg" {}

variable "vnet_id" {}

variable "subnet_id" {}

variable "ssh_key" {}

variable "worker_count" {
  default = 0
}

variable "worker_type" {
  default = "Standard_DS3_v2"
}

variable "worker_data_volume_size" {
  default = 100
}

variable "tags" {
  description = "Additional tags to apply to all resources"
}

variable "image" {}

variable "username" {}

variable "fault_domain_count" {}

variable "update_domain_count" {}
