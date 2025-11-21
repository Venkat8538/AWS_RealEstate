#!/usr/bin/env python3
"""
Verify MLflow S3 Backend Configuration
Tests if MLflow can connect to S3 backend and log experiments
"""

import os
import boto3
import mlflow
from datetime import datetime

def test_s3_access(bucket_name):
    """Test S3 bucket access"""
    try:
        s3 = boto3.client('s3')
        response = s3.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket '{bucket_name}' is accessible")
        return True
    except Exception as e:
        print(f"❌ S3 bucket access failed: {e}")
        return False

def test_mlflow_s3_backend(s3_uri):
    """Test MLflow with S3 backend"""
    try:
        print(f"Testing MLflow with S3 URI: {s3_uri}")
        
        # Set tracking URI
        mlflow.set_tracking_uri(s3_uri)
        print(f"✅ Set MLflow tracking URI to: {s3_uri}")
        
        # Create/get experiment
        experiment_name = "house-price-prediction"
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
                print(f"✅ Created experiment: {experiment_name} (ID: {experiment_id})")
            else:
                print(f"✅ Using existing experiment: {experiment_name}")
        except Exception as e:
            print(f"⚠️ Experiment setup issue: {e}")
        
        mlflow.set_experiment(experiment_name)
        
        # Test logging
        with mlflow.start_run(run_name=f"s3_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            mlflow.log_param("test_param", "s3_backend_test")
            mlflow.log_metric("test_metric", 1.0)
            mlflow.log_metric("timestamp", datetime.now().timestamp())
            
            print("✅ Successfully logged test run to MLflow S3 backend")
            
            # Get run info
            run = mlflow.active_run()
            print(f"✅ Run ID: {run.info.run_id}")
            print(f"✅ Experiment ID: {run.info.experiment_id}")
            
        return True
        
    except Exception as e:
        print(f"❌ MLflow S3 backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 Verifying MLflow S3 Backend Setup")
    print("=" * 50)
    
    # Get S3 bucket from environment or use default
    bucket_name = os.environ.get('S3_BUCKET_NAME', 'your-sagemaker-bucket')
    s3_uri = f"s3://{bucket_name}/mlflow-artifacts"
    
    print(f"S3 Bucket: {bucket_name}")
    print(f"MLflow S3 URI: {s3_uri}")
    print()
    
    # Test 1: S3 Access
    print("Test 1: S3 Bucket Access")
    s3_ok = test_s3_access(bucket_name)
    print()
    
    # Test 2: MLflow S3 Backend
    print("Test 2: MLflow S3 Backend")
    mlflow_ok = test_mlflow_s3_backend(s3_uri)
    print()
    
    # Summary
    print("=" * 50)
    print("SUMMARY:")
    print(f"S3 Access: {'✅ PASS' if s3_ok else '❌ FAIL'}")
    print(f"MLflow S3 Backend: {'✅ PASS' if mlflow_ok else '❌ FAIL'}")
    
    if s3_ok and mlflow_ok:
        print("\n🎉 MLflow S3 backend is working correctly!")
        print("Your SageMaker pipeline should now log to MLflow.")
    else:
        print("\n⚠️ Issues detected. Check AWS credentials and S3 permissions.")
        
    return s3_ok and mlflow_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)