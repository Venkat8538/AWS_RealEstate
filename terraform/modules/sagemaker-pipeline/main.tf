# SageMaker Pipeline with Terraform
locals {
  pipeline_name = "${var.project_name}-mlops-pipeline"
}

# SageMaker Pipeline Definition
resource "aws_sagemaker_pipeline" "mlops_pipeline" {
  pipeline_name         = local.pipeline_name
  pipeline_display_name = "House-Price-MLOps-Pipeline"
  role_arn             = var.sagemaker_role_arn

  pipeline_definition = jsonencode({
    Version = "2020-12-01"
    Metadata = {}
    Parameters = [
      {
        Name = "InputData"
        Type = "String"
        DefaultValue = "s3://${var.s3_bucket_name}/data/raw/house_data.csv"
      },
      {
        Name = "ProcessingInstanceType"
        Type = "String"
        DefaultValue = "ml.t3.medium"
      },
      {
        Name = "TrainingInstanceType"
        Type = "String"
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
              InstanceType = {
                Get = "Parameters.ProcessingInstanceType"
              }
              InstanceCount = 1
              VolumeSizeInGB = 30
            }
          }
          AppSpecification = {
            ImageUri = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.0-1-cpu-py3"
            ContainerEntrypoint = ["python3", "/opt/ml/processing/input/code/run_processing.py"]
          }
          RoleArn = var.sagemaker_role_arn
          ProcessingInputs = [
            {
              InputName = "input-data"
              AppManaged = false
              S3Input = {
                S3Uri = {
                  Get = "Parameters.InputData"
                }
                LocalPath = "/opt/ml/processing/input"
                S3DataType = "S3Prefix"
                S3InputMode = "File"
                S3DataDistributionType = "FullyReplicated"
              }
            },
            {
              InputName = "code"
              AppManaged = false
              S3Input = {
                S3Uri = "s3://${var.s3_bucket_name}/scripts/run_processing.py"
                LocalPath = "/opt/ml/processing/input/code"
                S3DataType = "S3Prefix"
                S3InputMode = "File"
                S3DataDistributionType = "FullyReplicated"
              }
            }
          ]
          ProcessingOutputConfig = {
            Outputs = [
              {
                OutputName = "processed-data"
                AppManaged = false
                S3Output = {
                  S3Uri = "s3://${var.s3_bucket_name}/data/processed"
                  LocalPath = "/opt/ml/processing/output"
                  S3UploadMode = "EndOfJob"
                }
              }
            ]
          }
        }
      },
      {
        Name = "FeatureEngineering"
        Type = "Processing"
        DependsOn = ["DataProcessing"]
        Arguments = {
          ProcessingResources = {
            ClusterConfig = {
              InstanceType = {
                Get = "Parameters.ProcessingInstanceType"
              }
              InstanceCount = 1
              VolumeSizeInGB = 30
            }
          }
          AppSpecification = {
            ImageUri = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.0-1-cpu-py3"
            ContainerEntrypoint = ["python3", "/opt/ml/processing/input/code/engineer.py"]
          }
          RoleArn = var.sagemaker_role_arn
          ProcessingInputs = [
            {
              InputName = "processed-data"
              AppManaged = false
              S3Input = {
                S3Uri = {
                  Get = "Steps.DataProcessing.ProcessingOutputConfig.Outputs['processed-data'].S3Output.S3Uri"
                }
                LocalPath = "/opt/ml/processing/input"
                S3DataType = "S3Prefix"
                S3InputMode = "File"
                S3DataDistributionType = "FullyReplicated"
              }
            },
            {
              InputName = "code"
              AppManaged = false
              S3Input = {
                S3Uri = "s3://${var.s3_bucket_name}/scripts/engineer.py"
                LocalPath = "/opt/ml/processing/input/code"
                S3DataType = "S3Prefix"
                S3InputMode = "File"
                S3DataDistributionType = "FullyReplicated"
              }
            }
          ]
          ProcessingOutputConfig = {
            Outputs = [
              {
                OutputName = "featured-data"
                AppManaged = false
                S3Output = {
                  S3Uri = "s3://${var.s3_bucket_name}/data/featured"
                  LocalPath = "/opt/ml/processing/output"
                  S3UploadMode = "EndOfJob"
                }
              }
            ]
          }
        }
      },
      {
        Name = "ModelTraining"
        Type = "Training"
        DependsOn = ["FeatureEngineering"]
       Arguments = {
  AlgorithmSpecification = {
    TrainingImage     = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.5-1"
    TrainingInputMode = "File"
  }

  # DO NOT add entry_point or source_dir here

  InputDataConfig = [
    {
      ChannelName = "train"
      DataSource = {
        S3DataSource = {
          S3DataType = "S3Prefix"
          S3Uri = {
            Get = "Steps.FeatureEngineering.ProcessingOutputConfig.Outputs['featured-data'].S3Output.S3Uri"
          }
          S3DataDistributionType = "FullyReplicated"
        }
      }
      ContentType = "text/csv"
      InputMode   = "File"
    }
  ]

  OutputDataConfig = {
    S3OutputPath = "s3://${var.s3_bucket_name}/models/trained"
  }

  ResourceConfig = {
    InstanceType   = { Get = "Parameters.TrainingInstanceType" }
    InstanceCount  = 1
    VolumeSizeInGB = 30
  }

  RoleArn           = var.sagemaker_role_arn
  StoppingCondition = { MaxRuntimeInSeconds = 3600 }
  Environment       = { S3_BUCKET = var.s3_bucket_name }

HyperParameters = {
  "entry_point"      = "train_model.py"
  "source_dir"       = "s3://${var.s3_bucket_name}/scripts"

  # XGBoost params
  "objective"        = "reg:squarederror"
  "num_round"        = "100"
  "max_depth"        = "5"
  "eta"              = "0.2"
  "gamma"            = "4"
  "min_child_weight" = "6"
  "subsample"        = "0.8"
  "verbosity"        = "1"

  # Data
  "target"           = "Price"   # change if your label is named differently
}


}
      }
    ]
  })

  tags = {
    Name        = local.pipeline_name
    Environment = var.environment
    Purpose     = "MLOps-Pipeline"
  }
}
