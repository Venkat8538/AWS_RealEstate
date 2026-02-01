from pydantic import BaseModel
from typing import Optional

class HousePredictionRequest(BaseModel):
    sqft: float
    bedrooms: int
    bathrooms: float
    location: str
    year_built: int
    condition: str

class PredictionResponse(BaseModel):
    predicted_price: float
    confidence_interval: list[float]
    features_importance: dict
    prediction_time: str
