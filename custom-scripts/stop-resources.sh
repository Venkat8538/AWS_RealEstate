#!/bin/bash
set -e

PROJECT="house-price"
REGION="us-east-1"

echo "🛑 Stopping AWS Resources for $PROJECT..."

# Stop EC2 Instances
echo "📦 Stopping EC2 instances..."
EC2_IDS=$(aws ec2 describe-instances \
  --region $REGION \
  --filters "Name=tag:Project,Values=$PROJECT" \
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

echo "✅ All resources stopped!"
