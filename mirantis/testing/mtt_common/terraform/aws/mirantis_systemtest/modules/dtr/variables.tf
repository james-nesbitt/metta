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

variable "ssh_key" {
  description = "SSH key name"
}

variable "dtr_count" {
  default = 1
}

variable "dtr_type" {
  default = "m5.large"
}

variable "dtr_volume_size" {
  default = 100
}