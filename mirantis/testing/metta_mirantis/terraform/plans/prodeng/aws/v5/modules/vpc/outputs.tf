output "id" {
  value = aws_vpc.network.id
}

output "public_subnet_ids" {
  value = aws_subnet.public.*.id
}

output "az_names" {
  value = data.aws_availability_zones.all.names
}
