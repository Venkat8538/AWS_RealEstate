variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "s3_bucket_arn" {
  description = "ARN of the MLOps S3 bucket"
  type        = string
}

variable "s3_bucket" {
  description = "Name of the MLOps S3 bucket"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}