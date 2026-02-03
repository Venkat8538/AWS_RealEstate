import joblib
import pandas as pd
from datetime import datetime
from schemas import HousePredictionRequest, PredictionResponse
import os

# Load model locally (not from SageMaker endpoint)
MODEL_PATH = os.getenv("MODEL_PATH", "/opt/ml/model/house_price_model.pkl")
PREPROCESSOR_PATH = os.getenv("PREPROCESSOR_PATH", "/opt/ml/model/preprocessor.pkl")

try:
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    MODEL_LOADED = True
except Exception as e:
    print(f"Warning: Could not load model: {e}")
    model = None
    preprocessor = None
    MODEL_LOADED = False

def predict_price(request: HousePredictionRequest) -> PredictionResponse:
    if not MODEL_LOADED:
        raise RuntimeError("Model not loaded")
    
    start_time = datetime.now()
    
    # Calculate derived features
    house_age = datetime.now().year - request.year_built
    price_per_sqft = 300  # Placeholder
    bed_bath_ratio = request.bedrooms / request.bathrooms if request.bathrooms > 0 else 0
    
    # Create DataFrame with all features
    input_data = pd.DataFrame([{
        'sqft': request.sqft,
        'bedrooms': request.bedrooms,
        'bathrooms': request.bathrooms,
        'location': request.location,
        'year_built': request.year_built,
        'condition': request.condition,
        'house_age': house_age,
        'price_per_sqft': price_per_sqft,
        'bed_bath_ratio': bed_bath_ratio
    }])
    
    # Preprocess and predict
    X_processed = preprocessor.transform(input_data)
    prediction = float(model.predict(X_processed)[0])
    
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

def batch_predict(requests: list[HousePredictionRequest]) -> list[PredictionResponse]:
    return [predict_price(req) for req in requests]
