output "instance_id" {
  value = aws_instance.bamboo_server.id
}

output "public_ip" {
  value = aws_instance.bamboo_server.public_ip
}

output "bamboo_url" {
  value = "http://${aws_instance.bamboo_server.public_ip}:${var.bamboo_port}"
}
