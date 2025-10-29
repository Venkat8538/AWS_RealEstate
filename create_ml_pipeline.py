#!/usr/bin/env python3
"""
SageMaker Pipeline for House Price Prediction
This script creates a complete ML pipeline with data processing, training, and model registration
Updated: Testing workflow trigger with fixed permissions
"""

import boto3
import sagemaker
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.xgboost.estimator import XGBoost
from sagemaker.inputs import TrainingInput
from sagemaker.workflow.parameters import ParameterString, ParameterInteger
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.processing import ProcessingInput, ProcessingOutput
import os

def get_pipeline_config():
    """Get pipeline configuration from environment or defaults"""
    bucket_name = os.getenv('S3_BUCKET', 'house-price-mlops-dev-itzi2hgi')
    # Remove s3:// prefix if present
    if bucket_name.startswith('s3://'):
        bucket_name = bucket_name.replace('s3://', '').split('/')[0]
    
    return {
        'role': os.getenv('SAGEMAKER_ROLE_ARN', 'arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role'),
        'bucket': bucket_name,
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
    data_processor = SKLearnProcessor(
        framework_version="1.0-1",
        instance_type=processing_instance_type,
        instance_count=1,
        base_job_name=f"{config['project_name']}-processing",
        role=config['role'],
        sagemaker_session=pipeline_session
    )
    
    processing_step = ProcessingStep(
        name="DataProcessing",
        processor=data_processor,
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
    
    # Step 2: Feature Engineering
    feature_processor = SKLearnProcessor(
        framework_version="1.0-1",
        instance_type=processing_instance_type,
        instance_count=1,
        base_job_name=f"{config['project_name']}-feature-engineering",
        role=config['role'],
        sagemaker_session=pipeline_session
    )
    
    feature_engineering_step = ProcessingStep(
        name="FeatureEngineering",
        processor=feature_processor,
        inputs=[
            ProcessingInput(
                source=processing_step.properties.ProcessingOutputConfig.Outputs[
                    "processed-data"
                ].S3Output.S3Uri,
                destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="featured-data",
                source="/opt/ml/processing/output",
                destination=f"s3://{config['bucket']}/data/featured"
            )
        ],
        code="src/features/engineer.py"
    )
    
    # Step 3: Model Training
    from sagemaker.xgboost.estimator import XGBoost
    
    xgb_estimator = XGBoost(
        entry_point="train_model.py",
        source_dir="src/models",
        framework_version="1.5-1",
        py_version="py3",
        instance_type=training_instance_type,
        instance_count=1,
        role=config['role'],
        base_job_name=f"{config['project_name']}-training",
        sagemaker_session=pipeline_session,
        environment={'S3_BUCKET': config['bucket']}
    )
    
    training_step = TrainingStep(
        name="ModelTraining",
        estimator=xgb_estimator,
        inputs={
            "training": TrainingInput(
                s3_data=feature_engineering_step.properties.ProcessingOutputConfig.Outputs[
                    "featured-data"
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
            feature_engineering_step,
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
        print("  2. Feature Engineering - Creates and transforms features")
        print("  3. Model Training - Trains XGBoost model")
        print("\nTo execute the pipeline, run:")
        print(f"  aws sagemaker start-pipeline-execution --pipeline-name {pipeline.name}")
        
        return pipeline
        
    except Exception as e:
        print(f"❌ Error creating pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main()