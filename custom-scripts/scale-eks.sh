#!/bin/bash
set -e

CLUSTER_NAME="house-price-jupyterhub-cluster"
REGION="us-east-1"
DESIRED_SIZE=${1:-0}

if [ "$DESIRED_SIZE" != "0" ] && [ "$DESIRED_SIZE" != "1" ]; then
  echo "Usage: $0 [0|1]"
  echo "  0 = Scale down to 0 nodes (default)"
  echo "  1 = Scale up to 1 node"
  exit 1
fi

echo "⚙️  Scaling EKS node groups to $DESIRED_SIZE for $CLUSTER_NAME..."

NODE_GROUPS=$(aws eks list-nodegroups \
  --cluster-name $CLUSTER_NAME \
  --region $REGION \
  --query 'nodegroups[]' \
  --output text)

if [ -z "$NODE_GROUPS" ]; then
  echo "ℹ️  No node groups found"
  exit 0
fi

for NG in $NODE_GROUPS; do
  echo "📊 Scaling node group: $NG to $DESIRED_SIZE"
  aws eks update-nodegroup-config \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NG \
    --scaling-config minSize=0,maxSize=2,desiredSize=$DESIRED_SIZE \
    --region $REGION
  echo "✅ Scaled: $NG"
done

echo "✅ All node groups scaled to $DESIRED_SIZE!"
