FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with MLflow
RUN pip install --no-cache-dir --timeout=300 \
    mlflow==2.8.0 \
    boto3 \
    pandas \
    numpy \
    scikit-learn

ENV PYTHONUNBUFFERED=1