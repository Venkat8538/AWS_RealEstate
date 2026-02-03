# Quick Start - Deploy FastAPI to SageMaker

## Prerequisites
- ✅ Docker installed (version 27.5.1 detected)
- ❌ Docker Desktop not running - **START IT FIRST**
- ✅ AWS CLI configured
- ✅ Python environment with boto3, sagemaker

## Steps to Deploy

### 1. Start Docker Desktop
```bash
# Open Docker Desktop app or run:
open -a Docker
# Wait for Docker to start (check menu bar icon)
```

### 2. Run Automated Deployment
```bash
cd /Users/venkat/Documents/devops/AWS_RealEstate
source venv/bin/activate
python src/fastapi/deploy_to_sagemaker.py
```

This will:
- Build Docker image with FastAPI + Model
- Push to ECR
- Deploy to SageMaker endpoint
- Test the endpoint

### 3. Or Manual Steps

#### Build Docker Image
```bash
cd src/fastapi
docker build -t house-price-fastapi .
```

#### Push to ECR
```bash
# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create ECR repo
aws ecr create-repository --repository-name house-price-fastapi --region us-east-1

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag house-price-fastapi:latest ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/house-price-fastapi:latest
docker push ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/house-price-fastapi:latest
```

#### Deploy to SageMaker (Python)
```python
import boto3
from sagemaker.model import Model
import sagemaker

account_id = boto3.client('sts').get_caller_identity()['Account']
image_uri = f"{account_id}.dkr.ecr.us-east-1.amazonaws.com/house-price-fastapi:latest"

model = Model(
    image_uri=image_uri,
    model_data="s3://house-price-mlops-dev-itzi2hgi/models/latest/model.tar.gz",
    role="arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role",
    sagemaker_session=sagemaker.Session()
)

predictor = model.deploy(
    instance_type="ml.t2.medium",
    initial_instance_count=1,
    endpoint_name="house-price-prod"
)
```

## Current Status
- ❌ Docker Desktop not running
- ✅ Code refactored to industry standard
- ✅ Deployment script ready
- ⏳ Waiting for Docker to start

## Next Action
**START DOCKER DESKTOP** then run:
```bash
python src/fastapi/deploy_to_sagemaker.py
```
