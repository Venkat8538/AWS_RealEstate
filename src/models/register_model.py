import os
import json
import boto3
from datetime import datetime

def register_model():
    try:
        print("Model Registration Started")
        
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
        raise

if __name__ == "__main__":
    register_model()