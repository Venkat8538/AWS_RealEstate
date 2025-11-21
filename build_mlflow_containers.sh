#!/bin/bash

# Build and push MLflow-enabled Docker images for SageMaker pipeline
set -e

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# ECR repositories
REPOSITORIES=(
    "data-processing"
    "feature-engineering" 
    "training"
    "evaluation"
    "model-registration"
)

echo "🔨 Building MLflow-enabled containers for SageMaker pipeline"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"

# Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push each container
for repo in "${REPOSITORIES[@]}"; do
    echo ""
    echo "🏗️  Building $repo container for AMD64..."
    
    # Build for AMD64 platform (SageMaker requirement)
    docker build --platform linux/amd64 -t $repo:latest docker/$repo/
    
    # Tag for ECR
    docker tag $repo:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo:latest
    
    # Push to ECR
    echo "📤 Pushing $repo to ECR..."
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo:latest
    
    echo "✅ $repo pushed successfully"
done

echo ""
echo "🎉 All MLflow-enabled containers built and pushed!"
echo ""
echo "📋 Container URLs:"
for repo in "${REPOSITORIES[@]}"; do
    echo "  $repo: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo:latest"
done

echo ""
echo "🔥 Now your SageMaker pipeline will have MLflow logging in ALL stages:"
echo "  ✅ DataProcessing - logs processing stats"
echo "  ✅ FeatureEngineering - logs feature metrics" 
echo "  ✅ ModelTraining - logs training metrics"
echo "  ✅ ModelEvaluation - logs evaluation metrics"
echo "  ✅ ModelRegistration - logs registration info"