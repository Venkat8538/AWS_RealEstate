#!/usr/bin/env python3
"""
Test SageMaker Pipeline locally
"""

import boto3
from create_ml_pipeline import create_ml_pipeline, get_pipeline_config

def test_pipeline_creation():
    """Test pipeline creation without execution"""
    try:
        print("🧪 Testing pipeline creation...")
        pipeline, config = create_ml_pipeline()
        
        print(f"✅ Pipeline created: {pipeline.name}")
        print(f"✅ Steps: {len(pipeline.steps)}")
        print(f"✅ Parameters: {len(pipeline.parameters)}")
        
        # Validate pipeline definition
        pipeline_def = pipeline.definition()
        print(f"✅ Pipeline definition generated ({len(pipeline_def)} chars)")
        
        return True
    except Exception as e:
        print(f"❌ Pipeline creation failed: {e}")
        return False

def test_aws_connectivity():
    """Test AWS connectivity and permissions"""
    try:
        config = get_pipeline_config()
        
        # Test SageMaker access
        sagemaker = boto3.client('sagemaker')
        sagemaker.list_pipelines(MaxResults=1)
        print("✅ SageMaker access OK")
        
        # Test S3 access
        s3 = boto3.client('s3')
        s3.head_bucket(Bucket=config['bucket'].replace('s3://', '').split('/')[0])
        print("✅ S3 access OK")
        
        return True
    except Exception as e:
        print(f"❌ AWS connectivity failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing SageMaker Pipeline Setup\n")
    
    # Test 1: AWS connectivity
    if not test_aws_connectivity():
        exit(1)
    
    # Test 2: Pipeline creation
    if not test_pipeline_creation():
        exit(1)
    
    print("\n✅ All tests passed! Ready to deploy pipeline.")