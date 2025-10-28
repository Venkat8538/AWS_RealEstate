# SageMaker Python SDK Pipeline

This document explains the SageMaker Python SDK pipeline implementation that replaces the Terraform-managed pipeline.

## Overview

The ML pipeline is now created and managed using the SageMaker Python SDK instead of Terraform. This approach provides:

- **Better version control**: Pipeline definitions are in code
- **Dynamic configuration**: Parameters can be set at runtime
- **Easier debugging**: Direct Python debugging capabilities
- **Flexible execution**: Can be run locally or in CI/CD

## Pipeline Architecture

The pipeline consists of two main steps:

1. **Data Processing**: Cleans and prepares the raw data
2. **Model Training**: Trains an XGBoost model on the processed data

## Files Structure

```
├── create_ml_pipeline.py          # Main pipeline creation script
├── execute_pipeline.py            # Pipeline execution script
├── pipeline_requirements.txt      # Python dependencies
├── src/
│   ├── data/
│   │   └── run_processing.py     # Data processing script
│   └── models/
│       └── train_model.py        # Model training script
└── .github/workflows/
    └── trigger-sagemaker-pipeline.yml  # Updated CI/CD workflow
```

## Usage

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r pipeline_requirements.txt
   ```

2. **Set environment variables** (optional):
   ```bash
   export SAGEMAKER_ROLE_ARN="arn:aws:iam::ACCOUNT:role/sagemaker-role"
   export S3_BUCKET="your-mlops-bucket"
   export PROJECT_NAME="house-price"
   export AWS_REGION="us-east-1"
   ```

3. **Create/Update the pipeline**:
   ```bash
   python create_ml_pipeline.py
   ```

4. **Execute the pipeline**:
   ```bash
   # Execute and return immediately
   python execute_pipeline.py
   
   # Execute and monitor progress
   python execute_pipeline.py --monitor
   ```

### CI/CD Integration

The GitHub Actions workflow automatically:

1. Installs Python dependencies
2. Uploads ML scripts to S3
3. Creates/updates the SageMaker pipeline
4. Executes the pipeline and monitors completion

### Pipeline Parameters

The pipeline supports the following parameters:

- **InputData**: S3 path to input data (default: `s3://bucket/data/raw/house_data.csv`)
- **ProcessingInstanceType**: Instance type for data processing (default: `ml.t3.medium`)
- **TrainingInstanceType**: Instance type for model training (default: `ml.m5.large`)

### Manual Pipeline Execution

You can also execute the pipeline using AWS CLI:

```bash
aws sagemaker start-pipeline-execution \
  --pipeline-name house-price-mlops-pipeline \
  --pipeline-parameters Name=InputData,Value=s3://your-bucket/data/raw/house_data.csv
```

## Monitoring

### Pipeline Status

Check pipeline execution status:

```bash
aws sagemaker list-pipeline-executions \
  --pipeline-name house-price-mlops-pipeline
```

### Logs

View logs in CloudWatch:
- Processing logs: `/aws/sagemaker/ProcessingJobs`
- Training logs: `/aws/sagemaker/TrainingJobs`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SAGEMAKER_ROLE_ARN` | SageMaker execution role | Account-specific role |
| `S3_BUCKET` | MLOps S3 bucket | `house-price-mlops-dev-*` |
| `PROJECT_NAME` | Project name prefix | `house-price` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `PIPELINE_NAME` | Pipeline name | `house-price-mlops-pipeline` |

### Pipeline Customization

To customize the pipeline:

1. **Add new steps**: Modify `create_ml_pipeline.py` to include additional processing or training steps
2. **Change instance types**: Update the parameter defaults or pass different values during execution
3. **Add parameters**: Define new `ParameterString` or `ParameterInteger` objects

## Terraform Integration

The Terraform configuration now only manages infrastructure:

- S3 buckets
- IAM roles
- SageMaker domain/user profiles

The pipeline itself is created via Python SDK, keeping infrastructure and ML logic properly separated.

## Troubleshooting

### Common Issues

1. **Permission errors**: Ensure the SageMaker role has proper S3 and SageMaker permissions
2. **Script not found**: Verify that ML scripts are uploaded to S3 before pipeline execution
3. **Instance type unavailable**: Try different instance types if the default ones are not available

### Debug Mode

For debugging, you can run the pipeline creation script with additional logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Benefits of Python SDK Approach

1. **Version Control**: Pipeline definitions are versioned with your code
2. **Flexibility**: Easy to modify and extend pipeline steps
3. **Testing**: Can unit test pipeline components
4. **Integration**: Better integration with Python ML ecosystem
5. **Debugging**: Easier to debug pipeline issues
6. **Cost Optimization**: Dynamic instance type selection based on workload