variable "node_count" {
  type        = number
  default     = 3
  description = "Number of nodes/machines."
}

variable "node_instance_type" {
  type        = string
  default     = "m5.large"
  description = "AWS instance type of the nodes/machines."
}

variable "node_volume_size" {
  type        = number
  default     = 100
  description = "Size in GB of the root volume of the nodes/machines."
}

variable "node_role" {
  type        = string
  description = "The node's role in the cluster, ie, manager/worker/msr."
}

variable "globals" {
  description = "Map of global variables."
}
