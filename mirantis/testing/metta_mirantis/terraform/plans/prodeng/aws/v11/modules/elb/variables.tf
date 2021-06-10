variable "ports" {
  type        = list(string)
  default     = ["443"]
  description = "Ports for the target groups."
}

variable "node_count" {
  type        = number
  description = "Number of nodes in the cluster."
}

variable "machine_ids" {
  description = "List of node instance IDs."
}

variable "component" {
  type = string
  description = "Brief name of product component, ie, 'mke', 'msr'."
}

variable "globals" {
  description = "Map of global variables."
}
