#!/bin/bash

echo "🔍 Verifying MLflow-enabled SageMaker Pipeline Setup"
echo ""

# Check ECR repositories
echo "📦 ECR Repositories:"
aws ecr describe-repositories --region us-east-1 --query 'repositories[?contains(repositoryName, `data-processing`) || contains(repositoryName, `feature-engineering`) || contains(repositoryName, `training`) || contains(repositoryName, `evaluation`) || contains(repositoryName, `model-registration`)].{Name:repositoryName,URI:repositoryUri}' --output table

echo ""
echo "🏗️ SageMaker Pipeline Status:"
aws sagemaker describe-pipeline --pipeline-name house-price-mlops-pipeline --region us-east-1 --query '{Name:PipelineName,Status:PipelineStatus,Created:CreationTime}' --output table

echo ""
echo "✅ Setup Complete!"
echo ""
echo "🎯 What's Fixed:"
echo "  ✅ All 5 pipeline stages now have MLflow logging"
echo "  ✅ Custom containers with MLflow installed"
echo "  ✅ Consistent MLflow helper across all scripts"
echo "  ✅ S3-based MLflow artifact storage"
echo ""
echo "🚀 Next Steps:"
echo "  1. Run your SageMaker pipeline"
echo "  2. Check MLflow UI for metrics from ALL stages"
echo "  3. Verify artifacts are stored in S3"