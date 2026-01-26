#!/usr/bin/env python3
"""
Standalone script to test SageMaker endpoint deployment
Tests only the deployment step without running the full pipeline
"""
import boto3
import sys
from datetime import datetime

def test_endpoint_deployment():
    """Test endpoint deployment with existing model artifacts"""
    
    # Configuration
    REGION = 'us-east-1'
    BUCKET = 'house-price-mlops-dev-itzi2hgi'
    ENDPOINT_NAME = 'house-price-prod'
    MODEL_NAME = f'house-price-model-test-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    ROLE_ARN = 'arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role'
    
    # Check if model exists in S3
    s3 = boto3.client('s3', region_name=REGION)
    sagemaker = boto3.client('sagemaker', region_name=REGION)
    
    print("🔍 Checking for model in S3...")
    model_data_url = f"s3://{BUCKET}/models/trained/model.tar.gz"
    
    try:
        s3.head_object(Bucket=BUCKET, Key='models/trained/model.tar.gz')
        print(f"✅ Found model: {model_data_url}")
    except s3.exceptions.ClientError:
        print(f"❌ Model not found at: {model_data_url}")
        print("💡 Upload model.tar.gz to S3 first")
        return False
    except Exception as e:
        print(f"❌ Error checking model: {e}")
        return False
    
    # Create SageMaker Model
    print(f"\n📦 Creating SageMaker model: {MODEL_NAME}")
    try:
        sagemaker.create_model(
            ModelName=MODEL_NAME,
            PrimaryContainer={
                'Image': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1',
                'ModelDataUrl': model_data_url
            },
            ExecutionRoleArn=ROLE_ARN
        )
        print(f"✅ Model created: {MODEL_NAME}")
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False
    
    # Create Endpoint Configuration
    config_name = f"{ENDPOINT_NAME}-config-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"\n⚙️  Creating endpoint config: {config_name}")
    try:
        sagemaker.create_endpoint_config(
            EndpointConfigName=config_name,
            ProductionVariants=[{
                'VariantName': 'primary',
                'ModelName': MODEL_NAME,
                'InitialInstanceCount': 1,
                'InstanceType': 'ml.t2.medium',
                'InitialVariantWeight': 1.0
            }]
        )
        print(f"✅ Endpoint config created: {config_name}")
    except Exception as e:
        print(f"❌ Endpoint config creation failed: {e}")
        return False
    
    # Create or Update Endpoint
    print(f"\n🚀 Deploying endpoint: {ENDPOINT_NAME}")
    try:
        # Check if endpoint exists
        try:
            endpoint_desc = sagemaker.describe_endpoint(EndpointName=ENDPOINT_NAME)
            status = endpoint_desc['EndpointStatus']
            print(f"📊 Existing endpoint status: {status}")
            
            if status in ['Creating', 'Updating']:
                print(f"⏳ Endpoint is {status}, skipping deployment")
                return True
            elif status == 'Failed':
                print(f"⚠️  Endpoint in Failed state, deleting and recreating...")
                sagemaker.delete_endpoint(EndpointName=ENDPOINT_NAME)
                print("⏳ Waiting 30s for deletion...")
                import time
                time.sleep(30)
                sagemaker.create_endpoint(
                    EndpointName=ENDPOINT_NAME,
                    EndpointConfigName=config_name
                )
                print(f"✅ Endpoint creation initiated")
            elif status == 'InService':
                print("🔄 Updating existing endpoint...")
                sagemaker.update_endpoint(
                    EndpointName=ENDPOINT_NAME,
                    EndpointConfigName=config_name
                )
                print(f"✅ Endpoint update initiated")
            else:
                print(f"⚠️  Endpoint in {status} state, deleting and recreating...")
                sagemaker.delete_endpoint(EndpointName=ENDPOINT_NAME)
                print("⏳ Waiting 30s for deletion...")
                import time
                time.sleep(30)
                sagemaker.create_endpoint(
                    EndpointName=ENDPOINT_NAME,
                    EndpointConfigName=config_name
                )
                print(f"✅ Endpoint creation initiated")
                
        except sagemaker.exceptions.ClientError:
            # Endpoint doesn't exist, create it
            print("📝 Creating new endpoint...")
            sagemaker.create_endpoint(
                EndpointName=ENDPOINT_NAME,
                EndpointConfigName=config_name
            )
            print(f"✅ Endpoint creation initiated")
        
        print(f"\n🎉 Deployment successful!")
        print(f"📍 Endpoint: {ENDPOINT_NAME}")
        print(f"📍 Config: {config_name}")
        print(f"\n⏳ Endpoint is being created/updated (takes 5-10 minutes)")
        print(f"💡 Monitor status: aws sagemaker describe-endpoint --endpoint-name {ENDPOINT_NAME}")
        return True
        
    except Exception as e:
        print(f"❌ Endpoint deployment failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing SageMaker Endpoint Deployment")
    print("=" * 60)
    
    success = test_endpoint_deployment()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - Endpoint deployment initiated")
    else:
        print("❌ TEST FAILED - Check errors above")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
