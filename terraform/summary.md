# Terraform Plan Summary

**Terraform Version:** 1.11.3
**Format Version:** 1.2

## Resource Changes Overview
- **Create:** 14 resources
- **Update:** 1 resources
- **Delete:** 4 resources
- **Replace:** 14 resources

## Changes by Module

### module

**➕ Create:**
- aws_appautoscaling_policy.sagemaker_policy
- aws_appautoscaling_target.sagemaker_target
- aws_eip_association.airflow_eip_assoc
- aws_eks_cluster.cluster
- aws_eks_node_group.node_group
- aws_iam_openid_connect_provider.cluster
- aws_iam_role.eks_cluster_role
- aws_iam_role.node_group_role
- aws_iam_role_policy_attachment.eks_cluster_policy
- aws_iam_role_policy_attachment.node_group_cni_policy
- aws_iam_role_policy_attachment.node_group_policy
- aws_iam_role_policy_attachment.node_group_registry_policy
- aws_instance.airflow_server
- aws_instance.mlflow_server

**❌ Delete:**
- aws_iam_instance_profile.bamboo_profile
- aws_iam_role.bamboo_role
- aws_iam_role_policy_attachment.ssm_policy
- aws_security_group.bamboo_sg

**🔧 No-Op:**
- aws_cloudwatch_event_rule.model_approval
- aws_cloudwatch_event_target.codepipeline_target
- aws_codebuild_project.deploy_model
- aws_codepipeline.deployment_pipeline
- aws_db_instance.airflow_db
- aws_db_subnet_group.airflow_db_subnet_group
- aws_ecr_lifecycle_policy.data_processing_policy
- aws_ecr_lifecycle_policy.evaluation_policy
- aws_ecr_lifecycle_policy.feature_engineering_policy
- aws_ecr_lifecycle_policy.model_registration_policy
- aws_ecr_lifecycle_policy.training_policy
- aws_ecr_repository.data_processing
- aws_ecr_repository.evaluation
- aws_ecr_repository.feature_engineering
- aws_ecr_repository.model_registration
- aws_ecr_repository.training
- aws_eip.airflow_eip
- aws_iam_instance_profile.airflow_profile
- aws_iam_instance_profile.mlflow_profile
- aws_iam_openid_connect_provider.github
- aws_iam_role.airflow_role
- aws_iam_role.codebuild_role
- aws_iam_role.codepipeline_role
- aws_iam_role.eventbridge_role
- aws_iam_role.github_actions
- aws_iam_role.mlflow_role
- aws_iam_role.sagemaker_execution_role
- aws_iam_role_policy.airflow_policy
- aws_iam_role_policy.codebuild_policy
- aws_iam_role_policy.codepipeline_policy
- aws_iam_role_policy.eventbridge_policy
- aws_iam_role_policy.github_sagemaker_policy
- aws_iam_role_policy.mlflow_s3_policy
- aws_iam_role_policy.s3_mlops_access
- aws_iam_role_policy.sagemaker_studio_permissions
- aws_iam_role_policy_attachment.ecr_policy
- aws_iam_role_policy_attachment.sagemaker_execution_policy
- aws_iam_role_policy_attachment.sagemaker_studio_policy
- aws_s3_bucket.codepipeline_artifacts
- aws_s3_bucket.mlops_bucket
- aws_s3_bucket_lifecycle_configuration.mlops_lifecycle
- aws_s3_bucket_public_access_block.mlops_pab
- aws_s3_bucket_server_side_encryption_configuration.codepipeline_encryption
- aws_s3_bucket_server_side_encryption_configuration.mlops_encryption
- aws_s3_bucket_versioning.mlops_versioning
- aws_s3_object.folders
- aws_s3_object.folders
- aws_s3_object.folders
- aws_s3_object.folders
- aws_s3_object.folders
- aws_s3_object.folders
- aws_s3_object.folders
- aws_s3_object.folders
- aws_s3_object.folders
- aws_s3_object.folders
- aws_sagemaker_domain.mlops_domain
- aws_sagemaker_endpoint.house_price_endpoint
- aws_sagemaker_endpoint_configuration.house_price_config
- aws_sagemaker_endpoint_configuration.house_price_serverless_config
- aws_sagemaker_model.house_price_model
- aws_sagemaker_pipeline.mlops_pipeline
- aws_sagemaker_user_profile.data_scientist
- aws_security_group.airflow_db_sg
- aws_security_group.airflow_sg
- aws_security_group.mlflow_sg
- random_string.bucket_suffix
- random_string.suffix

**📖 Read:**
- tls_certificate.cluster

**🔄 Update:**
- aws_eip.mlflow_eip

## Variables
- **airflow_db_password:** [SENSITIVE]
- **aws_region:** us-east-1
- **bamboo_ami_id:** ami-066279af4a501d501
- **bamboo_key_name:** 
- **bamboo_subnet_id:** subnet-0c092dfafe0a2b4b2
- **bamboo_vpc_id:** vpc-0ec06d2e45d4c6de8
- **environment:** dev
- **github_repository:** Venkat8538/AWS_RealEstate
- **github_token:** [SENSITIVE]
- **project_name:** house-price

## Key Outputs
- **airflow_server_ip:** 44.195.50.213
- **airflow_server_url:** http://44.195.50.213:8080
- **deployment_codebuild_arn:** arn:aws:codebuild:us-east-1:482227257362:project/house-price-deploy-model
- **deployment_pipeline_arn:** arn:aws:codepipeline:us-east-1:482227257362:house-price-deployment-pipeline
- **eks_cluster_endpoint:** Unknown
- **eks_cluster_name:** Unknown
- **eks_oidc_provider_arn:** Unknown
- **github_actions_role_arn:** arn:aws:iam::482227257362:role/house-price-github-actions-role
- **mlflow_server_ip:** 23.21.206.232
- **mlflow_server_url:** http://23.21.206.232:5000
- **s3_bucket_arn:** arn:aws:s3:::house-price-mlops-dev-itzi2hgi
- **s3_bucket_name:** house-price-mlops-dev-itzi2hgi
- **sagemaker_domain_id:** d-rr0shep9nrmf
- **sagemaker_execution_role_arn:** arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role
- **sagemaker_pipeline_arn:** arn:aws:sagemaker:us-east-1:482227257362:pipeline/house-price-mlops-pipeline
- **sagemaker_pipeline_name:** house-price-mlops-pipeline
- **sagemaker_user_profile_arn:** arn:aws:sagemaker:us-east-1:482227257362:user-profile/d-rr0shep9nrmf/data-scientist

