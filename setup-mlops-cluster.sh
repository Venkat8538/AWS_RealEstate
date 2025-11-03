#!/bin/bash

echo "🚀 Setting up MLOps cluster with Airflow + MLflow + SageMaker"

# Create Kind cluster
echo "📦 Creating Kind cluster..."
kind create cluster --config k8s/kind-config.yaml

# Create AWS credentials secret
echo "🔐 Creating AWS credentials secret..."
kubectl create secret generic aws-credentials \
  --from-literal=access-key-id="$AWS_ACCESS_KEY_ID" \
  --from-literal=secret-access-key="$AWS_SECRET_ACCESS_KEY"

# Deploy PostgreSQL
echo "🐘 Deploying PostgreSQL..."
kubectl apply -f k8s/postgres/postgres.yaml

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres

# Deploy MLflow
echo "📊 Deploying MLflow..."
kubectl apply -f k8s/mlflow/mlflow.yaml

# Deploy Airflow
echo "🌪️ Deploying Airflow..."
kubectl apply -f k8s/airflow/airflow.yaml

echo "✅ MLOps cluster setup complete!"
echo ""
echo "🌐 Access URLs:"
echo "   Airflow UI: http://localhost:8083 (admin/admin123)"
echo "   MLflow UI:  http://localhost:5001"
echo ""
echo "📋 Useful commands:"
echo "   kubectl get pods"
echo "   kubectl logs -f deployment/airflow-webserver"
echo "   kubectl logs -f deployment/mlflow"