variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "sagemaker_role_arn" {
  description = "SageMaker execution role ARN"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name for MLOps"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "mlflow_server_url" {
  description = "MLflow tracking server URL"
  type        = string
}