# Pipeline outputs removed - pipeline is now created via Python SDK
# The pipeline ARN and name can be retrieved using:
# aws sagemaker describe-pipeline --pipeline-name <pipeline-name>

output "pipeline_info" {
  description = "Information about pipeline creation"
  value = {
    message = "Pipeline is created via Python SDK using create_ml_pipeline.py"
    expected_name = "${var.project_name}-mlops-pipeline"
  }
}