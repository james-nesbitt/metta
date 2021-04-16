output "security_group_id" {
  value = aws_security_group.common.id
}

output "image_id" {
  value = data.aws_ami.linux.id
}

output "root_device_name" {
  value = data.aws_ami.linux.block_device_mappings.*.device_name[0]
}

output "windows_2019_image_id" {
  value = data.aws_ami.windows_2019.id
}

output "availability_zones" {
  value = data.aws_availability_zones.available.names
}

output "az_count" {
  value = length(data.aws_availability_zones.available.names)
}

output "instance_profile_name" {
  value = aws_iam_instance_profile.profile.name
}

output "key_pair" {
  value = aws_key_pair.key
}
