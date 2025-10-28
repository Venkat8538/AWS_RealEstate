variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "sagemaker_pipeline_arn" {
  description = "ARN of the SageMaker Pipeline to trigger"
  type        = string
}