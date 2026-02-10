#!/usr/bin/env python3
"""
Diagnostic script to check SageMaker permissions and configuration
"""
import boto3
import json
from botocore.exceptions import ClientError

REGION = "us-east-1"
PROJECT_NAME = "house-price"

def check_current_identity():
    """Check current AWS identity"""
    print("=" * 60)
    print("1. Current AWS Identity")
    print("=" * 60)
    try:
        sts = boto3.client('sts', region_name=REGION)
        identity = sts.get_caller_identity()
        print(f"✅ Account: {identity['Account']}")
        print(f"✅ User ARN: {identity['Arn']}")
        print(f"✅ User ID: {identity['UserId']}")
        return identity['Account']
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def check_sagemaker_permissions(account_id):
    """Check SageMaker permissions"""
    print("\n" + "=" * 60)
    print("2. SageMaker Permissions")
    print("=" * 60)
    
    sm = boto3.client('sagemaker', region_name=REGION)
    
    tests = [
        ("List Domains", lambda: sm.list_domains()),
        ("List Notebook Instances", lambda: sm.list_notebook_instances()),
        ("List Models", lambda: sm.list_models()),
        ("List Endpoints", lambda: sm.list_endpoints()),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}: PASS")
        except ClientError as e:
            print(f"❌ {test_name}: FAIL - {e.response['Error']['Code']}")

def check_execution_role(account_id):
    """Check SageMaker execution role"""
    print("\n" + "=" * 60)
    print("3. SageMaker Execution Role")
    print("=" * 60)
    
    role_name = f"{PROJECT_NAME}-sagemaker-execution-role"
    iam = boto3.client('iam')
    
    try:
        role = iam.get_role(RoleName=role_name)
        print(f"✅ Role exists: {role_name}")
        print(f"   ARN: {role['Role']['Arn']}")
        
        # Check trust policy
        trust_policy = role['Role']['AssumeRolePolicyDocument']
        print(f"\n   Trust Policy:")
        print(f"   {json.dumps(trust_policy, indent=2)}")
        
        # Check attached policies
        policies = iam.list_attached_role_policies(RoleName=role_name)
        print(f"\n   Attached Policies:")
        for policy in policies['AttachedPolicies']:
            print(f"   - {policy['PolicyName']}")
            
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"❌ Role does not exist: {role_name}")
            print(f"   Expected ARN: arn:aws:iam::{account_id}:role/{role_name}")
        else:
            print(f"❌ Error checking role: {e.response['Error']['Code']}")

def check_sagemaker_domains():
    """Check SageMaker domains"""
    print("\n" + "=" * 60)
    print("4. SageMaker Domains")
    print("=" * 60)
    
    sm = boto3.client('sagemaker', region_name=REGION)
    
    try:
        domains = sm.list_domains()
        if domains['Domains']:
            for domain in domains['Domains']:
                print(f"✅ Domain ID: {domain['DomainId']}")
                print(f"   Name: {domain['DomainName']}")
                print(f"   Status: {domain['Status']}")
                
                # Get detailed info
                try:
                    detail = sm.describe_domain(DomainId=domain['DomainId'])
                    print(f"   Auth Mode: {detail.get('AuthMode', 'N/A')}")
                    print(f"   Execution Role: {detail.get('DefaultUserSettings', {}).get('ExecutionRole', 'N/A')}")
                except Exception as e:
                    print(f"   ⚠️  Cannot describe domain: {e}")
        else:
            print("ℹ️  No SageMaker domains found")
    except ClientError as e:
        print(f"❌ Error listing domains: {e.response['Error']['Code']}")

def check_s3_access():
    """Check S3 bucket access"""
    print("\n" + "=" * 60)
    print("5. S3 Model Bucket Access")
    print("=" * 60)
    
    bucket_name = f"{PROJECT_NAME}-mlops-dev-itzi2hgi"
    s3 = boto3.client('s3', region_name=REGION)
    
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket exists: {bucket_name}")
        
        # Check if model file exists
        try:
            s3.head_object(Bucket=bucket_name, Key="models/trained/model.tar.gz")
            print(f"✅ Model file exists: models/trained/model.tar.gz")
        except ClientError:
            print(f"⚠️  Model file not found: models/trained/model.tar.gz")
            
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"❌ Bucket does not exist: {bucket_name}")
        else:
            print(f"❌ Error accessing bucket: {e.response['Error']['Code']}")

def check_ecr_access(account_id):
    """Check ECR repository access"""
    print("\n" + "=" * 60)
    print("6. ECR Repository Access")
    print("=" * 60)
    
    repo_name = f"{PROJECT_NAME}-fastapi"
    ecr = boto3.client('ecr', region_name=REGION)
    
    try:
        repos = ecr.describe_repositories(repositoryNames=[repo_name])
        print(f"✅ Repository exists: {repo_name}")
        print(f"   URI: {repos['repositories'][0]['repositoryUri']}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'RepositoryNotFoundException':
            print(f"ℹ️  Repository does not exist yet: {repo_name}")
        else:
            print(f"❌ Error: {e.response['Error']['Code']}")

if __name__ == "__main__":
    print("\n🔍 SageMaker Configuration Diagnostic Tool\n")
    
    account_id = check_current_identity()
    
    if account_id:
        check_sagemaker_permissions(account_id)
        check_execution_role(account_id)
        check_sagemaker_domains()
        check_s3_access()
        check_ecr_access(account_id)
    
    print("\n" + "=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)
