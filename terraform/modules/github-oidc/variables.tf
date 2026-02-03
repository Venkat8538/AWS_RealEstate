variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
}

variable "github_repository_streamlit" {
  description = "GitHub repository for Streamlit UI in format 'owner/repo'"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the MLOps S3 bucket"
  type        = string
}

variable "sagemaker_role_arn" {
  description = "ARN of the SageMaker execution role"
  type        = string
}