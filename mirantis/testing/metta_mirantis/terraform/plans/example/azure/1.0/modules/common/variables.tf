variable "cluster_name" {}

variable "rg" {}

variable "vnet_id" {}

variable "subnet_id" {}

variable "location" {}

variable tags {
  description = "Additional tags to apply to all resources"
  type        = map
  default     = {}
}
