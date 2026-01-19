variable "project_name" {
  type = string
}

variable "ami_id" {
  type        = string
  description = "Amazon Linux 2023 AMI ID"
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}

variable "key_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "allowed_cidr_blocks" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}

variable "volume_size" {
  type    = number
  default = 50
}

variable "bamboo_port" {
  type    = number
  default = 8085
}

variable "bamboo_image" {
  type    = string
  default = "atlassian/bamboo-server:latest"
}

variable "bamboo_data_dir" {
  type    = string
  default = "/var/bamboo"
}

variable "bamboo_container_name" {
  type    = string
  default = "bamboo"
}

variable "linux_host_ns" {
  type    = string
  default = "bamboo-"
}
