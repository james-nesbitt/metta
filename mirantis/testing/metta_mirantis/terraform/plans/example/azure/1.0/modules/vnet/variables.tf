variable "cluster_name" {}

variable "location" {}

variable "virtual_network_name" {}

variable "host_cidr" {
  description = "CIDR IPv4 range to assign to VMs"
  default     = "172.31.0.0/16"
}

variable "subnet_cidr" {
  description = "The address prefix to use for the subnet."
  default     = "172.31.0.0/16"
}

variable "tags" {
  description = "Additional tags to apply to all resources"
}
