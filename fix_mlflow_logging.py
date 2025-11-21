#!/usr/bin/env python3
"""
Quick Fix for MLflow Logging in SageMaker Pipeline
This script demonstrates the correct way to log to MLflow from SageMaker
"""

import os
import mlflow
import boto3
from datetime import datetime

def setup_mlflow_for_sagemaker():
    """
    Setup MLflow for SageMaker with S3 backend
    This is the pattern your training scripts should follow
    """
    
    # Get S3 tracking URI from environment (set by SageMaker pipeline)
    tracking_uri = os.environ.get('MLFLOW_TRACKING_URI')
    
    if not tracking_uri:
        print("❌ MLFLOW_TRACKING_URI not set in environment")
        return False
    
    if not tracking_uri.startswith('s3://'):
        print(f"❌ Invalid tracking URI: {tracking_uri}. Must be S3 URI.")
        return False
    
    try:
        print(f"🔧 Setting MLflow tracking URI to: {tracking_uri}")
        mlflow.set_tracking_uri(tracking_uri)
        
        # Set experiment
        experiment_name = "house-price-prediction"
        try:
            mlflow.set_experiment(experiment_name)
            print(f"✅ Using experiment: {experiment_name}")
        except Exception:
            # Create experiment if it doesn't exist
            experiment_id = mlflow.create_experiment(experiment_name)
            mlflow.set_experiment(experiment_name)
            print(f"✅ Created experiment: {experiment_name} (ID: {experiment_id})")
        
        return True
        
    except Exception as e:
        print(f"❌ MLflow setup failed: {e}")
        return False

def log_sagemaker_job_example():
    """
    Example of how to log from SageMaker job
    """
    
    if not setup_mlflow_for_sagemaker():
        return False
    
    try:
        # Start MLflow run
        with mlflow.start_run(run_name=f"sagemaker_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            
            # Log parameters (hyperparameters, config, etc.)
            mlflow.log_param("instance_type", "ml.m5.large")
            mlflow.log_param("framework", "xgboost")
            mlflow.log_param("objective", "reg:squarederror")
            
            # Log metrics (performance metrics)
            mlflow.log_metric("train_rmse", 45000.0)
            mlflow.log_metric("train_r2", 0.85)
            mlflow.log_metric("validation_rmse", 47000.0)
            
            # Log additional info
            mlflow.log_param("sagemaker_job_name", os.environ.get('TRAINING_JOB_NAME', 'unknown'))
            mlflow.log_param("aws_region", os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
            
            print("✅ Successfully logged to MLflow S3 backend")
            
            # Get run info
            run = mlflow.active_run()
            print(f"📊 Run ID: {run.info.run_id}")
            print(f"🧪 Experiment ID: {run.info.experiment_id}")
            
        return True
        
    except Exception as e:
        print(f"❌ MLflow logging failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 MLflow SageMaker Logging Fix")
    print("=" * 40)
    
    # Simulate SageMaker environment
    if 'MLFLOW_TRACKING_URI' not in os.environ:
        # Set a test S3 URI (replace with your actual bucket)
        bucket_name = "your-sagemaker-bucket"  # Replace with actual bucket
        os.environ['MLFLOW_TRACKING_URI'] = f"s3://{bucket_name}/mlflow-artifacts"
        print(f"🧪 Test mode: Using S3 URI: {os.environ['MLFLOW_TRACKING_URI']}")
    
    # Test the logging
    success = log_sagemaker_job_example()
    
    if success:
        print("\n🎉 MLflow logging is working!")
        print("Your SageMaker pipeline should now log runs and experiments.")
    else:
        print("\n⚠️ MLflow logging failed. Check:")
        print("1. AWS credentials are configured")
        print("2. S3 bucket exists and is accessible")
        print("3. MLFLOW_TRACKING_URI is set correctly")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)