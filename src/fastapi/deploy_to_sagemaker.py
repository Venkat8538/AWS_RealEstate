#!/usr/bin/env python3
"""
Deploy FastAPI as SageMaker Endpoint (Industry Standard)
This script builds the Docker image, pushes to ECR, and deploys to SageMaker
"""
import boto3
import sagemaker
from sagemaker.model import Model
from datetime import datetime
import subprocess
import os

# Configuration
REGION = "us-east-1"
PROJECT_NAME = "house-price"
IMAGE_NAME = f"{PROJECT_NAME}-fastapi"
ENDPOINT_NAME = f"{PROJECT_NAME}-prod"

# Get AWS account ID
sts = boto3.client('sts', region_name=REGION)
account_id = sts.get_caller_identity()['Account']

# ECR repository URI
ecr_uri = f"{account_id}.dkr.ecr.{REGION}.amazonaws.com/{IMAGE_NAME}"

# SageMaker role (from Terraform output)
sagemaker_role = f"arn:aws:iam::{account_id}:role/{PROJECT_NAME}-sagemaker-execution-role"

# S3 model location
s3_model_uri = f"s3://{PROJECT_NAME}-mlops-dev-itzi2hgi/models/trained/model.tar.gz"

def build_and_push_image():
    """Build Docker image and push to ECR"""
    print("🔨 Building Docker image...")
    
    # Build image
    subprocess.run([
        "docker", "build",
        "-t", IMAGE_NAME,
        "-f", "src/fastapi/Dockerfile",
        "src/fastapi"
    ], check=True)
    
    # Create ECR repository if it doesn't exist
    ecr = boto3.client('ecr', region_name=REGION)
    try:
        ecr.create_repository(repositoryName=IMAGE_NAME)
        print(f"✅ Created ECR repository: {IMAGE_NAME}")
    except ecr.exceptions.RepositoryAlreadyExistsException:
        print(f"ℹ️  ECR repository already exists: {IMAGE_NAME}")
    
    # Login to ECR
    print("🔐 Logging into ECR...")
    login_cmd = subprocess.run([
        "aws", "ecr", "get-login-password",
        "--region", REGION
    ], capture_output=True, text=True, check=True)
    
    subprocess.run([
        "docker", "login",
        "--username", "AWS",
        "--password-stdin",
        f"{account_id}.dkr.ecr.{REGION}.amazonaws.com"
    ], input=login_cmd.stdout, text=True, check=True)
    
    # Tag and push
    print(f"📤 Pushing image to ECR: {ecr_uri}")
    subprocess.run(["docker", "tag", IMAGE_NAME, f"{ecr_uri}:latest"], check=True)
    subprocess.run(["docker", "push", f"{ecr_uri}:latest"], check=True)
    
    print(f"✅ Image pushed: {ecr_uri}:latest")
    return f"{ecr_uri}:latest"

def deploy_to_sagemaker(image_uri):
    """Deploy FastAPI container to SageMaker endpoint"""
    print("🚀 Deploying to SageMaker...")
    
    # Create SageMaker model
    model = Model(
        image_uri=image_uri,
        model_data=s3_model_uri,  # Model artifacts from S3
        role=sagemaker_role,
        name=f"{PROJECT_NAME}-model-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        sagemaker_session=sagemaker.Session()
    )
    
    # Deploy endpoint
    print(f"📦 Deploying endpoint: {ENDPOINT_NAME}")
    predictor = model.deploy(
        instance_type="ml.t2.medium",
        initial_instance_count=1,
        endpoint_name=ENDPOINT_NAME,
        wait=True
    )
    
    print(f"✅ Endpoint deployed: {ENDPOINT_NAME}")
    print(f"🌐 Endpoint URL: https://runtime.sagemaker.{REGION}.amazonaws.com/endpoints/{ENDPOINT_NAME}/invocations")
    
    return predictor

def test_endpoint():
    """Test the deployed endpoint"""
    print("🧪 Testing endpoint...")
    
    runtime = boto3.client('sagemaker-runtime', region_name=REGION)
    
    payload = {
        "sqft": 2000,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "location": "Urban",
        "year_built": 2010,
        "condition": "Good"
    }
    
    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType='application/json',
        Body=str(payload)
    )
    
    result = response['Body'].read().decode()
    print(f"✅ Test prediction: {result}")

if __name__ == "__main__":
    print("=" * 60)
    print("🏗️  Deploying FastAPI to SageMaker (Industry Standard)")
    print("=" * 60)
    
    # Step 1: Build and push Docker image
    image_uri = build_and_push_image()
    
    # Step 2: Deploy to SageMaker
    deploy_to_sagemaker(image_uri)
    
    # Step 3: Test endpoint
    test_endpoint()
    
    print("\n" + "=" * 60)
    print("✅ Deployment complete!")
    print("=" * 60)
    print(f"\nEndpoint Name: {ENDPOINT_NAME}")
    print(f"Region: {REGION}")
    print(f"\nTo invoke:")
    print(f"  aws sagemaker-runtime invoke-endpoint \\")
    print(f"    --endpoint-name {ENDPOINT_NAME} \\")
    print(f"    --body '{{...}}' \\")
    print(f"    --region {REGION} \\")
    print(f"    output.json")
