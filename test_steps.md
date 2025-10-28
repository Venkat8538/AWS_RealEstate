# Testing SageMaker Python SDK Pipeline

## Step 1: Prerequisites Check
```bash
# Install dependencies
pip install -r pipeline_requirements.txt

# Verify AWS credentials
aws sts get-caller-identity

# Check S3 bucket access
aws s3 ls s3://house-price-mlops-dev-itzi2hgi/
```

## Step 2: Local Validation
```bash
# Run test script
python test_pipeline.py
```

## Step 3: Pipeline Creation Test
```bash
# Create pipeline (dry run)
python create_ml_pipeline.py
```

## Step 4: Pipeline Execution Test
```bash
# Execute pipeline
python execute_pipeline.py --monitor
```

## Step 5: Manual AWS CLI Test
```bash
# List pipelines
aws sagemaker list-pipelines

# Describe pipeline
aws sagemaker describe-pipeline --pipeline-name house-price-mlops-pipeline

# Start execution
aws sagemaker start-pipeline-execution --pipeline-name house-price-mlops-pipeline

# Check execution status
aws sagemaker list-pipeline-executions --pipeline-name house-price-mlops-pipeline
```

## Expected Results:
- ✅ Pipeline created successfully
- ✅ 2 steps: DataProcessing, ModelTraining  
- ✅ Execution starts without errors
- ✅ Processing job completes
- ✅ Training job completes
- ✅ Model artifacts saved to S3