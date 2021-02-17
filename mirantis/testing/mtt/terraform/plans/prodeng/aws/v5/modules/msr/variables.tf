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

variable "msr_count" {
  default = 1
}

variable "msr_type" {
  default = "m5.xlarge"
}

variable "msr_volume_size" {
  default = 100
}

variable "tags" {
  description = "Tags that will be added to the AWS resources"
  type = map(string)
  default = {}
}
