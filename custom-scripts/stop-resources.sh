#!/bin/bash
set -e

PROJECT="house-price"
REGION="us-east-1"

echo "🛑 Stopping AWS Resources for $PROJECT..."
echo ""

# Stop EC2 Instances (Airflow & MLflow)
echo "📦 Stopping EC2 instances..."
EC2_IDS=$(aws ec2 describe-instances \
  --region $REGION \
  --filters "Name=tag:Name,Values=*$PROJECT*" \
            "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].InstanceId" \
  --output text)

if [ -n "$EC2_IDS" ]; then
  aws ec2 stop-instances --region $REGION --instance-ids $EC2_IDS
  echo "✅ Stopped EC2: $EC2_IDS"
else
  echo "ℹ️  No running EC2 instances found"
fi

# Stop RDS Instance
echo ""
echo "🗄️  Stopping RDS instance..."
RDS_ID=$(aws rds describe-db-instances \
  --region $REGION \
  --query "DBInstances[?contains(DBInstanceIdentifier, '$PROJECT')].DBInstanceIdentifier" \
  --output text)

if [ -n "$RDS_ID" ]; then
  aws rds stop-db-instance --region $REGION --db-instance-identifier $RDS_ID 2>/dev/null || echo "⚠️  RDS already stopped or cannot be stopped"
  echo "✅ Stopped RDS: $RDS_ID"
else
  echo "ℹ️  No RDS instance found"
fi

# Delete SageMaker Endpoints
echo ""
echo "🤖 Deleting SageMaker endpoints..."
ENDPOINTS=$(aws sagemaker list-endpoints --region $REGION --query 'Endpoints[*].EndpointName' --output text)

if [ -n "$ENDPOINTS" ]; then
  for ENDPOINT in $ENDPOINTS; do
    aws sagemaker delete-endpoint --endpoint-name $ENDPOINT --region $REGION
    echo "✅ Deleted endpoint: $ENDPOINT"
  done
else
  echo "ℹ️  No SageMaker endpoints found"
fi

echo ""
echo "✅ All resources stopped!"
echo "⚠️  Note: RDS will auto-restart after 7 days. Stop it again to avoid charges."
