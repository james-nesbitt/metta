variable "cluster_name" {}

variable "project" {}

variable "task_name" {}

variable "username" {}

variable "expire" {}

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

variable "tags" {
  description = "Tags that will be added to the AWS resources"
  type = map(string)
  default = {}
}
