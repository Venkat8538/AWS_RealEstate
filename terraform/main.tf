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
}

# SageMaker Pipeline Module
module "sagemaker_pipeline" {
  source = "./modules/sagemaker-pipeline"
  
  project_name        = var.project_name
  environment         = var.environment
  sagemaker_role_arn  = module.sagemaker.sagemaker_execution_role_arn
  s3_bucket_name      = module.s3.bucket_name
}

# EventBridge Module for GitHub Integration
module "eventbridge" {
  source = "./modules/eventbridge"
  
  project_name          = var.project_name
  environment           = var.environment
  sagemaker_pipeline_arn = module.sagemaker_pipeline.pipeline_arn
}

# GitHub OIDC Module for secure authentication
module "github_oidc" {
  source = "./modules/github-oidc"
  
  project_name      = var.project_name
  github_repository = var.github_repository
}