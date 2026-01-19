output "cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.cluster.id
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.cluster.arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.cluster.endpoint
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane"
  value       = aws_eks_cluster.cluster.vpc_config[0].cluster_security_group_id
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = aws_iam_role.eks_cluster_role.name
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN associated with EKS cluster"
  value       = aws_iam_role.eks_cluster_role.arn
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.cluster.certificate_authority[0].data
}

output "cluster_primary_security_group_id" {
  description = "Cluster security group that was created by Amazon EKS for the cluster"
  value       = aws_eks_cluster.cluster.vpc_config[0].cluster_security_group_id
}

output "node_groups" {
  description = "EKS node groups"
  value       = aws_eks_node_group.node_group
}

output "node_group_arn" {
  description = "Amazon Resource Name (ARN) of the EKS Node Group"
  value       = aws_eks_node_group.node_group.arn
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider if enabled"
  value       = aws_iam_openid_connect_provider.cluster.arn
}

output "vpc_id" {
  description = "ID of the VPC where the cluster is deployed"
  value       = local.vpc_id
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = var.create_vpc ? aws_subnet.private[*].id : var.subnet_ids
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = var.create_vpc ? aws_subnet.public[*].id : []
}

output "namespaces" {
  description = "Created Kubernetes namespaces"
  value = {
    aap_base      = kubernetes_namespace.aap_base.metadata[0].name
    aap_analytica = kubernetes_namespace.aap_analytica.metadata[0].name
  }
}