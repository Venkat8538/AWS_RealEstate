#!/bin/bash
set -e

PROJECT="house-price"
REGION="us-east-1"

echo "🚀 Starting AWS Resources for $PROJECT..."
echo ""

# Start EC2 Instances
echo "📦 Starting EC2 instances..."
EC2_IDS=$(aws ec2 describe-instances \
  --region $REGION \
  --filters "Name=tag:Name,Values=*$PROJECT*" \
            "Name=instance-state-name,Values=stopped" \
  --query "Reservations[].Instances[].InstanceId" \
  --output text)

if [ -n "$EC2_IDS" ]; then
  aws ec2 start-instances --region $REGION --instance-ids $EC2_IDS
  echo "✅ Started EC2: $EC2_IDS"
  echo "⏳ Waiting for instances to start..."
  sleep 10
else
  echo "ℹ️  No stopped EC2 instances found"
fi

# Start RDS Instance
echo ""
echo "🗄️  Starting RDS instance..."
RDS_ID=$(aws rds describe-db-instances \
  --region $REGION \
  --query "DBInstances[?contains(DBInstanceIdentifier, '$PROJECT')].DBInstanceIdentifier" \
  --output text)

if [ -n "$RDS_ID" ]; then
  aws rds start-db-instance --region $REGION --db-instance-identifier $RDS_ID 2>/dev/null || echo "⚠️  RDS already running or cannot be started"
  echo "✅ Started RDS: $RDS_ID"
else
  echo "ℹ️  No RDS instance found"
fi

echo ""
echo "✅ All resources started!"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📋 Resource Information"
echo "═══════════════════════════════════════════════════════════"

# Get Airflow Server Info
AIRFLOW_IP=$(aws ec2 describe-instances \
  --region $REGION \
  --filters "Name=tag:Name,Values=*airflow*" \
            "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text 2>/dev/null)

if [ "$AIRFLOW_IP" != "None" ] && [ -n "$AIRFLOW_IP" ]; then
  echo "🌊 Airflow Server:"
  echo "   URL: http://$AIRFLOW_IP:8080"
  echo "   IP:  $AIRFLOW_IP"
else
  echo "ℹ️  Airflow server not found or not running"
fi

# Get MLflow Server Info
MLFLOW_IP=$(aws ec2 describe-instances \
  --region $REGION \
  --filters "Name=tag:Name,Values=*mlflow*" \
            "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text 2>/dev/null)

if [ "$MLFLOW_IP" != "None" ] && [ -n "$MLFLOW_IP" ]; then
  echo ""
  echo "📊 MLflow Server:"
  echo "   URL: http://$MLFLOW_IP:5000"
  echo "   IP:  $MLFLOW_IP"
else
  echo "ℹ️  MLflow server not found or not running"
fi

# Get RDS Info
if [ -n "$RDS_ID" ]; then
  RDS_ENDPOINT=$(aws rds describe-db-instances \
    --region $REGION \
    --db-instance-identifier $RDS_ID \
    --query "DBInstances[0].Endpoint.Address" \
    --output text 2>/dev/null)
  
  RDS_PORT=$(aws rds describe-db-instances \
    --region $REGION \
    --db-instance-identifier $RDS_ID \
    --query "DBInstances[0].Endpoint.Port" \
    --output text 2>/dev/null)
  
  if [ "$RDS_ENDPOINT" != "None" ] && [ -n "$RDS_ENDPOINT" ]; then
    echo ""
    echo "🗄️  RDS Database:"
    echo "   Endpoint: $RDS_ENDPOINT:$RDS_PORT"
    echo "   Instance: $RDS_ID"
  fi
fi

echo "═══════════════════════════════════════════════════════════"
