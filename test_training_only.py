#!/usr/bin/env python3
"""
Quick test: Train model locally and upload to S3
"""
import boto3
import subprocess
import os

BUCKET = 'house-price-mlops-dev-itzi2hgi'
REGION = 'us-east-1'

print("🚀 Quick Training Test")
print("=" * 60)

# 1. Train locally (uses data/processed/cleaned_house_data.csv)
print("\n📦 Training model locally...")
os.chdir('/Users/venkat/Documents/devops/AWS_RealEstate')

# Create minimal training data
subprocess.run([
    'python3', 'src/models/train_model.py',
    '--num_round', '50'
], env={**os.environ, 'TRAIN_CHANNEL': 'data/processed'})

# 2. Package model
print("\n📦 Packaging model...")
subprocess.run(['tar', '-czf', 'model.tar.gz', '-C', '/opt/ml/model', 'xgboost-model'])

# 3. Upload to S3
print("\n☁️  Uploading to S3...")
s3 = boto3.client('s3', region_name=REGION)
s3.upload_file('model.tar.gz', BUCKET, 'models/trained/model.tar.gz')

print("\n✅ Model ready at: s3://{}/models/trained/model.tar.gz".format(BUCKET))
print("\n💡 Now run: python3 test_endpoint_deployment.py")
