#!/usr/bin/env python3
"""
MLflow Configuration and Setup Utilities
Ensures consistent MLflow tracking across SageMaker and Airflow
"""

import os
import mlflow
from typing import Optional

def setup_mlflow_tracking(
    tracking_uri: Optional[str] = None,
    experiment_name: str = "house-price-prediction"
) -> bool:
    """
    Setup MLflow tracking with fallback URIs
    
    Args:
        tracking_uri: Optional MLflow tracking URI
        experiment_name: Name of the MLflow experiment
        
    Returns:
        bool: True if setup successful, False otherwise
    """
    # Define fallback URIs in order of preference
    uris_to_try = [
        tracking_uri,
        os.environ.get('MLFLOW_TRACKING_URI'),
        "http://mlflow-service:5000",  # Kubernetes service
        "http://localhost:5001",       # Local development
        "http://127.0.0.1:5000"       # Default MLflow
    ]
    
    # Filter out None values
    uris_to_try = [uri for uri in uris_to_try if uri is not None]
    
    for uri in uris_to_try:
        try:
            print(f"Attempting to connect to MLflow at: {uri}")
            mlflow.set_tracking_uri(uri)
            
            # Test connection by listing experiments
            mlflow.search_experiments()
            
            print(f"✅ Successfully connected to MLflow at: {uri}")
            
            # Setup experiment
            try:
                experiment = mlflow.get_experiment_by_name(experiment_name)
                if experiment is None:
                    experiment_id = mlflow.create_experiment(experiment_name)
                    print(f"Created new experiment: {experiment_name} (ID: {experiment_id})")
                else:
                    print(f"Using existing experiment: {experiment_name}")
                
                mlflow.set_experiment(experiment_name)
                return True
                
            except Exception as exp_error:
                print(f"Experiment setup failed: {exp_error}")
                return False
                
        except Exception as e:
            print(f"Failed to connect to {uri}: {e}")
            continue
    
    print("❌ Could not connect to any MLflow server")
    return False

def log_sagemaker_job_info(job_name: str, job_type: str = "training"):
    """
    Log SageMaker job information to MLflow
    
    Args:
        job_name: SageMaker job name
        job_type: Type of job (training, processing, etc.)
    """
    try:
        with mlflow.start_run(run_name=f"sagemaker_{job_type}_{job_name}"):
            mlflow.log_param("sagemaker_job_name", job_name)
            mlflow.log_param("sagemaker_job_type", job_type)
            mlflow.log_param("aws_region", os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
            
            # Log environment info
            mlflow.log_param("python_version", os.sys.version.split()[0])
            mlflow.log_param("mlflow_version", mlflow.__version__)
            
            print(f"Logged SageMaker {job_type} job: {job_name}")
            
    except Exception as e:
        print(f"Failed to log SageMaker job info: {e}")

def get_mlflow_run_context():
    """
    Get current MLflow run context information
    
    Returns:
        dict: Run context information
    """
    try:
        active_run = mlflow.active_run()
        if active_run:
            return {
                "run_id": active_run.info.run_id,
                "experiment_id": active_run.info.experiment_id,
                "status": active_run.info.status,
                "tracking_uri": mlflow.get_tracking_uri()
            }
        else:
            return {"status": "no_active_run", "tracking_uri": mlflow.get_tracking_uri()}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Test MLflow setup
    success = setup_mlflow_tracking()
    if success:
        print("MLflow setup test completed successfully")
        
        # Test logging
        with mlflow.start_run(run_name="config_test"):
            mlflow.log_param("test_param", "config_test_value")
            mlflow.log_metric("test_metric", 1.0)
            print("Test logging completed")
    else:
        print("MLflow setup test failed")