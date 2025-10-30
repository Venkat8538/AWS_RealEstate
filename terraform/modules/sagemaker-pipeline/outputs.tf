# SageMaker Pipeline Outputs
output "pipeline_arn" {
  description = "ARN of the SageMaker pipeline"
  value       = aws_sagemaker_pipeline.mlops_pipeline.arn
}

output "pipeline_name" {
  description = "Name of the SageMaker pipeline"
  value       = aws_sagemaker_pipeline.mlops_pipeline.pipeline_name
}

output "pipeline_execution_command" {
  description = "AWS CLI command to execute the pipeline"
  value       = "aws sagemaker start-pipeline-execution --pipeline-name ${aws_sagemaker_pipeline.mlops_pipeline.pipeline_name}"
}

output "data_paths" {
  description = "S3 paths for pipeline data flow"
  value = {
    raw_data       = "s3://${var.s3_bucket_name}/data/raw/"
    processed_data = "s3://${var.s3_bucket_name}/data/processed/"
    featured_data  = "s3://${var.s3_bucket_name}/data/featured/"
    trained_models = "s3://${var.s3_bucket_name}/models/trained/"
  }
}