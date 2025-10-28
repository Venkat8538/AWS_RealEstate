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
            ContainerEntrypoint = ["python3", "-c", "import pandas as pd; import os; df = pd.read_csv('/opt/ml/processing/input/house_data.csv'); print(f'✅ Processed {len(df)} rows'); df.to_csv('/opt/ml/processing/output/processed_data.csv', index=False); print('✅ Data saved to S3')"]
          }
          ProcessingInputs = [
            {
              InputName = "input-data"
              S3Input = {
                S3Uri = "s3://${var.s3_bucket_name}/data/raw/"
                LocalPath = "/opt/ml/processing/input"
                S3DataType = "S3Prefix"
                S3InputMode = "File"
              }
            }
          ]
          ProcessingOutputs = [
            {
              OutputName = "processed-data"
              S3Output = {
                S3Uri = "s3://${var.s3_bucket_name}/data/processed/"
                LocalPath = "/opt/ml/processing/output"
                S3UploadMode = "EndOfJob"
              }
            }
          ]
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
              InstanceType   = "ml.t3.medium"
              InstanceCount  = 1
              VolumeSizeInGB = 20
            }
          }
          AppSpecification = {
            ImageUri = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
            ContainerEntrypoint = ["python3", "-c", "import pandas as pd; import os; df = pd.read_csv('/opt/ml/processing/input/processed_data.csv'); df['price_per_sqft'] = df['price'] / df['sqft_living']; print(f'✅ Engineered features for {len(df)} rows'); df.to_csv('/opt/ml/processing/output/features.csv', index=False); print('✅ Features saved to S3')"]
          }
          ProcessingInputs = [
            {
              InputName = "processed-data"
              S3Input = {
                S3Uri = "s3://${var.s3_bucket_name}/data/processed/"
                LocalPath = "/opt/ml/processing/input"
                S3DataType = "S3Prefix"
                S3InputMode = "File"
              }
            }
          ]
          ProcessingOutputs = [
            {
              OutputName = "features"
              S3Output = {
                S3Uri = "s3://${var.s3_bucket_name}/data/interim/"
                LocalPath = "/opt/ml/processing/output"
                S3UploadMode = "EndOfJob"
              }
            }
          ]
          RoleArn = var.sagemaker_role_arn
        }
      },
      {
        Name = "ModelTraining"
        Type = "Processing"
        DependsOn = ["FeatureEngineering"]
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
            ContainerEntrypoint = ["python3", "-c", "import pandas as pd; import pickle; from sklearn.ensemble import RandomForestRegressor; from sklearn.model_selection import train_test_split; df = pd.read_csv('/opt/ml/processing/input/features.csv'); X = df[['bedrooms', 'bathrooms', 'sqft_living', 'price_per_sqft']]; y = df['price']; X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2); model = RandomForestRegressor(n_estimators=10); model.fit(X_train, y_train); score = model.score(X_test, y_test); print(f'✅ Model trained with R² score: {score:.3f}'); with open('/opt/ml/processing/output/model.pkl', 'wb') as f: pickle.dump(model, f); print('✅ Model saved to S3')"]
          }
          ProcessingInputs = [
            {
              InputName = "features"
              S3Input = {
                S3Uri = "s3://${var.s3_bucket_name}/data/interim/"
                LocalPath = "/opt/ml/processing/input"
                S3DataType = "S3Prefix"
                S3InputMode = "File"
              }
            }
          ]
          ProcessingOutputs = [
            {
              OutputName = "model"
              S3Output = {
                S3Uri = "s3://${var.s3_bucket_name}/models/trained/"
                LocalPath = "/opt/ml/processing/output"
                S3UploadMode = "EndOfJob"
              }
            }
          ]
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