variable "create_vpc" {
  description = "Whether to create a new VPC or use existing one"
  type        = bool
  default     = true
}

variable "vpc_id" {
  description = "ID of existing VPC (required if create_vpc = false)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "List of existing subnet IDs (required if create_vpc = false)"
  type        = list(string)
  default     = []
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_access_cidrs" {
  description = "List of CIDR blocks that can access the EKS cluster endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "node_capacity_type" {
  description = "Type of capacity associated with the EKS Node Group. Valid values: ON_DEMAND, SPOT"
  type        = string
  default     = "ON_DEMAND"
}

variable "node_instance_types" {
  description = "List of instance types for the EKS Node Group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of nodes in the EKS Node Group"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of nodes in the EKS Node Group"
  type        = number
  default     = 4
}

variable "node_min_size" {
  description = "Minimum number of nodes in the EKS Node Group"
  type        = number
  default     = 1
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}