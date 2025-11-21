output "sagemaker_execution_role_arn" {
  description = "ARN of the SageMaker execution role"
  value       = aws_iam_role.sagemaker_execution_role.arn
}

output "sagemaker_execution_role_name" {
  description = "Name of the SageMaker execution role"
  value       = aws_iam_role.sagemaker_execution_role.name
}

output "sagemaker_domain_id" {
  description = "ID of the SageMaker Domain"
  value       = aws_sagemaker_domain.mlops_domain.id
}

output "sagemaker_domain_arn" {
  description = "ARN of the SageMaker Domain"
  value       = aws_sagemaker_domain.mlops_domain.arn
}

output "sagemaker_user_profile_arn" {
  description = "ARN of the SageMaker User Profile"
  value       = aws_sagemaker_user_profile.data_scientist.arn
}

output "endpoint_name" {
  description = "Name of the SageMaker endpoint"
  value       = aws_sagemaker_endpoint.house_price_endpoint.name
}

output "endpoint_arn" {
  description = "ARN of the SageMaker endpoint"
  value       = aws_sagemaker_endpoint.house_price_endpoint.arn
}