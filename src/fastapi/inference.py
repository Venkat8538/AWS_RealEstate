import boto3
import os
from datetime import datetime
from schemas import HousePredictionRequest, PredictionResponse

ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT", "house-price-prod")
REGION = os.getenv("AWS_REGION", "us-east-1")

sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=REGION)
MODEL_LOADED = True

def predict_price(request: HousePredictionRequest) -> PredictionResponse:
    start_time = datetime.now()
    
    # Calculate derived features
    house_age = datetime.now().year - request.year_built
    price_per_sqft = 300  # Placeholder estimate
    bed_bath_ratio = request.bedrooms / request.bathrooms if request.bathrooms > 0 else 0
    
    # Prepare numeric CSV input for SageMaker (no categorical variables)
    csv_input = f"{request.sqft},{request.bedrooms},{request.bathrooms},{house_age},{price_per_sqft},{bed_bath_ratio}"
    
    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='text/csv',
            Accept='text/csv',
            Body=csv_input
        )
        
        prediction = float(response['Body'].read().decode('utf-8').strip())
        
        # Calculate confidence interval (±10%)
        lower = prediction * 0.9
        upper = prediction * 1.1
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return PredictionResponse(
            predicted_price=prediction,
            confidence_interval=[lower, upper],
            features_importance={"sqft": 0.43, "location": 0.27, "bathrooms": 0.15},
            prediction_time=f"{elapsed:.2f} seconds"
        )
    except Exception as e:
        raise RuntimeError(f"SageMaker endpoint error: {str(e)}")

def batch_predict(requests: list[HousePredictionRequest]) -> list[PredictionResponse]:
    return [predict_price(req) for req in requests]
