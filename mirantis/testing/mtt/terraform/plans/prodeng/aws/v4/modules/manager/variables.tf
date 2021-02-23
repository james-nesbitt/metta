variable "cluster_name" {}

variable "vpc_id" {}

variable "instance_profile_name" {}

variable "security_group_id" {}

variable "subnet_ids" {
  type = list(string)
}

variable "image_id" {}

variable "kube_cluster_tag" {}

variable "project" {}

variable "platform" {}

variable "expire" {}

variable "controller_port" {
  type    = string
  default = "443"
}

variable "ssh_key" {
  description = "SSH key name"
}

variable "manager_count" {
  default = 3
}

variable "manager_type" {
  default = "m5.xlarge"
}

variable "manager_volume_size" {
  default = 100
}
