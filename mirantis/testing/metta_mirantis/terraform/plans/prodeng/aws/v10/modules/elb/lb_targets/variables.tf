variable "port" {
  type        = string
  default     = "443"
  description = "Port for the target group."
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

variable "arn" {
    description = "LB-specific ARN"
}

variable "tags" {
    description = "LB-specific map of tags"
}
