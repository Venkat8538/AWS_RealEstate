#!/usr/bin/env python3
"""
SageMaker Pipeline for House Price Prediction
This script creates a complete ML pipeline with data processing, training, and model registration
"""

import boto3
import sagemaker
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.inputs import TrainingInput
from sagemaker.workflow.parameters import ParameterString, ParameterInteger
from sagemaker.workflow.pipeline_context import PipelineSession
import os

def get_pipeline_config():
    """Get pipeline configuration from environment or defaults"""
    return {
        'role': os.getenv('SAGEMAKER_ROLE_ARN', 'arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role'),
        'bucket': os.getenv('S3_BUCKET', 'house-price-mlops-dev-itzi2hgi'),
        'project_name': os.getenv('PROJECT_NAME', 'house-price'),
        'region': os.getenv('AWS_REGION', 'us-east-1')
    }

def create_ml_pipeline():
    """Create comprehensive SageMaker ML Pipeline"""
    config = get_pipeline_config()
    
    # Initialize SageMaker session
    pipeline_session = PipelineSession()
    
    # Pipeline parameters
    input_data = ParameterString(
        name="InputData",
        default_value=f"s3://{config['bucket']}/data/raw/house_data.csv"
    )
    
    processing_instance_type = ParameterString(
        name="ProcessingInstanceType",
        default_value="ml.t3.medium"
    )
    
    training_instance_type = ParameterString(
        name="TrainingInstanceType",
        default_value="ml.m5.large"
    )
    
    # Step 1: Data Processing
    processor = SKLearnProcessor(
        framework_version="1.0-1",
        instance_type=processing_instance_type,
        instance_count=1,
        base_job_name=f"{config['project_name']}-processing",
        role=config['role'],
        sagemaker_session=pipeline_session
    )
    
    processing_step = ProcessingStep(
        name="DataProcessing",
        processor=processor,
        inputs=[
            ProcessingInput(
                source=input_data,
                destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="processed-data",
                source="/opt/ml/processing/output",
                destination=f"s3://{config['bucket']}/data/processed"
            )
        ],
        code="src/data/run_processing.py"
    )
    
    # Step 2: Model Training
    sklearn_estimator = SKLearn(
        entry_point="train_model.py",
        source_dir="src/models",
        framework_version="1.0-1",
        py_version="py3",
        instance_type=training_instance_type,
        instance_count=1,
        role=config['role'],
        base_job_name=f"{config['project_name']}-training",
        sagemaker_session=pipeline_session
    )
    
    training_step = TrainingStep(
        name="ModelTraining",
        estimator=sklearn_estimator,
        inputs={
            "training": TrainingInput(
                s3_data=processing_step.properties.ProcessingOutputConfig.Outputs[
                    "processed-data"
                ].S3Output.S3Uri,
                content_type="text/csv"
            )
        }
    )
    
    # Create pipeline
    pipeline = Pipeline(
        name=f"{config['project_name']}-mlops-pipeline",
        parameters=[
            input_data,
            processing_instance_type,
            training_instance_type
        ],
        steps=[
            processing_step,
            training_step
        ],
        sagemaker_session=pipeline_session
    )
    
    return pipeline, config

def main():
    """Main function to create and upsert the pipeline"""
    try:
        pipeline, config = create_ml_pipeline()
        
        print(f"Creating pipeline: {pipeline.name}")
        print(f"Using role: {config['role']}")
        print(f"Using bucket: {config['bucket']}")
        
        # Create/update the pipeline
        pipeline.upsert(role_arn=config['role'])
        
        print("✅ ML Pipeline created successfully!")
        print(f"Pipeline ARN: {pipeline.describe()['PipelineArn']}")
        print("\nPipeline includes:")
        print("  1. Data Processing - Cleans and prepares data")
        print("  2. Model Training - Trains XGBoost model")
        print("\nTo execute the pipeline, run:")
        print(f"  aws sagemaker start-pipeline-execution --pipeline-name {pipeline.name}")
        
        return pipeline
        
    except Exception as e:
        print(f"❌ Error creating pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main()