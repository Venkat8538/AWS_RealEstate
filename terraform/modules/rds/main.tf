resource "aws_db_subnet_group" "airflow_db_subnet_group" {
  name       = "${lower(var.project_name)}-airflow-db-subnet-group"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name = "${var.project_name}-airflow-db-subnet-group"
  }
}

resource "aws_security_group" "airflow_db_sg" {
  name_prefix = "${lower(var.project_name)}-airflow-db-"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-airflow-db-sg"
  }
}

resource "aws_db_instance" "airflow_db" {
  identifier = "${lower(var.project_name)}-airflow-db"
  
  engine         = "postgres"
  engine_version = "15.7"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type         = "gp2"
  storage_encrypted    = true
  
  db_name  = "airflow"
  username = "airflow"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.airflow_db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.airflow_db_subnet_group.name
  
  backup_retention_period = 0
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = true
  deletion_protection = false
  
  tags = {
    Name = "${var.project_name}-airflow-db"
  }
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}