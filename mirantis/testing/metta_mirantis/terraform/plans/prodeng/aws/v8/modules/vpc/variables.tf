
variable "host_cidr" {
  description = "CIDR IPv4 range to assign to EC2 nodes"
  default     = "172.31.0.0/16"
}

variable "constants" {
  description = "Map of constant values from configuration."
  type = map(string)
  default = {}
}

variable "tags" {
  description = "Map of tags to apply to all created resources."
  type = map(string)
  default = {}
}
