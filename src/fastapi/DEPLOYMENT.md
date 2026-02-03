# House Price Prediction API - Industry Standard Deployment

## Architecture (Industry Standard)

```
User → SageMaker Endpoint (FastAPI + Model inside) → Prediction
```

FastAPI runs **inside** the SageMaker endpoint container, not as a separate service.

## Key Changes from Previous Setup

### Before (Anti-pattern):
- FastAPI on separate EC2
- Calls SageMaker endpoint via boto3
- Extra network hop
- Two deployments to manage

### After (Industry Standard):
- FastAPI embedded in SageMaker endpoint
- Model loaded locally in container
- Single deployment
- Lower latency

## SageMaker-Required Endpoints

- `GET /ping` - Health check (SageMaker requirement)
- `POST /invocations` - Predictions (SageMaker requirement)
- `GET /health` - Legacy health check
- `POST /predict` - Legacy prediction endpoint
- `POST /batch-predict` - Batch predictions

## Deployment Steps

### 1. Build and Push Docker Image

```bash
cd src/fastapi

# Build image
docker build -t house-price-fastapi .

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name house-price-fastapi --region us-east-1

# Tag and push
docker tag house-price-fastapi:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/house-price-fastapi:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/house-price-fastapi:latest
```

### 2. Deploy to SageMaker (Automated)

```bash
python deploy_to_sagemaker.py
```

This script will:
1. Build Docker image
2. Push to ECR
3. Create SageMaker model
4. Deploy endpoint
5. Test the endpoint

### 3. Manual Deployment (Alternative)

```python
from sagemaker.model import Model

model = Model(
    image_uri="<account-id>.dkr.ecr.us-east-1.amazonaws.com/house-price-fastapi:latest",
    model_data="s3://bucket/models/model.tar.gz",
    role="arn:aws:iam::<account-id>:role/SageMakerRole"
)

predictor = model.deploy(
    instance_type="ml.t2.medium",
    initial_instance_count=1,
    endpoint_name="house-price-prod"
)
```

## Testing the Endpoint

### Via AWS CLI

```bash
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name house-price-prod \
  --content-type application/json \
  --body '{"sqft": 2000, "bedrooms": 3, "bathrooms": 2.5, "location": "Urban", "year_built": 2010, "condition": "Good"}' \
  --region us-east-1 \
  output.json

cat output.json
```

### Via Python

```python
import boto3
import json

runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')

payload = {
    "sqft": 2000,
    "bedrooms": 3,
    "bathrooms": 2.5,
    "location": "Urban",
    "year_built": 2010,
    "condition": "Good"
}

response = runtime.invoke_endpoint(
    EndpointName='house-price-prod',
    ContentType='application/json',
    Body=json.dumps(payload)
)

result = json.loads(response['Body'].read())
print(result)
```

## Directory Structure

```
/opt/ml/model/              # SageMaker model directory
├── main.py                 # FastAPI application
├── inference.py            # Inference logic
├── schemas.py              # Pydantic models
├── house_price_model.pkl   # Trained model
└── preprocessor.pkl        # Feature preprocessor
```

## Environment Variables

- `MODEL_PATH`: Path to model file (default: `/opt/ml/model/house_price_model.pkl`)
- `PREPROCESSOR_PATH`: Path to preprocessor (default: `/opt/ml/model/preprocessor.pkl`)

## Cost Comparison

### Old Setup:
- EC2 (t3.small): ~$15/month
- SageMaker endpoint (ml.t2.medium): ~$47/month
- **Total**: ~$62/month

### New Setup:
- SageMaker endpoint (ml.t2.medium): ~$47/month
- **Total**: ~$47/month
- **Savings**: $15/month + simpler architecture

## Monitoring

Access metrics at: `https://<endpoint-url>/metrics`

Prometheus metrics include:
- `http_requests_total` - Request count by endpoint
- `http_request_duration_seconds` - Request latency
- `predictions_total` - Total predictions made

## Cleanup

```bash
# Delete endpoint
aws sagemaker delete-endpoint --endpoint-name house-price-prod --region us-east-1

# Delete endpoint config
aws sagemaker delete-endpoint-config --endpoint-config-name <config-name> --region us-east-1

# Delete model
aws sagemaker delete-model --model-name <model-name> --region us-east-1
```

## Benefits of This Approach

✅ **Industry Standard**: FastAPI inside SageMaker endpoint  
✅ **Lower Latency**: No extra network hop  
✅ **Simpler**: Single deployment instead of two  
✅ **Cost Effective**: No separate EC2 needed  
✅ **Scalable**: SageMaker auto-scaling built-in  
✅ **Managed**: AWS handles infrastructure  

## Next Steps

1. Add model versioning
2. Implement A/B testing
3. Add request/response logging
4. Set up CloudWatch alarms
5. Configure auto-scaling policies
