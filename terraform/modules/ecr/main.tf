# ECR Repository for Model Registration
resource "aws_ecr_repository" "model_registration" {
  name                 = "model-registration"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-model-registration"
    Environment = var.environment
    Purpose     = "MLOps-Model-Registration"
  }
}

# ECR Repository for Data Processing
resource "aws_ecr_repository" "data_processing" {
  name                 = "data-processing"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-data-processing"
    Environment = var.environment
    Purpose     = "MLOps-Data-Processing"
  }
}

# ECR Repository for Feature Engineering
resource "aws_ecr_repository" "feature_engineering" {
  name                 = "feature-engineering"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-feature-engineering"
    Environment = var.environment
    Purpose     = "MLOps-Feature-Engineering"
  }
}

# ECR Repository for Training
resource "aws_ecr_repository" "training" {
  name                 = "training"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-training"
    Environment = var.environment
    Purpose     = "MLOps-Training"
  }
}

# ECR Repository for Evaluation
resource "aws_ecr_repository" "evaluation" {
  name                 = "evaluation"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-evaluation"
    Environment = var.environment
    Purpose     = "MLOps-Evaluation"
  }
}

# ECR Lifecycle Policies
resource "aws_ecr_lifecycle_policy" "model_registration_policy" {
  repository = aws_ecr_repository.model_registration.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "data_processing_policy" {
  repository = aws_ecr_repository.data_processing.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "feature_engineering_policy" {
  repository = aws_ecr_repository.feature_engineering.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "training_policy" {
  repository = aws_ecr_repository.training.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "evaluation_policy" {
  repository = aws_ecr_repository.evaluation.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}