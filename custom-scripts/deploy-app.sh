#!/bin/bash
set -e

echo "=== Deploying Applications to Argo CD ==="

# Deploy dev application
echo "Deploying mlops-streamlit-ui (dev)..."
kubectl apply -f apps/mlops-streamlit-ui/dev-application.yaml

echo ""
echo "Application deployed!"
echo ""
echo "Check status:"
echo "  kubectl get applications -n argocd"
echo ""
echo "View details:"
echo "  kubectl describe application mlops-streamlit-ui-dev -n argocd"
echo ""
echo "Access Argo CD UI:"
echo "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo ""
