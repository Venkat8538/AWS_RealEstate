# Main Terraform configuration for MLOps Single Account
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# AWS Provider
provider "aws" {
  region = var.aws_region
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# S3 Module for MLOps
module "s3" {
  source = "./modules/s3"
  
  project_name = var.project_name
  environment  = var.environment
}

# SageMaker Module for Data Scientists
module "sagemaker" {
  source = "./modules/sagemaker"
  
  project_name   = var.project_name
  environment    = var.environment
  s3_bucket_arn  = module.s3.bucket_arn
  s3_bucket      = module.s3.bucket_name
  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# ECR Module for Model Registration
module "ecr" {
  source = "./modules/ecr"
  
  project_name = var.project_name
  environment  = var.environment
}

# MLflow Server Module
module "mlflow_server" {
  source = "./modules/mlflow-server"
  
  project_name   = var.project_name
  s3_bucket_name = module.s3.bucket_name
}

# RDS Module for Airflow
module "rds" {
  source = "./modules/rds"
  
  project_name = var.project_name
  db_password  = var.airflow_db_password
}

# Airflow Server Module
module "airflow_server" {
  source = "./modules/airflow-server"
  
  project_name = var.project_name
  db_endpoint  = module.rds.db_endpoint
  db_name      = module.rds.db_name
  db_username  = module.rds.db_username
  db_password  = var.airflow_db_password
}

# SageMaker Pipeline Module
module "sagemaker_pipeline" {
  source = "./modules/sagemaker-pipeline"
  
  project_name        = var.project_name
  environment         = var.environment
  sagemaker_role_arn  = module.sagemaker.sagemaker_execution_role_arn
  s3_bucket_name      = module.s3.bucket_name
  account_id          = data.aws_caller_identity.current.account_id
  mlflow_server_url   = module.mlflow_server.mlflow_server_url
}

# EventBridge Module for GitHub Integration (optional - pipeline now uses Python SDK)
# module "eventbridge" {
#   source = "./modules/eventbridge"
#   
#   project_name          = var.project_name
#   environment           = var.environment
# }

# GitHub OIDC Module for secure authentication
module "github_oidc" {
  source = "./modules/github-oidc"
  
  project_name        = var.project_name
  github_repository   = var.github_repository
  s3_bucket_name      = module.s3.bucket_name
  sagemaker_role_arn  = module.sagemaker.sagemaker_execution_role_arn
}

# Deployment Pipeline Module
module "deployment_pipeline" {
  source = "./modules/deployment-pipeline"
  
  project_name        = var.project_name
  environment         = var.environment
  s3_bucket_name      = module.s3.bucket_name
  s3_bucket_arn       = module.s3.bucket_arn
  sagemaker_role_arn  = module.sagemaker.sagemaker_execution_role_arn
  github_repository   = var.github_repository
  github_token        = var.github_token
}