#!/bin/bash

# Fix MLflow logging in SageMaker Pipeline
set -e

echo "🔧 Fixing MLflow logging in SageMaker Pipeline"
echo "=============================================="

# Get AWS account info
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"

# Step 1: Build and push containers
echo ""
echo "📦 Step 1: Building and pushing MLflow-enabled containers..."
./build_mlflow_containers.sh

# Step 2: Verify containers are pushed
echo ""
echo "🔍 Step 2: Verifying containers in ECR..."
for repo in "data-processing" "feature-engineering" "training" "evaluation" "model-registration"; do
    image_count=$(aws ecr list-images --repository-name $repo --region $AWS_REGION --query 'length(imageIds)' --output text 2>/dev/null || echo "0")
    if [ "$image_count" -gt 0 ]; then
        echo "✅ $repo: $image_count images found"
    else
        echo "❌ $repo: No images found"
    fi
done

# Step 3: Check MLflow S3 backend
echo ""
echo "🗄️  Step 3: Checking MLflow S3 backend..."
S3_BUCKET="house-price-mlops-dev-itzi2hgi"
MLFLOW_PATH="s3://$S3_BUCKET/mlflow-artifacts"

# Check if S3 bucket exists
if aws s3 ls "s3://$S3_BUCKET" >/dev/null 2>&1; then
    echo "✅ S3 bucket exists: $S3_BUCKET"
    
    # Check MLflow artifacts path
    if aws s3 ls "$MLFLOW_PATH/" >/dev/null 2>&1; then
        echo "✅ MLflow artifacts path exists: $MLFLOW_PATH"
        
        # Count experiments
        experiment_count=$(aws s3 ls "$MLFLOW_PATH/" --recursive | grep -c "meta.yaml" || echo "0")
        echo "📊 Found $experiment_count MLflow experiments"
    else
        echo "⚠️  MLflow artifacts path doesn't exist yet: $MLFLOW_PATH"
        echo "   This is normal for first run - will be created when pipeline runs"
    fi
else
    echo "❌ S3 bucket not found: $S3_BUCKET"
fi

# Step 4: Run a test pipeline execution
echo ""
echo "🚀 Step 4: Triggering pipeline execution..."
EXECUTION_ARN=$(aws sagemaker start-pipeline-execution \
    --pipeline-name house-price-mlops-pipeline \
    --region $AWS_REGION \
    --query 'PipelineExecutionArn' \
    --output text)

echo "✅ Pipeline execution started: $EXECUTION_ARN"
echo ""
echo "📋 Next steps:"
echo "1. Monitor pipeline execution in SageMaker console"
echo "2. Check MLflow artifacts in S3: $MLFLOW_PATH"
echo "3. Verify metrics are logged after pipeline completes"

# Step 5: Create verification script
echo ""
echo "📝 Creating verification script..."
cat > verify_mlflow_logging.py << 'EOF'
#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

def check_mlflow_s3_artifacts():
    """Check if MLflow artifacts are being created in S3"""
    s3 = boto3.client('s3')
    bucket = 'house-price-mlops-dev-itzi2hgi'
    prefix = 'mlflow-artifacts/'
    
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' not in response:
            print("❌ No MLflow artifacts found in S3")
            return False
            
        artifacts = response['Contents']
        print(f"✅ Found {len(artifacts)} MLflow artifacts in S3")
        
        # Look for recent artifacts (last 24 hours)
        recent_artifacts = []
        now = datetime.now(artifacts[0]['LastModified'].tzinfo)
        
        for artifact in artifacts:
            age_hours = (now - artifact['LastModified']).total_seconds() / 3600
            if age_hours < 24:
                recent_artifacts.append(artifact)
        
        print(f"📊 Recent artifacts (last 24h): {len(recent_artifacts)}")
        
        # Show some recent files
        if recent_artifacts:
            print("Recent MLflow files:")
            for artifact in recent_artifacts[:5]:
                print(f"  - {artifact['Key']} ({artifact['LastModified']})")
        
        return len(recent_artifacts) > 0
        
    except Exception as e:
        print(f"❌ Error checking S3: {e}")
        return False

def check_pipeline_status():
    """Check recent pipeline execution status"""
    sagemaker = boto3.client('sagemaker', region_name='us-east-1')
    
    try:
        response = sagemaker.list_pipeline_executions(
            PipelineName='house-price-mlops-pipeline',
            MaxResults=1
        )
        
        if not response['PipelineExecutionSummaries']:
            print("❌ No pipeline executions found")
            return False
            
        latest = response['PipelineExecutionSummaries'][0]
        print(f"📋 Latest pipeline: {latest['PipelineExecutionStatus']}")
        print(f"   Started: {latest['StartTime']}")
        
        return latest['PipelineExecutionStatus'] == 'Succeeded'
        
    except Exception as e:
        print(f"❌ Error checking pipeline: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying MLflow logging...")
    print("=" * 40)
    
    pipeline_ok = check_pipeline_status()
    mlflow_ok = check_mlflow_s3_artifacts()
    
    print("\n📊 SUMMARY:")
    print(f"Pipeline Status: {'✅ OK' if pipeline_ok else '❌ Issues'}")
    print(f"MLflow Logging: {'✅ Working' if mlflow_ok else '❌ Not working'}")
    
    if pipeline_ok and mlflow_ok:
        print("\n🎉 MLflow logging is working correctly!")
    else:
        print("\n⚠️  MLflow logging needs attention")
        print("Run the pipeline again and check container logs")
EOF

chmod +x verify_mlflow_logging.py

echo "✅ Created verification script: verify_mlflow_logging.py"
echo ""
echo "🎯 SUMMARY:"
echo "Your SageMaker pipeline should now log to MLflow properly."
echo "Run './verify_mlflow_logging.py' after the pipeline completes to verify."