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

variable "worker_count" {
  default = 0
}

variable "worker_type" {
  default = "m5.large"
}

variable "worker_volume_size" {
  default = 100
}

variable "windows_administrator_password" {
}

variable "tags" {
  description = "Tags that will be added to the AWS resources"
  type = map(string)
  default = {}
}
