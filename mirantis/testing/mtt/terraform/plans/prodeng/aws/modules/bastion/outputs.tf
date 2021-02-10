output "public_ips" {
  value = aws_instance.mke_bastion.*.public_ip
}
output "private_ips" {
  value = aws_instance.mke_bastion.*.private_ip
}
output "machines" {
  value = aws_instance.mke_bastion.*
}
