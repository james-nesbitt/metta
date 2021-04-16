
variable "asg_node_id" {
  type        = string
  description = "AWS security group node ID."
}

variable "instance_type" {
  type        = string
  description = "Local instance type."
}

variable "node_count" {
  type        = number
  description = "Number of nodes/machines."
}

variable "node_role" {
  type        = string
  description = "Local node role."
}

variable "os_type" {
  type        = string
  description = "Local OS type, ie, linux or windows."
}

variable "constants" {
  description = "Map of constant values from configuration."
  type = map(string)
  default = {}
}

variable "globals" {
  description = "Map of global variables."
}

variable "tags" {
  description = "Map of tags to apply to all created resources."
  type = map(string)
  default = {}
}

variable "volume_size" {
  type        = string
  description = "Size of root volume."
}
