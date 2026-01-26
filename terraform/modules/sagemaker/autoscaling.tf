# Auto Scaling for SageMaker Endpoint - Disabled until endpoint is created
# Uncomment after first successful model deployment

# resource "aws_appautoscaling_target" "sagemaker_target" {
#   max_capacity       = 3
#   min_capacity       = 0
#   resource_id        = "endpoint/${aws_sagemaker_endpoint.house_price_endpoint.name}/variant/AllTraffic"
#   scalable_dimension = "sagemaker:variant:DesiredInstanceCount"
#   service_namespace  = "sagemaker"
# }

# resource "aws_appautoscaling_policy" "sagemaker_policy" {
#   name               = "sagemaker-scaling-policy"
#   policy_type        = "TargetTrackingScaling"
#   resource_id        = aws_appautoscaling_target.sagemaker_target.resource_id
#   scalable_dimension = aws_appautoscaling_target.sagemaker_target.scalable_dimension
#   service_namespace  = aws_appautoscaling_target.sagemaker_target.service_namespace

#   target_tracking_scaling_policy_configuration {
#     target_value = 70.0
#     predefined_metric_specification {
#       predefined_metric_type = "SageMakerVariantInvocationsPerInstance"
#     }
#   }
# }