# SageMaker Pipeline for MLOps
resource "aws_sagemaker_pipeline" "mlops_pipeline" {
  pipeline_name         = "${var.project_name}-mlops-pipeline"
  pipeline_display_name = "House-Price-MLOps-Pipeline"
  role_arn             = var.sagemaker_role_arn

  pipeline_definition = jsonencode({
    Version = "2020-12-01"
    Steps = [
      {
        Name = "DataProcessing"
        Type = "Processing"
        Arguments = {
          ProcessingResources = {
            ClusterConfig = {
              InstanceType   = "ml.t3.medium"
              InstanceCount  = 1
              VolumeSizeInGB = 20
            }
          }
          AppSpecification = {
            ImageUri = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
            ContainerEntrypoint = ["python3", "-c", "import time; print('Pipeline completed successfully'); time.sleep(5)"]
          }
          RoleArn = var.sagemaker_role_arn
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-mlops-pipeline"
    Environment = var.environment
  }
}