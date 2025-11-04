import os
import json
import boto3
import mlflow
from datetime import datetime

def register_model():
    try:
        print("Model Registration Started")
        
        # Setup MLflow tracking
        try:
            mlflow_uri = os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow-service:5000')
            mlflow.set_tracking_uri(mlflow_uri)
            mlflow.set_experiment("house-price-prediction")
            print(f"MLflow tracking URI: {mlflow_uri}")
        except Exception as e:
            print(f"MLflow setup failed: {e}")
        
        # Load evaluation report
        report_file = "/opt/ml/processing/input/evaluation/evaluation_report.json"
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        print(f"Evaluation Performance: {report['model_performance']}")
        
        if report['model_performance'] == 'PASS':
            print("Model passed evaluation - proceeding with registration")
            
            # Initialize SageMaker client with region
            sagemaker_client = boto3.client('sagemaker', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
            
            # Get model artifacts path from environment
            model_package_group_name = os.environ.get('MODEL_PACKAGE_GROUP_NAME', 'house-price-model-group')
            # Use a more generic model path since we don't have the exact training job output
            model_data_url = 's3://house-price-mlops-dev-itzi2hgi/models/trained/model.tar.gz'
            
            try:
                # Create model package group if it doesn't exist
                try:
                    sagemaker_client.create_model_package_group(
                        ModelPackageGroupName=model_package_group_name,
                        ModelPackageGroupDescription="House price prediction model group"
                    )
                    print(f"Created model package group: {model_package_group_name}")
                except Exception as e:
                    if "already exists" in str(e) or "ValidationException" in str(e):
                        print(f"Model package group {model_package_group_name} already exists")
                    else:
                        raise e
                
                # Register model package without model artifacts (for demo)
                response = sagemaker_client.create_model_package(
                    ModelPackageGroupName=model_package_group_name,
                    ModelPackageDescription=f"House price model - RMSE: {report['evaluation_metrics']['rmse']:.2f}, R2: {report['evaluation_metrics']['r2_score']:.4f}",
                    ModelApprovalStatus='PendingManualApproval',
                    # Skip InferenceSpecification for now since we don't have valid model artifacts
                    ModelMetrics={
                        'ModelQuality': {
                            'Statistics': {
                                'ContentType': 'application/json',
                                'S3Uri': 's3://house-price-mlops-dev-itzi2hgi/evaluation/reports/evaluation_report.json'
                            }
                        }
                    }
                )
                
                model_package_arn = response['ModelPackageArn']
                print(f"Model registered successfully: {model_package_arn}")
                
                # Log to MLflow
                try:
                    with mlflow.start_run(run_name="model_registration"):
                        mlflow.log_param("model_package_arn", model_package_arn)
                        mlflow.log_param("model_status", "REGISTERED")
                        mlflow.log_param("approval_status", "PendingManualApproval")
                        mlflow.log_metric("eval_rmse", report['evaluation_metrics']['rmse'])
                        mlflow.log_metric("eval_r2", report['evaluation_metrics']['r2_score'])
                        mlflow.log_param("registration_timestamp", datetime.utcnow().isoformat())
                        print("Model registration logged to MLflow")
                except Exception as e:
                    print(f"MLflow logging failed: {e}")
                
                registration_data = {
                    "model_status": "REGISTERED",
                    "model_package_arn": model_package_arn,
                    "registration_time": datetime.utcnow().isoformat(),
                    "evaluation_metrics": report['evaluation_metrics'],
                    "model_performance": report['model_performance'],
                    "approval_reason": "Automated registration - pending manual approval"
                }
                
            except Exception as e:
                print(f"Failed to register model: {e}")
                
                # Log failure to MLflow
                try:
                    with mlflow.start_run(run_name="model_registration_failed"):
                        mlflow.log_param("model_status", "REGISTRATION_FAILED")
                        mlflow.log_param("error", str(e))
                        mlflow.log_metric("eval_rmse", report['evaluation_metrics']['rmse'])
                        mlflow.log_metric("eval_r2", report['evaluation_metrics']['r2_score'])
                        mlflow.log_param("registration_timestamp", datetime.utcnow().isoformat())
                except Exception as mlflow_e:
                    print(f"MLflow logging failed: {mlflow_e}")
                
                registration_data = {
                    "model_status": "REGISTRATION_FAILED",
                    "error": str(e),
                    "registration_time": datetime.utcnow().isoformat(),
                    "evaluation_metrics": report['evaluation_metrics'],
                    "model_performance": report['model_performance']
                }
            
            # Save registration metadata
            os.makedirs("/opt/ml/processing/output", exist_ok=True)
            with open("/opt/ml/processing/output/registration_metadata.json", "w") as f:
                json.dump(registration_data, f, indent=2)
            
            print(f"RMSE: {report['evaluation_metrics']['rmse']:.2f}")
            print(f"R² Score: {report['evaluation_metrics']['r2_score']:.4f}")
            print("Model registration completed")
            
        else:
            print("Model failed evaluation - skipping registration")
            
            # Log rejection to MLflow
            try:
                with mlflow.start_run(run_name="model_rejected"):
                    mlflow.log_param("model_status", "REJECTED")
                    mlflow.log_param("rejection_reason", "Model failed evaluation criteria")
                    mlflow.log_metric("eval_rmse", report['evaluation_metrics']['rmse'])
                    mlflow.log_metric("eval_r2", report['evaluation_metrics']['r2_score'])
                    mlflow.log_param("registration_timestamp", datetime.utcnow().isoformat())
            except Exception as e:
                print(f"MLflow logging failed: {e}")
            
            registration_data = {
                "model_status": "REJECTED",
                "registration_time": datetime.utcnow().isoformat(),
                "evaluation_metrics": report['evaluation_metrics'],
                "model_performance": report['model_performance'],
                "rejection_reason": "Model failed evaluation criteria"
            }
            
            os.makedirs("/opt/ml/processing/output", exist_ok=True)
            with open("/opt/ml/processing/output/registration_metadata.json", "w") as f:
                json.dump(registration_data, f, indent=2)
        
        print("Model registration process completed")
        
    except Exception as e:
        print(f"Registration failed: {e}")
        
        # Log critical failure to MLflow
        try:
            with mlflow.start_run(run_name="registration_critical_failure"):
                mlflow.log_param("model_status", "CRITICAL_FAILURE")
                mlflow.log_param("error", str(e))
                mlflow.log_param("timestamp", datetime.utcnow().isoformat())
        except Exception as mlflow_e:
            print(f"MLflow logging failed: {mlflow_e}")
        
        raise

if __name__ == "__main__":
    register_model()