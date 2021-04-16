variable "vpc_id" {}

variable "platform" {
  default = "ubuntu_18.04"
}

variable "ami_obj" {}

variable "ami_obj_win" {}

variable "open_sg_for_myip" {
  type        = bool
  default     = false
  description = "If true, trust all traffic, any protocol, originating from the terraform execution source IP."
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
