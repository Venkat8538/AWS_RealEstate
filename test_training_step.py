#!/usr/bin/env python3
"""
Run ONLY SageMaker training job (not full pipeline)
Then test endpoint deployment
"""
import boto3
import time
from datetime import datetime

REGION = 'us-east-1'
BUCKET = 'house-price-mlops-dev-itzi2hgi'
ROLE_ARN = 'arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role'

sagemaker = boto3.client('sagemaker', region_name=REGION)

print("🚀 Quick Training Job Test")
print("=" * 60)

# 1. Start training job
job_name = f"quick-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
print(f"\n📦 Starting training job: {job_name}")

sagemaker.create_training_job(
    TrainingJobName=job_name,
    RoleArn=ROLE_ARN,
    AlgorithmSpecification={
        'TrainingImage': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1',
        'TrainingInputMode': 'File'
    },
    InputDataConfig=[{
        'ChannelName': 'train',
        'DataSource': {
            'S3DataSource': {
                'S3DataType': 'S3Prefix',
                'S3Uri': f's3://{BUCKET}/data/processed/',
                'S3DataDistributionType': 'FullyReplicated'
            }
        },
        'ContentType': 'text/csv'
    }],
    OutputDataConfig={
        'S3OutputPath': f's3://{BUCKET}/models/trained'
    },
    ResourceConfig={
        'InstanceType': 'ml.m5.large',
        'InstanceCount': 1,
        'VolumeSizeInGB': 30
    },
    StoppingCondition={'MaxRuntimeInSeconds': 3600},
    HyperParameters={
        'sagemaker_program': 'train_model.py',
        'sagemaker_submit_directory': f's3://{BUCKET}/scripts/scripts.tar.gz',
        'objective': 'reg:squarederror',
        'num_round': '50'
    }
)

# 2. Wait for completion
print("\n⏳ Waiting for training to complete...")
while True:
    status = sagemaker.describe_training_job(TrainingJobName=job_name)
    state = status['TrainingJobStatus']
    print(f"   Status: {state}")
    
    if state in ['Completed', 'Failed', 'Stopped']:
        break
    time.sleep(30)

if state == 'Completed':
    model_url = status['ModelArtifacts']['S3ModelArtifacts']
    print(f"\n✅ Training complete!")
    print(f"📦 Model: {model_url}")
    
    # 3. Test deployment
    print("\n🚀 Testing endpoint deployment...")
    import subprocess
    subprocess.run(['python3', 'test_endpoint_deployment.py'])
else:
    print(f"\n❌ Training {state}")
