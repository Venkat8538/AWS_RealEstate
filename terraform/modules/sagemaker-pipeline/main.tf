# SageMaker Pipeline for MLOps
resource "aws_sagemaker_pipeline" "mlops_pipeline" {
  pipeline_name         = "${var.project_name}-mlops-pipeline"
  pipeline_display_name = "House-Price-MLOps-Pipeline"
  role_arn             = var.sagemaker_role_arn

  pipeline_definition = jsonencode({
    Version = "2020-12-01"
    Parameters = [
      {
        Name         = "ProcessingInstanceType"
        Type         = "String"
        DefaultValue = "ml.m5.large"
      },
      {
        Name         = "TrainingInstanceType"
        Type         = "String"
        DefaultValue = "ml.m5.large"
      }
    ]
    Steps = [
      {
        Name = "DataProcessing"
        Type = "Processing"
        Arguments = {
          ProcessingResources = {
            ClusterConfig = {
              InstanceType   = "ml.m5.large"
              InstanceCount  = 1
              VolumeSizeInGB = 30
            }
          }
          AppSpecification = {
            ImageUri = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
            ContainerEntrypoint = ["python3", "/opt/ml/processing/input/code/run_processing.py"]
          }
          RoleArn = var.sagemaker_role_arn
        }
      },
      {
        Name = "FeatureEngineering"
        Type = "Processing"
        DependsOn = ["DataProcessing"]
        Arguments = {
          ProcessingResources = {
            ClusterConfig = {
              InstanceType   = "ml.m5.large"
              InstanceCount  = 1
              VolumeSizeInGB = 30
            }
          }
          AppSpecification = {
            ImageUri = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
            ContainerEntrypoint = ["python3", "/opt/ml/processing/input/code/engineer.py"]
          }
          RoleArn = var.sagemaker_role_arn
        }
      },
      {
        Name = "ModelTraining"
        Type = "Training"
        DependsOn = ["FeatureEngineering"]
        Arguments = {
          AlgorithmSpecification = {
            TrainingImage = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
            TrainingInputMode = "File"
          }
          RoleArn = var.sagemaker_role_arn
          ResourceConfig = {
            InstanceType   = "ml.m5.large"
            InstanceCount  = 1
            VolumeSizeInGB = 30
          }
          StoppingCondition = {
            MaxRuntimeInSeconds = 3600
          }
          HyperParameters = {
            "n_estimators" = "100"
            "max_depth"    = "10"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-mlops-pipeline"
    Environment = var.environment
  }
}