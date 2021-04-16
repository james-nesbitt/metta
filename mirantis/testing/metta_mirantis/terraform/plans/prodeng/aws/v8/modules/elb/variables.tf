
variable "manager_count" {
  type        = number
  description = "Number of managers in the cluster."
}

variable "machine_ids" {
  description = "List of manager instance IDs."
}

variable "subnet_ids" {}

variable "globals" {
  description = "Map of global variables."
  default = {}
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
