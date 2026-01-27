#!/usr/bin/env python3
import os
import json
import boto3
import time
from datetime import datetime

def deploy_model():
    sm = boto3.client('sagemaker')
    s3 = boto3.client('s3')
    
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    endpoint_name = os.environ.get('ENDPOINT_NAME', 'house-price-prod')
    model_base_name = os.environ.get('MODEL_NAME', 'house-price-model')
    bucket = os.environ.get('S3_BUCKET', 'house-price-mlops-dev-itzi2hgi')
    role = os.environ.get('SAGEMAKER_ROLE_ARN', 'arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role')
    
    image_uri = f"683313688378.dkr.ecr.{region}.amazonaws.com/sagemaker-xgboost:1.7-1"

    try:
        print("🚀 Starting Deployment Pipeline...")

        # 1. Resolve Model Artifact Path
        model_data_url = os.environ.get('MODEL_DATA_URL')
        if not model_data_url:
            prefixes = s3.list_objects_v2(Bucket=bucket, Prefix='models/trained/pipelines-', Delimiter='/')
            if 'CommonPrefixes' not in prefixes:
                raise FileNotFoundError("No pipeline model artifacts found in S3.")
            latest_folder = sorted([p['Prefix'] for p in prefixes['CommonPrefixes']])[-1]
            model_data_url = f"s3://{bucket}/{latest_folder}output/model.tar.gz"

        # 2. Sync to Static Path
        static_key = "models/trained/model.tar.gz"
        source_key = model_data_url.replace(f"s3://{bucket}/", "")
        s3.copy_object(Bucket=bucket, CopySource={'Bucket': bucket, 'Key': source_key}, Key=static_key)

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

        # 4. Deploy Strategy
        action = "CREATED"
        try:
            desc = sm.describe_endpoint(EndpointName=endpoint_name)
            status = desc['EndpointStatus']
            
            if status == 'Failed':
                print(f"⚠️ Deleting failed endpoint...")
                sm.delete_endpoint(EndpointName=endpoint_name)
                # Wait for deletion to finish
                while True:
                    try:
                        time.sleep(15)
                        sm.describe_endpoint(EndpointName=endpoint_name)
                    except sm.exceptions.ClientError:
                        break # Successfully deleted
                sm.create_endpoint(EndpointName=endpoint_name, EndpointConfigName=unique_config_name)
                action = "RECREATED"
            elif status in ['Creating', 'Updating']:
                print(f"Endpoint is {status}. Exiting script to let it finish.")
                return 
            else:
                sm.update_endpoint(EndpointName=endpoint_name, EndpointConfigName=unique_config_name)
                action = "UPDATED"

        except sm.exceptions.ClientError:
            sm.create_endpoint(EndpointName=endpoint_name, EndpointConfigName=unique_config_name)

        # 5. Monitoring loop (Increased to 20 minutes)
        print(f"⏳ Monitoring {endpoint_name}...")
        for attempt in range(40): 
            time.sleep(30)
            desc = sm.describe_endpoint(EndpointName=endpoint_name)
            status = desc['EndpointStatus']
            print(f"Attempt {attempt+1}/40: {status}")
            
            if status == 'InService':
                break
            elif status == 'Failed':
                raise Exception(f"Deployment failed: {desc.get('FailureReason')}")
        else:
            raise TimeoutError("Endpoint did not reach InService within 20 minutes")

        meta = {"status": "SUCCESS", "action": action, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        meta = {"status": "FAILED", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        raise e
    
    finally:
        os.makedirs("/opt/ml/processing/output", exist_ok=True)
        with open("/opt/ml/processing/output/deployment_metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

if __name__ == "__main__":
    deploy_model()