data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64"
}

resource "aws_instance" "bamboo_server" {
  ami                       = data.aws_ssm_parameter.al2023_ami.value
  instance_type             = var.instance_type
  key_name                  = var.key_name
  vpc_security_group_ids    = [aws_security_group.bamboo_sg.id]
  subnet_id                 = var.subnet_id
  iam_instance_profile      = aws_iam_instance_profile.bamboo_profile.name
  user_data                 = file("${path.module}/linux_user_data.tpl")
  user_data_replace_on_change = true

  root_block_device {
    volume_size = var.volume_size
    volume_type = "gp3"
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-bamboo-server"
  }
}

resource "aws_security_group" "bamboo_sg" {
  name        = "${var.project_name}-bamboo-sg"
  description = "Security group for Bamboo server"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = var.bamboo_port
    to_port     = var.bamboo_port
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-bamboo-sg"
  }
}

resource "aws_iam_role" "bamboo_role" {
  name = "${var.project_name}-bamboo-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.bamboo_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "bamboo_profile" {
  name = "${var.project_name}-bamboo-profile"
  role = aws_iam_role.bamboo_role.name
}
