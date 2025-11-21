# Model Registration Repository
output "repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.model_registration.repository_url
}

output "repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.model_registration.arn
}

output "repository_name" {
  description = "Name of the ECR repository"
  value       = aws_ecr_repository.model_registration.name
}

# Data Processing Repository
output "data_processing_repository_url" {
  description = "URL of the data processing ECR repository"
  value       = aws_ecr_repository.data_processing.repository_url
}

# Feature Engineering Repository
output "feature_engineering_repository_url" {
  description = "URL of the feature engineering ECR repository"
  value       = aws_ecr_repository.feature_engineering.repository_url
}

# Training Repository
output "training_repository_url" {
  description = "URL of the training ECR repository"
  value       = aws_ecr_repository.training.repository_url
}

# Evaluation Repository
output "evaluation_repository_url" {
  description = "URL of the evaluation ECR repository"
  value       = aws_ecr_repository.evaluation.repository_url
}