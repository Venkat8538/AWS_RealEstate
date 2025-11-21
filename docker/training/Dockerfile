FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with MLflow and XGBoost
RUN pip install --no-cache-dir --timeout=300 \
    mlflow==2.8.0 \
    boto3 \
    sagemaker \
    pandas \
    numpy \
    scipy \
    scikit-learn \
    xgboost

# Copy training script
COPY train_model.py /opt/ml/code/train_model.py
COPY mlflow_helper.py /opt/ml/code/mlflow_helper.py

# Set executable permissions and create train entry point
RUN chmod +x /opt/ml/code/train_model.py
RUN echo '#!/bin/bash\npython /opt/ml/code/train_model.py "$@"' > /opt/ml/code/train && chmod +x /opt/ml/code/train

ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/ml/code:${PATH}"