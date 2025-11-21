# MLflow Tracking Server on EC2
resource "aws_instance" "mlflow_server" {
  ami           = "ami-0fc5d935ebf8bc3bc" # Ubuntu 22.04 LTS
  instance_type = "t3.micro"
  
  vpc_security_group_ids = [aws_security_group.mlflow_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.mlflow_profile.name
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    s3_bucket = var.s3_bucket_name
  }))
  
  tags = {
    Name = "${var.project_name}-mlflow-server"
  }
}

# Security Group
resource "aws_security_group" "mlflow_sg" {
  name = "${var.project_name}-mlflow-sg"
  
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM Role
resource "aws_iam_role" "mlflow_role" {
  name = "${var.project_name}-mlflow-role"
  
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

resource "aws_iam_role_policy" "mlflow_s3_policy" {
  name = "${var.project_name}-mlflow-s3-policy"
  role = aws_iam_role.mlflow_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "mlflow_profile" {
  name = "${var.project_name}-mlflow-profile"
  role = aws_iam_role.mlflow_role.name
}

resource "aws_eip" "mlflow_eip" {
  instance = aws_instance.mlflow_server.id
  domain   = "vpc"
  
  tags = {
    Name = "${var.project_name}-mlflow-eip"
  }
}