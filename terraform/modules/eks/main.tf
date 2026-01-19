# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Use existing VPC if provided
data "aws_vpc" "existing" {
  count = var.create_vpc ? 0 : 1
  id    = var.vpc_id
}

data "aws_subnets" "existing" {
  count = var.create_vpc ? 0 : 1
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}

# VPC for EKS (only if create_vpc = true)
resource "aws_vpc" "eks_vpc" {
  count = var.create_vpc ? 1 : 0
  
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name                                        = "${var.cluster_name}-vpc"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

# Internet Gateway (only if create_vpc = true)
resource "aws_internet_gateway" "eks_igw" {
  count  = var.create_vpc ? 1 : 0
  vpc_id = aws_vpc.eks_vpc[0].id

  tags = {
    Name = "${var.cluster_name}-igw"
  }
}

# Public Subnets (only if create_vpc = true)
resource "aws_subnet" "public" {
  count = var.create_vpc ? 2 : 0

  vpc_id                  = aws_vpc.eks_vpc[0].id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                                        = "${var.cluster_name}-public-${count.index + 1}"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = "1"
  }
}

# Private Subnets (only if create_vpc = true)
resource "aws_subnet" "private" {
  count = var.create_vpc ? 2 : 0

  vpc_id            = aws_vpc.eks_vpc[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name                                        = "${var.cluster_name}-private-${count.index + 1}"
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
    "kubernetes.io/role/internal-elb"           = "1"
  }
}

# NAT Gateway (only if create_vpc = true)
resource "aws_eip" "nat" {
  count  = var.create_vpc ? 2 : 0
  domain = "vpc"

  tags = {
    Name = "${var.cluster_name}-nat-${count.index + 1}"
  }
}

resource "aws_nat_gateway" "nat" {
  count = var.create_vpc ? 2 : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${var.cluster_name}-nat-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.eks_igw]
}

# Route Tables (only if create_vpc = true)
resource "aws_route_table" "public" {
  count  = var.create_vpc ? 1 : 0
  vpc_id = aws_vpc.eks_vpc[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.eks_igw[0].id
  }

  tags = {
    Name = "${var.cluster_name}-public-rt"
  }
}

resource "aws_route_table" "private" {
  count  = var.create_vpc ? 2 : 0
  vpc_id = aws_vpc.eks_vpc[0].id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat[count.index].id
  }

  tags = {
    Name = "${var.cluster_name}-private-rt-${count.index + 1}"
  }
}

# Route Table Associations (only if create_vpc = true)
resource "aws_route_table_association" "public" {
  count = var.create_vpc ? 2 : 0

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table_association" "private" {
  count = var.create_vpc ? 2 : 0

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Local values for VPC and subnets
locals {
  vpc_id     = var.create_vpc ? aws_vpc.eks_vpc[0].id : var.vpc_id
  subnet_ids = var.create_vpc ? concat(aws_subnet.public[*].id, aws_subnet.private[*].id) : var.subnet_ids
}

# EKS Cluster IAM Role
resource "aws_iam_role" "eks_cluster_role" {
  name = "${var.cluster_name}-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

# EKS Cluster
resource "aws_eks_cluster" "cluster" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = local.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = var.public_access_cidrs
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]

  tags = var.tags
}

# Node Group IAM Role
resource "aws_iam_role" "node_group_role" {
  name = "${var.cluster_name}-node-group-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "node_group_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node_group_role.name
}

resource "aws_iam_role_policy_attachment" "node_group_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node_group_role.name
}

resource "aws_iam_role_policy_attachment" "node_group_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node_group_role.name
}

# EKS Node Group
resource "aws_eks_node_group" "node_group" {
  cluster_name    = aws_eks_cluster.cluster.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = aws_iam_role.node_group_role.arn
  subnet_ids      = var.create_vpc ? aws_subnet.private[*].id : var.subnet_ids

  capacity_type  = "ON_DEMAND"
  instance_types = ["t3.small", "t3.medium"]
  ami_type       = "AL2_x86_64"
  disk_size      = 20

  scaling_config {
    desired_size = var.node_desired_size
    max_size     = var.node_max_size
    min_size     = var.node_min_size
  }

  update_config {
    max_unavailable = 1
  }

  depends_on = [
    aws_iam_role_policy_attachment.node_group_policy,
    aws_iam_role_policy_attachment.node_group_cni_policy,
    aws_iam_role_policy_attachment.node_group_registry_policy,
  ]

  tags = var.tags
}

# OIDC Identity Provider
data "tls_certificate" "cluster" {
  url = aws_eks_cluster.cluster.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "cluster" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.cluster.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.cluster.identity[0].oidc[0].issuer

  tags = var.tags
}

# Kubernetes Namespaces
resource "kubernetes_namespace" "aap_base" {
  metadata {
    name = "aap-base"
    labels = {
      purpose = "platform-controllers"
    }
  }

  depends_on = [aws_eks_node_group.node_group]
}

resource "kubernetes_namespace" "aap_analytica" {
  metadata {
    name = "aap-analytica"
    labels = {
      purpose = "jupyterhub-runtime"
    }
  }

  depends_on = [aws_eks_node_group.node_group]
}