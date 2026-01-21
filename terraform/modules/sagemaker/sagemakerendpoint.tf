resource "aws_sagemaker_model" "house_price_model" {
  name               = "house-price-model-v2"
  execution_role_arn = aws_iam_role.sagemaker_execution_role.arn

  primary_container {
    image          = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:3.0-5-cpu-py3"
    model_data_url = "s3://${var.s3_bucket}/models/trained/model.tar.gz"
  }

  tags = var.tags
}

resource "aws_sagemaker_endpoint_configuration" "house_price_config" {
  name = "house-price-config"

  production_variants {
    variant_name            = "AllTraffic"
    model_name              = aws_sagemaker_model.house_price_model.name
    initial_instance_count  = 1
    instance_type           = "ml.t2.medium"  # Smallest: $0.0464/hr vs ml.m5.large $0.115/hr
    initial_variant_weight  = 1
  }

  tags = var.tags
}

resource "aws_sagemaker_endpoint_configuration" "house_price_serverless_config" {
  name = "house-price-serverless-config-v2"

  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.house_price_model.name
    initial_variant_weight = 1

    serverless_config {
      memory_size_in_mb = 2048
      max_concurrency   = 5
    }
  }

  tags = var.tags
}

resource "aws_sagemaker_endpoint" "house_price_endpoint" {
  name                 = "house-price-prod"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.house_price_serverless_config.name

  tags = var.tags
}