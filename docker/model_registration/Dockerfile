FROM python:3.10-slim

# Install basic dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (MLflow + AWS SDK + helpers)
RUN pip install --no-cache-dir --timeout=300 mlflow==2.8.0
RUN pip install --no-cache-dir boto3 sagemaker pandas numpy scipy

ENV PYTHONUNBUFFERED=1