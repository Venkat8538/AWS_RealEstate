output "pipeline_arn" {
  description = "ARN of the SageMaker Pipeline"
  value       = aws_sagemaker_pipeline.mlops_pipeline.arn
}

output "pipeline_name" {
  description = "Name of the SageMaker Pipeline"
  value       = aws_sagemaker_pipeline.mlops_pipeline.pipeline_name
}