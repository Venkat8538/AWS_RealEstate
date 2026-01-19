# EKS Terraform Module

This module creates a production-ready Amazon EKS cluster with:

- VPC with public and private subnets across 2 AZs
- NAT Gateways for private subnet internet access
- EKS cluster with managed node groups
- OIDC provider for IRSA (IAM Roles for Service Accounts)
- CloudWatch logging enabled

## Usage

```hcl
module "eks" {
  source = "./modules/eks"
  
  cluster_name       = "jupyterhub-cluster"
  kubernetes_version = "1.28"
  
  node_instance_types = ["t3.medium"]
  node_desired_size   = 2
  node_max_size       = 4
  node_min_size       = 1
  
  tags = {
    Environment = "production"
    Project     = "jupyterhub-platform"
  }
}
```

## Outputs

- `cluster_endpoint` - EKS cluster API endpoint
- `cluster_certificate_authority_data` - CA certificate for cluster
- `oidc_provider_arn` - OIDC provider ARN for IRSA
- `vpc_id` - VPC ID
- `private_subnets` - Private subnet IDs
- `public_subnets` - Public subnet IDs

## Post-Deployment

After cluster creation, update kubeconfig:

```bash
aws eks update-kubeconfig --name jupyterhub-cluster --region us-east-1
```