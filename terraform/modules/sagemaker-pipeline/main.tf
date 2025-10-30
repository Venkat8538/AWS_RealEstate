# SageMaker Pipeline Infrastructure
# Note: Actual pipeline definition is created via Python SDK (create_ml_pipeline.py)
# This module creates supporting infrastructure

# S3 paths for pipeline data flow
locals {
  pipeline_name = "${var.project_name}-mlops-pipeline"
  
  # Pipeline data paths
  raw_data_path       = "s3://${var.s3_bucket_name}/data/raw/"
  processed_data_path = "s3://${var.s3_bucket_name}/data/processed/"
  featured_data_path  = "s3://${var.s3_bucket_name}/data/featured/"
  model_artifacts_path = "s3://${var.s3_bucket_name}/models/artifacts/"
  trained_models_path = "s3://${var.s3_bucket_name}/models/trained/"
}

# Upload pipeline scripts to S3
resource "aws_s3_object" "data_processing_script" {
  bucket = var.s3_bucket_name
  key    = "code/data/run_processing.py"
  source = "${path.root}/../src/data/run_processing.py"
  etag   = filemd5("${path.root}/../src/data/run_processing.py")
  
  tags = {
    Name        = "${var.project_name}-data-processing-script"
    Environment = var.environment
    Purpose     = "MLOps-Pipeline-Code"
  }
}

resource "aws_s3_object" "feature_engineering_script" {
  bucket = var.s3_bucket_name
  key    = "code/features/engineer.py"
  source = "${path.root}/../src/features/engineer.py"
  etag   = filemd5("${path.root}/../src/features/engineer.py")
  
  tags = {
    Name        = "${var.project_name}-feature-engineering-script"
    Environment = var.environment
    Purpose     = "MLOps-Pipeline-Code"
  }
}

resource "aws_s3_object" "model_training_script" {
  bucket = var.s3_bucket_name
  key    = "code/models/train_model.py"
  source = "${path.root}/../src/models/train_model.py"
  etag   = filemd5("${path.root}/../src/models/train_model.py")
  
  tags = {
    Name        = "${var.project_name}-model-training-script"
    Environment = var.environment
    Purpose     = "MLOps-Pipeline-Code"
  }
}

resource "aws_s3_object" "model_requirements" {
  bucket = var.s3_bucket_name
  key    = "code/models/requirements.txt"
  source = "${path.root}/../src/models/requirements.txt"
  etag   = filemd5("${path.root}/../src/models/requirements.txt")
  
  tags = {
    Name        = "${var.project_name}-model-requirements"
    Environment = var.environment
    Purpose     = "MLOps-Pipeline-Code"
  }
}

# Pipeline execution parameters
resource "aws_ssm_parameter" "pipeline_config" {
  name  = "/${var.project_name}/pipeline/config"
  type  = "String"
  value = jsonencode({
    pipeline_name = local.pipeline_name
    data_paths = {
      raw_data       = local.raw_data_path
      processed_data = local.processed_data_path
      featured_data  = local.featured_data_path
      model_artifacts = local.model_artifacts_path
      trained_models = local.trained_models_path
    }
    scripts = {
      data_processing     = "s3://${var.s3_bucket_name}/code/data/run_processing.py"
      feature_engineering = "s3://${var.s3_bucket_name}/code/features/engineer.py"
      model_training      = "s3://${var.s3_bucket_name}/code/models/train_model.py"
    }
  })
  
  tags = {
    Name        = "${var.project_name}-pipeline-config"
    Environment = var.environment
    Purpose     = "MLOps-Pipeline-Configuration"
  }
}