output "codepipeline_arn" {
  description = "ARN of the deployment CodePipeline"
  value       = aws_codepipeline.deployment_pipeline.arn
}

output "codebuild_project_arn" {
  description = "ARN of the CodeBuild project"
  value       = aws_codebuild_project.deploy_model.arn
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.model_approval.arn
}