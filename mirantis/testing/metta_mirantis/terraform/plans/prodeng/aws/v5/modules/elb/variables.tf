variable "controller_port" {
  type        = string
  default     = "443"
  description = "Controler port for the MKE manager."
}

variable "manager_count" {
  type        = number
  description = "Number of managers in the cluster."
}

variable "machine_ids" {
  description = "List of manager instance IDs."
}

variable "globals" {
  description = "Map of global variables."
}
