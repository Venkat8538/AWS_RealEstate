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
          Environment = {
            MLFLOW_TRACKING_URI = "http://mlflow-service:5000"
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
          Environment = {
            MLFLOW_TRACKING_URI = "http://mlflow-service:5000"
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
    TrainingImage     = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1"
    TrainingInputMode = "File"
  }

  InputDataConfig = [
    {
      ChannelName = "train"
      DataSource = {
        S3DataSource = {
          S3DataType = "S3Prefix"
          S3Uri = {
            Get = "Steps.DataProcessing.ProcessingOutputConfig.Outputs['processed-data'].S3Output.S3Uri"
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

  RoleArn = var.sagemaker_role_arn
  StoppingCondition = { MaxRuntimeInSeconds = 3600 }

  Environment = {
    S3_BUCKET            = var.s3_bucket_name
    MLFLOW_TRACKING_URI  = "http://mlflow-service:5000"
  }

  HyperParameters = {
    # Required by ScriptMode
    "sagemaker_program"           = "train_model.py"
    "sagemaker_submit_directory"  = "s3://${var.s3_bucket_name}/scripts/scripts.tar.gz"

    # Your actual HPs
    "objective"        = "reg:squarederror"
    "num_round"        = "100"
  }
}

      },
      {
        Name = "ModelEvaluation"
        Type = "Processing"
        DependsOn = ["ModelTraining"]
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
            ImageUri = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.5-1"
            ContainerEntrypoint = ["python3", "/opt/ml/processing/input/code/evaluate.py"]
          }
          Environment = {
            MLFLOW_TRACKING_URI = "http://mlflow-service:5000"
          }
          RoleArn = var.sagemaker_role_arn
          ProcessingInputs = [
            {
              InputName = "model"
              AppManaged = false
              S3Input = {
                S3Uri = {
                  Get = "Steps.ModelTraining.ModelArtifacts.S3ModelArtifacts"
                }
                LocalPath = "/opt/ml/processing/input/model"
                S3DataType = "S3Prefix"
                S3InputMode = "File"
                S3DataDistributionType = "FullyReplicated"
              }
            },
            {
              InputName = "test-data"
              AppManaged = false
              S3Input = {
                S3Uri = "s3://${var.s3_bucket_name}/data/test/test.csv"
                LocalPath = "/opt/ml/processing/input/data"
                S3DataType = "S3Prefix"
                S3InputMode = "File"
                S3DataDistributionType = "FullyReplicated"
              }
            },
            {
              InputName = "code"
              AppManaged = false
              S3Input = {
                S3Uri = "s3://${var.s3_bucket_name}/scripts/evaluate.py"
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
                OutputName = "evaluation-report"
                AppManaged = false
                S3Output = {
                  S3Uri = "s3://${var.s3_bucket_name}/evaluation/reports"
                  LocalPath = "/opt/ml/processing/output"
                  S3UploadMode = "EndOfJob"
                }
              }
            ]
          }
        }
      },
        {
          Name = "ModelRegistration"
          Type = "Processing"
          DependsOn = ["ModelEvaluation"]
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
              ContainerEntrypoint = ["python3", "/opt/ml/processing/input/code/register_model.py"]
            }
            Environment = {
              AWS_DEFAULT_REGION = "us-east-1"
              MLFLOW_TRACKING_URI = "http://mlflow-service:5000"
            }
            RoleArn = var.sagemaker_role_arn
            ProcessingInputs = [
              {
                InputName = "evaluation-report"
                AppManaged = false
                S3Input = {
                  S3Uri = {
                    Get = "Steps.ModelEvaluation.ProcessingOutputConfig.Outputs['evaluation-report'].S3Output.S3Uri"
                  }
                  LocalPath = "/opt/ml/processing/input/evaluation"
                  S3DataType = "S3Prefix"
                  S3InputMode = "File"
                  S3DataDistributionType = "FullyReplicated"
                }
              },
              {
                InputName = "code"
                AppManaged = false
                S3Input = {
                  S3Uri = "s3://${var.s3_bucket_name}/scripts/register_model.py"
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
                  OutputName = "registration-metadata"
                  AppManaged = false
                  S3Output = {
                    S3Uri = "s3://${var.s3_bucket_name}/models/registry"
                    LocalPath = "/opt/ml/processing/output"
                    S3UploadMode = "EndOfJob"
                  }
                }
              ]
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
