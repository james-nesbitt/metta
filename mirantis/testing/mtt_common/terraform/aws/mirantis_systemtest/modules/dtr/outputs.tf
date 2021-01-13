output "private_ips" {
  value = aws_instance.dtr.*.private_ip
}
output "machines" {
  value = aws_instance.dtr.*
}
