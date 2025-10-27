output "bucket_name" {
  description = "Name of the MLOps S3 bucket"
  value       = aws_s3_bucket.mlops_bucket.id
}

output "bucket_arn" {
  description = "ARN of the MLOps S3 bucket"
  value       = aws_s3_bucket.mlops_bucket.arn
}

output "bucket_domain_name" {
  description = "Domain name of the MLOps S3 bucket"
  value       = aws_s3_bucket.mlops_bucket.bucket_domain_name
}