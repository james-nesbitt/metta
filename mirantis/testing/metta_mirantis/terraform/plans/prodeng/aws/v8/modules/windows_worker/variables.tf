
variable "image_id" {
  type        = string
  description = "Amazon Machine Image ID for Windows."
}

variable "node_count" {
  type        = number
  default     = 0
  description = "Number of Windows nodes."
}

variable "node_role" {
  type        = string
  description = "The node's role in the cluster, ie, manager/worker/msr."
}

variable "node_instance_type" {
  type        = string
  default     = "m5.large"
  description = "AWS instance type of the nodes/machines."
}

variable "node_volume_size" {
  default = 100
}

variable "win_admin_password" {
  type        = string
  description = "Windows administrator password."
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
