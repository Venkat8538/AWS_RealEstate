# S3 Bucket for Single-Account MLOps
resource "aws_s3_bucket" "mlops_bucket" {
  bucket = "${var.project_name}-mlops-${var.environment}-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-mlops-bucket"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "MLOps-SingleAccount"
  }
}

# Random suffix for unique bucket name
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Bucket versioning - Required for CodePipeline
resource "aws_s3_bucket_versioning" "mlops_versioning" {
  bucket = aws_s3_bucket.mlops_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Bucket encryption - Use SSE-S3 (free) instead of KMS
resource "aws_s3_bucket_server_side_encryption_configuration" "mlops_encryption" {
  bucket = aws_s3_bucket.mlops_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"  # Free SSE-S3 encryption
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "mlops_pab" {
  bucket = aws_s3_bucket.mlops_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Create MLOps folder structure
resource "aws_s3_object" "folders" {
  for_each = toset([
    "data/raw/",
    "data/test/",
    "data/processed/",
    "data/featured/",
    "models/trained/",
    "models/registry/",
    "pipelines/",
    "logs/",
    "configs/"
  ])

  bucket = aws_s3_bucket.mlops_bucket.id
  key    = each.value
  content_type = "application/x-directory"
}

# Lifecycle policy for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "mlops_lifecycle" {
  bucket = aws_s3_bucket.mlops_bucket.id

  rule {
    id     = "cost_optimization"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Move to cheaper storage after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Move to even cheaper storage after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Delete old objects after 365 days (optional)
    expiration {
      days = 365
    }
  }
}

# Create folder structure - minimal approach
# Folders will be created automatically when files are uploaded
# This saves on unnecessary S3 object costs