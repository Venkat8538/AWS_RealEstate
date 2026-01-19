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

variable "bamboo_ami_id" {
  description = "AMI ID for Bamboo server"
  type        = string
  default     = "ami-066279af4a501d501"  # AlmaLinux 9.7 Official (no subscription, Podman included)
}

variable "bamboo_key_name" {
  description = "EC2 key pair name for Bamboo server"
  type        = string
  default     = ""
}

variable "bamboo_vpc_id" {
  description = "VPC ID for Bamboo server"
  type        = string
  default     = "vpc-0ec06d2e45d4c6de8"
}

variable "bamboo_subnet_id" {
  description = "Subnet ID for Bamboo server"
  type        = string
  default     = "subnet-0c092dfafe0a2b4b2"
}