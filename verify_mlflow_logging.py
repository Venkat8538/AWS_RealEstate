#!/usr/bin/env python3
import boto3
import json
from datetime import datetime, timedelta

def check_mlflow_s3_artifacts():
    """Check if MLflow artifacts are being created in S3"""
    s3 = boto3.client('s3')
    bucket = 'house-price-mlops-dev-itzi2hgi'
    prefix = 'mlflow-artifacts/'
    
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' not in response:
            print("❌ No MLflow artifacts found in S3")
            return False
            
        artifacts = response['Contents']
        print(f"✅ Found {len(artifacts)} MLflow artifacts in S3")
        
        # Look for recent artifacts (last 2 hours)
        recent_artifacts = []
        now = datetime.now(artifacts[0]['LastModified'].tzinfo)
        
        for artifact in artifacts:
            age_hours = (now - artifact['LastModified']).total_seconds() / 3600
            if age_hours < 2:
                recent_artifacts.append(artifact)
        
        print(f"📊 Recent artifacts (last 2h): {len(recent_artifacts)}")
        
        # Show some recent files
        if recent_artifacts:
            print("Recent MLflow files:")
            for artifact in recent_artifacts[:10]:
                print(f"  - {artifact['Key']} ({artifact['LastModified']})")
        
        return len(recent_artifacts) > 0
        
    except Exception as e:
        print(f"❌ Error checking S3: {e}")
        return False

def check_pipeline_status():
    """Check recent pipeline execution status"""
    sagemaker = boto3.client('sagemaker', region_name='us-east-1')
    
    try:
        response = sagemaker.list_pipeline_executions(
            PipelineName='house-price-mlops-pipeline',
            MaxResults=3
        )
        
        if not response['PipelineExecutionSummaries']:
            print("❌ No pipeline executions found")
            return False
            
        print("📋 Recent pipeline executions:")
        for i, execution in enumerate(response['PipelineExecutionSummaries']):
            status = execution['PipelineExecutionStatus']
            start_time = execution['StartTime']
            print(f"  {i+1}. {status} - Started: {start_time}")
        
        latest = response['PipelineExecutionSummaries'][0]
        return latest['PipelineExecutionStatus'] in ['Succeeded', 'Executing']
        
    except Exception as e:
        print(f"❌ Error checking pipeline: {e}")
        return False

def check_pipeline_steps():
    """Check the steps of the most recent pipeline execution"""
    sagemaker = boto3.client('sagemaker', region_name='us-east-1')
    
    try:
        # Get latest execution
        executions = sagemaker.list_pipeline_executions(
            PipelineName='house-price-mlops-pipeline',
            MaxResults=1
        )
        
        if not executions['PipelineExecutionSummaries']:
            print("❌ No pipeline executions found")
            return False
            
        execution_arn = executions['PipelineExecutionSummaries'][0]['PipelineExecutionArn']
        
        # Get steps
        steps = sagemaker.list_pipeline_execution_steps(
            PipelineExecutionArn=execution_arn
        )
        
        print(f"\n🔍 Pipeline steps for latest execution:")
        for step in steps['PipelineExecutionSteps']:
            step_name = step['StepName']
            step_status = step['StepStatus']
            
            # Check if step has started
            if 'StartTime' in step:
                start_time = step['StartTime']
                print(f"  - {step_name}: {step_status} (Started: {start_time})")
                
                # Check for training job details
                if 'Metadata' in step and 'TrainingJob' in step['Metadata']:
                    job_name = step['Metadata']['TrainingJob']['Arn'].split('/')[-1]
                    print(f"    Training Job: {job_name}")
                
                # Check for processing job details  
                elif 'Metadata' in step and 'ProcessingJob' in step['Metadata']:
                    job_name = step['Metadata']['ProcessingJob']['Arn'].split('/')[-1]
                    print(f"    Processing Job: {job_name}")
            else:
                print(f"  - {step_name}: {step_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking pipeline steps: {e}")
        return False

def main():
    print("🔍 Verifying MLflow logging in SageMaker Pipeline")
    print("=" * 50)
    
    pipeline_ok = check_pipeline_status()
    steps_ok = check_pipeline_steps()
    mlflow_ok = check_mlflow_s3_artifacts()
    
    print("\n📊 SUMMARY:")
    print(f"Pipeline Status: {'✅ OK' if pipeline_ok else '❌ Issues'}")
    print(f"Pipeline Steps: {'✅ OK' if steps_ok else '❌ Issues'}")
    print(f"MLflow Logging: {'✅ Working' if mlflow_ok else '❌ Not working yet'}")
    
    if pipeline_ok and mlflow_ok:
        print("\n🎉 MLflow logging is working correctly!")
        print("Your SageMaker pipeline is now logging metrics to S3.")
    elif pipeline_ok and not mlflow_ok:
        print("\n⏳ Pipeline is running but MLflow artifacts not found yet.")
        print("Wait for the pipeline to complete and run this script again.")
    else:
        print("\n⚠️  Issues detected. Check the pipeline execution logs.")
    
    print(f"\n💡 To monitor in real-time:")
    print(f"   - SageMaker Console: https://console.aws.amazon.com/sagemaker/home?region=us-east-1#/pipelines")
    print(f"   - S3 MLflow artifacts: s3://house-price-mlops-dev-itzi2hgi/mlflow-artifacts/")

if __name__ == "__main__":
    main()