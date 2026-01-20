#!/usr/bin/env python3
import os
import json
import boto3
from datetime import datetime

def deploy_model():
    """Deploy trained model to SageMaker endpoint"""
    try:
        print("Model Deployment Started")
        
        # Get environment variables
        endpoint_name = os.environ.get('ENDPOINT_NAME', 'house-price-prod')
        model_name = os.environ.get('MODEL_NAME', 'house-price-model')
        region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Initialize SageMaker client
        sagemaker_client = boto3.client('sagemaker', region_name=region)
        
        # Get model artifacts path - should be passed from training step
        model_data_url = os.environ.get('MODEL_DATA_URL')
        if not model_data_url:
            # Try to find the latest model in S3
            s3_client = boto3.client('s3')
            bucket_name = os.environ.get('S3_BUCKET', 'house-price-mlops-dev-itzi2hgi')
            
            try:
                # List all training job folders
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix='models/trained/pipelines-',
                    Delimiter='/'
                )
                
                if 'CommonPrefixes' in response:
                    # Get the most recent folder (last modified)
                    folders = [prefix['Prefix'] for prefix in response['CommonPrefixes']]
                    latest_folder = sorted(folders)[-1]  # Get latest alphabetically
                    model_data_url = f"s3://{bucket_name}/{latest_folder}output/model.tar.gz"
                    print(f"Found latest model at: {model_data_url}")
                else:
                    raise FileNotFoundError("No training job folders found")
            except Exception as e:
                raise FileNotFoundError(f"Could not find model artifacts: {e}")
        
        print(f"Deploying model from: {model_data_url}")
        
        # Copy model to static Terraform path for consistency
        try:
            s3_client = boto3.client('s3')
            bucket_name = os.environ.get('S3_BUCKET', 'house-price-mlops-dev-itzi2hgi')
            
            # Parse source S3 URL
            source_key = model_data_url.replace(f"s3://{bucket_name}/", "")
            dest_key = "models/trained/model.tar.gz"
            
            # Copy to static path
            s3_client.copy_object(
                Bucket=bucket_name,
                CopySource={'Bucket': bucket_name, 'Key': source_key},
                Key=dest_key
            )
            print(f"Copied model to static path: s3://{bucket_name}/{dest_key}")
        except Exception as e:
            print(f"Warning: Failed to copy model to static path: {e}")
        
        # Create unique names with timestamp
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        model_name_unique = f"{model_name}-{timestamp}"
        endpoint_config_name = f"{endpoint_name}-config-{timestamp}"
        
        # 1. Create SageMaker Model
        try:
            model_response = sagemaker_client.create_model(
                ModelName=model_name_unique,
                PrimaryContainer={
                    'Image': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1-cpu-py3',
                    'ModelDataUrl': model_data_url
                },
                ExecutionRoleArn=os.environ.get('SAGEMAKER_ROLE_ARN', 
                    'arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role')
            )
            print(f"Created model: {model_name_unique}")
            
        except Exception as e:
            print(f"Model creation failed: {e}")
            raise
        
        # 2. Create Endpoint Configuration
        try:
            config_response = sagemaker_client.create_endpoint_config(
                EndpointConfigName=endpoint_config_name,
                ProductionVariants=[
                    {
                        'VariantName': 'primary',
                        'ModelName': model_name_unique,
                        'InitialInstanceCount': 1,
                        'InstanceType': 'ml.t2.medium',
                        'InitialVariantWeight': 1.0
                    }
                ]
            )
            print(f"Created endpoint config: {endpoint_config_name}")
            
        except Exception as e:
            print(f"Endpoint config creation failed: {e}")
            raise
        
        # 3. Create or Update Endpoint
        try:
            # Check if endpoint exists and its status
            try:
                endpoint_desc = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
                endpoint_status = endpoint_desc['EndpointStatus']
                print(f"Endpoint exists with status: {endpoint_status}")
                
                if endpoint_status in ['Creating', 'Updating']:
                    print(f"Endpoint is {endpoint_status}, skipping deployment")
                    deployment_action = "SKIPPED_IN_PROGRESS"
                elif endpoint_status == 'InService':
                    # Endpoint exists and ready, update it
                    update_response = sagemaker_client.update_endpoint(
                        EndpointName=endpoint_name,
                        EndpointConfigName=endpoint_config_name
                    )
                    print(f"Updated existing endpoint: {endpoint_name}")
                    deployment_action = "UPDATED"
                else:
                    print(f"Endpoint in unexpected state: {endpoint_status}")
                    deployment_action = "SKIPPED_UNEXPECTED_STATE"
                    
            except sagemaker_client.exceptions.ClientError as e:
                if 'does not exist' in str(e) or 'ValidationException' in str(e):
                    # Endpoint doesn't exist, create it
                    create_response = sagemaker_client.create_endpoint(
                        EndpointName=endpoint_name,
                        EndpointConfigName=endpoint_config_name
                    )
                    print(f"Created new endpoint: {endpoint_name}")
                    deployment_action = "CREATED"
                else:
                    raise
        
        except Exception as e:
            print(f"Endpoint deployment failed: {e}")
            raise
        
        # Save deployment metadata
        deployment_data = {
            "endpoint_name": endpoint_name,
            "model_name": model_name_unique,
            "endpoint_config_name": endpoint_config_name,
            "model_data_url": model_data_url,
            "deployment_action": deployment_action,
            "deployment_time": datetime.utcnow().isoformat(),
            "status": "DEPLOYING"
        }
        
        os.makedirs("/opt/ml/processing/output", exist_ok=True)
        with open("/opt/ml/processing/output/deployment_metadata.json", "w") as f:
            json.dump(deployment_data, f, indent=2)
        
        print(f"Model deployment initiated successfully")
        print(f"Endpoint: {endpoint_name}")
        print(f"Action: {deployment_action}")
        print(f"Config: {endpoint_config_name}")
        
    except Exception as e:
        print(f"Deployment failed: {e}")
        
        # Save failure metadata
        failure_data = {
            "endpoint_name": endpoint_name,
            "deployment_action": "FAILED",
            "error": str(e),
            "deployment_time": datetime.utcnow().isoformat(),
            "status": "FAILED"
        }
        
        os.makedirs("/opt/ml/processing/output", exist_ok=True)
        with open("/opt/ml/processing/output/deployment_metadata.json", "w") as f:
            json.dump(failure_data, f, indent=2)
        
        raise

if __name__ == "__main__":
    deploy_model()