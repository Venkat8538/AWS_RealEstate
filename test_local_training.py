#!/usr/bin/env python3
"""
Test model training locally using Docker (simulates SageMaker)
Then deploy to test endpoint
"""
import subprocess
import os
import boto3

BUCKET = 'house-price-mlops-dev-itzi2hgi'
REGION = 'us-east-1'

print("🧪 Local Training + Deployment Test")
print("=" * 60)

# 1. Train using XGBoost container locally
print("\n📦 Training with XGBoost 1.7 container...")
subprocess.run([
    'docker', 'run', '--rm',
    '-v', f'{os.getcwd()}/data/processed:/opt/ml/input/data/train',
    '-v', f'{os.getcwd()}/model_output:/opt/ml/model',
    '-v', f'{os.getcwd()}/src/models:/opt/ml/code',
    '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1',
    'train',
    '--num_round', '50'
], check=True)

# 2. Package model
print("\n📦 Creating model.tar.gz...")
subprocess.run(['tar', '-czf', 'model.tar.gz', '-C', 'model_output', '.'], check=True)

# 3. Upload to S3
print("\n☁️  Uploading to S3...")
s3 = boto3.client('s3', region_name=REGION)
s3.upload_file('model.tar.gz', BUCKET, 'models/trained/model.tar.gz')

print("\n✅ Model uploaded!")
print("\n🚀 Testing deployment...")

# 4. Run deployment test
subprocess.run(['python3', 'test_endpoint_deployment.py'], check=True)
