output "s3_bucket_name" {
  description = "Name of the MLOps S3 bucket"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the MLOps S3 bucket"
  value       = module.s3.bucket_arn
}

output "sagemaker_execution_role_arn" {
  description = "ARN of the SageMaker execution role"
  value       = module.sagemaker.sagemaker_execution_role_arn
}

output "sagemaker_pipeline_arn" {
  description = "ARN of the SageMaker Pipeline"
  value       = module.sagemaker_pipeline.pipeline_arn
}

output "sagemaker_pipeline_name" {
  description = "Name of the SageMaker Pipeline"
  value       = module.sagemaker_pipeline.pipeline_name
}

output "sagemaker_domain_id" {
  description = "ID of the SageMaker Domain"
  value       = module.sagemaker.sagemaker_domain_id
}

output "sagemaker_user_profile_arn" {
  description = "ARN of the SageMaker User Profile"
  value       = module.sagemaker.sagemaker_user_profile_arn
}