from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from inference import predict_price, batch_predict, MODEL_LOADED
from schemas import HousePredictionRequest, PredictionResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

# Initialize FastAPI app with metadata
app = FastAPI(
    title="House Price Prediction API",
    description=(
        "An API for predicting house prices based on various features. "
        "This application is part of the MLOps Bootcamp by School of Devops. "
        "Authored by Gourav Shah."
    ),
    version="2.1.0",
    contact={
        "name": "School of Devops",
        "url": "https://schoolofdevops.com",
        "email": "learn@schoolofdevops.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
PREDICTION_COUNT = Counter('predictions_total', 'Total predictions made')

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Root endpoint
@app.get("/")
async def root():
    REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
    return {"message": "House Price Prediction API", "docs": "/docs", "health": "/health"}

# Health check endpoint
@app.get("/health", response_model=dict)
async def health_check():
    REQUEST_COUNT.labels(method='GET', endpoint='/health').inc()
    return {"status": "healthy", "model_loaded": MODEL_LOADED}

# Prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: HousePredictionRequest):
    start_time = time.time()
    REQUEST_COUNT.labels(method='POST', endpoint='/predict').inc()
    PREDICTION_COUNT.inc()
    
    result = predict_price(request)
    
    REQUEST_DURATION.observe(time.time() - start_time)
    return result

# Batch prediction endpoint
@app.post("/batch-predict", response_model=list)
async def batch_predict_endpoint(requests: list[HousePredictionRequest]):
    return batch_predict(requests)