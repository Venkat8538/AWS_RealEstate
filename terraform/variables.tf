variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "house-price"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "github_repository" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
  default     = "Venkat8538/AWS_RealEstate"
}

variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
}

variable "airflow_db_password" {
  description = "Password for Airflow PostgreSQL database"
  type        = string
  sensitive   = true
  default     = "airflow123!"
}