#!/bin/bash
set -e

echo "=== Installing Argo CD on EKS ==="

# 1. Create namespace
echo "Creating argocd namespace..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# 2. Install Argo CD
echo "Installing Argo CD..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 3. Wait for Argo CD to be ready
echo "Waiting for Argo CD pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# 4. Get initial admin password
echo ""
echo "=== Argo CD Installation Complete ==="
echo ""
echo "Admin Password:"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo ""
echo ""
echo "To access Argo CD UI, run:"
echo "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo ""
echo "Then open: https://localhost:8080"
echo "  Username: admin"
echo "  Password: (shown above)"
echo ""
echo "To deploy the application:"
echo "  kubectl apply -f apps/mlops-streamlit-ui/dev-application.yaml"
echo ""
