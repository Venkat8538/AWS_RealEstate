output "airflow_server_ip" {
  description = "Elastic IP of Airflow server"
  value       = aws_eip.airflow_eip.public_ip
}

output "airflow_server_url" {
  description = "Airflow web UI URL"
  value       = "http://${aws_eip.airflow_eip.public_ip}:8080"
}