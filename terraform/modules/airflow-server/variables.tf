variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "db_endpoint" {
  description = "RDS endpoint for Airflow database"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}