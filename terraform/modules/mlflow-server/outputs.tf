output "mlflow_server_url" {
  description = "MLflow server URL"
  value       = "http://${aws_eip.mlflow_eip.public_ip}:5000"
}

output "mlflow_server_ip" {
  description = "MLflow server Elastic IP"
  value       = aws_eip.mlflow_eip.public_ip
}