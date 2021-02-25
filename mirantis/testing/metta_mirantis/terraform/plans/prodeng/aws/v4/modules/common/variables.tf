variable "cluster_name" {}

variable "vpc_id" {}

variable "platform" {
  default = "ubuntu_18.04"
}

variable "ami_obj" {}

variable "ami_obj_win" {}

variable "key_path" {}

variable "open_sg_for_myip" {
  type        = bool
  default     = false
  description = "If true, trust all traffic, any protocol, originating from the terraform execution source IP."
}
