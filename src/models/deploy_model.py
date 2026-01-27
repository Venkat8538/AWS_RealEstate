#!/usr/bin/env python3
import os
import json
import boto3
import time
from datetime import datetime

def deploy_model():
    """Deploy trained model to SageMaker endpoint with status monitoring"""
    sm = boto3.client('sagemaker')
    s3 = boto3.client('s3')
    
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    endpoint_name = os.environ.get('ENDPOINT_NAME', 'house-price-prod')
    model_base_name = os.environ.get('MODEL_NAME', 'house-price-model')
    bucket = os.environ.get('S3_BUCKET', 'house-price-mlops-dev-itzi2hgi')
    role = os.environ.get('SAGEMAKER_ROLE_ARN', 'arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role')
    
    # Image URI for XGBoost 1.7-1
    image_uri = f"683313688378.dkr.ecr.{region}.amazonaws.com/sagemaker-xgboost:1.7-1"

    try:
        print("🚀 Starting Deployment Pipeline...")

        # 1. Resolve Model Artifact Path
        model_data_url = os.environ.get('MODEL_DATA_URL')
        if not model_data_url:
            print("Searching for latest model in S3...")
            prefixes = s3.list_objects_v2(Bucket=bucket, Prefix='models/trained/pipelines-', Delimiter='/')
            if 'CommonPrefixes' not in prefixes:
                raise FileNotFoundError("No pipeline model artifacts found in S3.")
            
            latest_folder = sorted([p['Prefix'] for p in prefixes['CommonPrefixes']])[-1]
            model_data_url = f"s3://{bucket}/{latest_folder}output/model.tar.gz"

        # 2. Sync to Static Path (Terraform/Ops consistency)
        static_key = "models/trained/model.tar.gz"
        source_key = model_data_url.replace(f"s3://{bucket}/", "")
        s3.copy_object(Bucket=bucket, CopySource={'Bucket': bucket, 'Key': source_key}, Key=static_key)
        print(f"✅ Model synced: {model_data_url} -> s3://{bucket}/{static_key}")

        # 3. Create Unique Resources
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        unique_model_name = f"{model_base_name}-{ts}"
        unique_config_name = f"{endpoint_name}-config-{ts}"

        sm.create_model(
            ModelName=unique_model_name,
            PrimaryContainer={'Image': image_uri, 'ModelDataUrl': model_data_url},
            ExecutionRoleArn=role
        )

        sm.create_endpoint_config(
            EndpointConfigName=unique_config_name,
            ProductionVariants=[{
                'VariantName': 'primary',
                'ModelName': unique_model_name,
                'InitialInstanceCount': 1,
                'InstanceType': 'ml.t2.medium'
            }]
        )

        # 4. Deploy/Update Strategy
        try:
            desc = sm.describe_endpoint(EndpointName=endpoint_name)
            status = desc['EndpointStatus']
            print(f"Current Endpoint Status: {status}")

            if status == 'Failed':
                failure_reason = desc.get('FailureReason', 'Unknown')
                print(f"⚠️ Endpoint Failed Previously: {failure_reason}")
                print("Deleting failed endpoint...")
                sm.delete_endpoint(EndpointName=endpoint_name)
                time.sleep(30)
                sm.create_endpoint(EndpointName=endpoint_name, EndpointConfigName=unique_config_name)
                action = "RECREATED"
            elif status in ['Creating', 'Updating']:
                print(f"Endpoint already {status}, skipping deployment")
                return
            else:
                print(f"Updating endpoint to config: {unique_config_name}")
                sm.update_endpoint(EndpointName=endpoint_name, EndpointConfigName=unique_config_name)
                action = "UPDATED"

        except sm.exceptions.ClientError:
            print("Creating new endpoint...")
            sm.create_endpoint(EndpointName=endpoint_name, EndpointConfigName=unique_config_name)
            action = "CREATED"

        # 5. Monitor deployment with early failure detection
        print(f"⏳ Monitoring endpoint {endpoint_name}...")
        for attempt in range(15):  # 7.5 minutes max
            time.sleep(30)
            desc = sm.describe_endpoint(EndpointName=endpoint_name)
            status = desc['EndpointStatus']
            print(f"Attempt {attempt+1}/15: Status = {status}")
            
            if status == 'InService':
                print("✅ Endpoint is InService")
                break
            elif status == 'Failed':
                failure_reason = desc.get('FailureReason', 'Unknown')
                raise Exception(f"Endpoint deployment failed: {failure_reason}")
        else:
            raise TimeoutError("Endpoint did not reach InService within 7.5 minutes")

        # 6. Final Metadata
        meta = {
            "endpoint_name": endpoint_name,
            "model_name": unique_model_name,
            "action": action,
            "status": "SUCCESS",
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"✅ Deployment Complete! Status: {action}")

    except Exception as e:
        print(f"❌ Deployment Failed: {str(e)}")
        meta = {"status": "FAILED", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        raise e
    
    finally:
        out_path = "/opt/ml/processing/output"
        os.makedirs(out_path, exist_ok=True)
        with open(f"{out_path}/deployment_metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

if __name__ == "__main__":
    deploy_model()