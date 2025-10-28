#!/usr/bin/env python3
"""
Execute SageMaker Pipeline
This script executes the ML pipeline and monitors its progress
"""

import boto3
import time
import sys
import os
from datetime import datetime

def get_pipeline_config():
    """Get pipeline configuration from environment or defaults"""
    return {
        'pipeline_name': os.getenv('PIPELINE_NAME', 'house-price-mlops-pipeline'),
        'region': os.getenv('AWS_REGION', 'us-east-1')
    }

def execute_pipeline():
    """Execute the SageMaker pipeline"""
    config = get_pipeline_config()
    
    # Initialize SageMaker client
    sagemaker_client = boto3.client('sagemaker', region_name=config['region'])
    
    try:
        # Start pipeline execution
        response = sagemaker_client.start_pipeline_execution(
            PipelineName=config['pipeline_name'],
            PipelineExecutionDisplayName=f"execution-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        execution_arn = response['PipelineExecutionArn']
        print(f"✅ Pipeline execution started: {execution_arn}")
        
        return execution_arn
        
    except Exception as e:
        print(f"❌ Error starting pipeline execution: {str(e)}")
        return None

def monitor_pipeline_execution(execution_arn):
    """Monitor pipeline execution progress"""
    config = get_pipeline_config()
    sagemaker_client = boto3.client('sagemaker', region_name=config['region'])
    
    print("🔄 Monitoring pipeline execution...")
    
    while True:
        try:
            response = sagemaker_client.describe_pipeline_execution(
                PipelineExecutionArn=execution_arn
            )
            
            status = response['PipelineExecutionStatus']
            print(f"Status: {status}")
            
            if status in ['Succeeded', 'Failed', 'Stopped']:
                break
                
            time.sleep(30)  # Wait 30 seconds before checking again
            
        except Exception as e:
            print(f"❌ Error monitoring pipeline: {str(e)}")
            break
    
    return status

def main():
    """Main function"""
    print("🚀 Starting SageMaker Pipeline Execution")
    
    # Execute pipeline
    execution_arn = execute_pipeline()
    if not execution_arn:
        sys.exit(1)
    
    # Monitor execution if requested
    if '--monitor' in sys.argv:
        final_status = monitor_pipeline_execution(execution_arn)
        
        if final_status == 'Succeeded':
            print("✅ Pipeline execution completed successfully!")
            sys.exit(0)
        else:
            print(f"❌ Pipeline execution failed with status: {final_status}")
            sys.exit(1)
    else:
        print("Pipeline execution started. Use --monitor flag to track progress.")

if __name__ == "__main__":
    main()