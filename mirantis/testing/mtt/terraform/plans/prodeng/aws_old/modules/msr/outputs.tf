output "private_ips" {
  value = aws_instance.msr.*.private_ip
}
output "machines" {
  value = aws_instance.msr.*
}
