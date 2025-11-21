resource "aws_instance" "airflow_server" {
  ami                    = "ami-0fc5d935ebf8bc3bc"
  instance_type          = "t3.small"
  iam_instance_profile   = aws_iam_instance_profile.airflow_profile.name
  vpc_security_group_ids = [aws_security_group.airflow_sg.id]

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    db_endpoint      = var.db_endpoint
    db_name          = var.db_name
    db_username      = var.db_username
    db_password      = var.db_password
    AIRFLOW_VERSION  = "2.7.3"
    CONSTRAINT_URL   = "https://raw.githubusercontent.com/apache/airflow/constraints-2.7.3/constraints-3.10.txt"
  }))
  # Optional, if your provider supports it:
  # user_data_replace_on_change = true

  tags = {
    Name = "house-price-airflow-server"
  }
}

resource "aws_security_group" "airflow_sg" {
  name_prefix = "${var.project_name}-airflow-sg"
  
  ingress {
    from_port   = 8080
    to_port     = 8080
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

resource "aws_iam_role" "airflow_role" {
  name = "${var.project_name}-airflow-role"
  
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

resource "aws_iam_role_policy" "airflow_policy" {
  name = "${var.project_name}-airflow-policy"
  role = aws_iam_role.airflow_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:*",
          "s3:*",
          "ssm:*",
          "ssmmessages:*",
          "ec2messages:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "airflow_profile" {
  name = "${var.project_name}-airflow-profile"
  role = aws_iam_role.airflow_role.name
}

resource "aws_eip" "airflow_eip" {
  domain = "vpc"
  
  tags = {
    Name = "${var.project_name}-airflow-eip"
  }
}

resource "aws_eip_association" "airflow_eip_assoc" {
  instance_id   = aws_instance.airflow_server.id
  allocation_id = aws_eip.airflow_eip.id
  
  depends_on = [aws_instance.airflow_server]
}