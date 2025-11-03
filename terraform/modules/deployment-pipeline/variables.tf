variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "s3_bucket_name" {
  description = "Name of the MLOps S3 bucket"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the MLOps S3 bucket"
  type        = string
}

variable "sagemaker_role_arn" {
  description = "ARN of the SageMaker execution role"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
}

variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
}