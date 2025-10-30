# Pipeline infrastructure outputs
output "pipeline_name" {
  description = "Name of the SageMaker pipeline"
  value       = local.pipeline_name
}

output "data_paths" {
  description = "S3 paths for pipeline data flow"
  value = {
    raw_data       = local.raw_data_path
    processed_data = local.processed_data_path
    featured_data  = local.featured_data_path
    model_artifacts = local.model_artifacts_path
    trained_models = local.trained_models_path
  }
}

output "script_locations" {
  description = "S3 locations of uploaded pipeline scripts"
  value = {
    data_processing     = "s3://${var.s3_bucket_name}/${aws_s3_object.data_processing_script.key}"
    feature_engineering = "s3://${var.s3_bucket_name}/${aws_s3_object.feature_engineering_script.key}"
    model_training      = "s3://${var.s3_bucket_name}/${aws_s3_object.model_training_script.key}"
    model_requirements  = "s3://${var.s3_bucket_name}/${aws_s3_object.model_requirements.key}"
  }
}

output "pipeline_config_parameter" {
  description = "SSM parameter containing pipeline configuration"
  value       = aws_ssm_parameter.pipeline_config.name
}

output "pipeline_execution_command" {
  description = "Command to execute the pipeline"
  value       = "python3 create_ml_pipeline.py && python3 execute_pipeline.py"
}