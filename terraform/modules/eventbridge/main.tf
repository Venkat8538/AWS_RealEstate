# EventBridge Rule to trigger SageMaker Pipeline
resource "aws_cloudwatch_event_rule" "sagemaker_pipeline_trigger" {
  name        = "${var.project_name}-pipeline-trigger"
  description = "Trigger SageMaker Pipeline from GitHub events"

  event_pattern = jsonencode({
    source      = ["github.mlops"]
    detail-type = ["ML Pipeline Trigger"]
  })
}

# EventBridge Target - SageMaker Pipeline
resource "aws_cloudwatch_event_target" "sagemaker_pipeline_target" {
  rule      = aws_cloudwatch_event_rule.sagemaker_pipeline_trigger.name
  target_id = "SageMakerPipelineTarget"
  arn       = var.sagemaker_pipeline_arn
  role_arn  = aws_iam_role.eventbridge_sagemaker_role.arn

  input_transformer {
    input_paths = {
      commit = "$.detail.commit"
      branch = "$.detail.branch"
    }
    input_template = "{\"GitCommit\": \"<commit>\", \"GitBranch\": \"<branch>\"}"
  }
}

# IAM Role for EventBridge to invoke SageMaker Pipeline
resource "aws_iam_role" "eventbridge_sagemaker_role" {
  name = "${var.project_name}-eventbridge-sagemaker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for EventBridge to start SageMaker Pipeline
resource "aws_iam_role_policy" "eventbridge_sagemaker_policy" {
  name = "${var.project_name}-eventbridge-sagemaker-policy"
  role = aws_iam_role.eventbridge_sagemaker_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:StartPipelineExecution"
        ]
        Resource = var.sagemaker_pipeline_arn
      }
    ]
  })
}