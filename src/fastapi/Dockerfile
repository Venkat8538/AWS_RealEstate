FROM python:3.11-slim

# SageMaker expects model files in /opt/ml/model
WORKDIR /opt/ml/model

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py inference.py schemas.py ./

# Model files will be mounted by SageMaker at /opt/ml/model
# Or you can copy them here during build:
# COPY models/house_price_model.pkl models/preprocessor.pkl ./

# SageMaker uses port 8080
EXPOSE 8080

# Set environment variables for SageMaker
ENV MODEL_PATH=/opt/ml/model/house_price_model.pkl
ENV PREPROCESSOR_PATH=/opt/ml/model/preprocessor.pkl

# Start FastAPI server on port 8080 (SageMaker standard)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
