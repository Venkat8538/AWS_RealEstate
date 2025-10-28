#!/usr/bin/env python3
"""
SageMaker Pipeline for House Price Prediction
This script creates the actual ML pipeline with proper data processing
"""

import boto3
import sagemaker
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.workflow.steps import ProcessingStep
from sagemaker.workflow.pipeline import Pipeline

def create_ml_pipeline():
    # Initialize SageMaker session
    sagemaker_session = sagemaker.Session()
    region = sagemaker_session.boto_region_name
    role = "arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role"
    bucket = "house-price-mlops-dev-itzi2hgi"
    
    # Create processor
    processor = SKLearnProcessor(
        framework_version="0.23-1",
        instance_type="ml.t3.medium",
        instance_count=1,
        base_job_name="house-price-processing",
        role=role,
    )
    
    # Step 1: Data Processing
    processing_step = ProcessingStep(
        name="DataProcessing",
        processor=processor,
        inputs=[
            ProcessingInput(
                source=f"s3://{bucket}/data/raw/house_data.csv",
                destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="processed-data",
                source="/opt/ml/processing/output",
                destination=f"s3://{bucket}/data/processed"
            )
        ],
        code="src/data/run_processing.py"
    )
    
    # Create pipeline
    pipeline = Pipeline(
        name="house-price-mlops-pipeline",
        steps=[processing_step],
        sagemaker_session=sagemaker_session,
    )
    
    return pipeline

if __name__ == "__main__":
    pipeline = create_ml_pipeline()
    pipeline.upsert(role_arn="arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role")
    print("✅ ML Pipeline created successfully!")
    print("Now your pipeline will actually process data and save to S3")