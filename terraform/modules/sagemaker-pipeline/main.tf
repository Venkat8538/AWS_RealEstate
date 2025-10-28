# SageMaker Pipeline placeholder - actual pipeline created via Python SDK
# This resource is commented out since we'll use Python SDK to create the pipeline
# resource "aws_sagemaker_pipeline" "mlops_pipeline" {
#   pipeline_name         = "${var.project_name}-mlops-pipeline"
#   pipeline_display_name = "House-Price-MLOps-Pipeline"
#   role_arn             = var.sagemaker_role_arn
# }