variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "db_password" {
  description = "Password for the Airflow database"
  type        = string
  sensitive   = true
}