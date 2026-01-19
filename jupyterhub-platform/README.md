# JupyterHub Platform

Enterprise-grade JupyterHub platform for AWS EKS with IRSA and External Secrets Operator.

## Architecture

- **production-lab-parent**: Orchestration chart that wires together ESO, ingress, and application charts
- **charts/vendor/**: Upstream Helm charts (JupyterHub, MLflow, MinIO) - DO NOT EDIT
- **deployments/**: Environment-specific configurations and customer tenants

## Environment Selection

- **EKS Production**: Uses `deployments/environments/prod.yaml` with IRSA enabled
- **Staging**: Uses `deployments/environments/test.yaml`

## Infrastructure Components

| Component | Implementation |
|-----------|----------------|
| Secrets Backend | AWS Secrets Manager |
| Ingress | ALB Controller |
| Authentication | IRSA + IAM |
| Storage | EBS/EFS |

## Safe to Edit

✅ `deployments/environments/` - Environment configs
✅ `deployments/customers/` - Customer-specific configs  
✅ `charts/production-lab-parent/` - Platform orchestration logic

❌ `charts/vendor/` - Upstream charts (use Helm dependencies instead)

## Quick Start

1. Deploy EKS: `cd terraform && terraform apply`
2. Configure kubectl: `aws eks update-kubeconfig --name house-price-jupyterhub-cluster`
3. Deploy platform: `helm install platform charts/production-lab-parent/ -f deployments/environments/prod.yaml`