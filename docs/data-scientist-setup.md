# Data Scientist Setup Guide

## Development Account Infrastructure

✅ **S3 Bucket**: `house-price-mlops-dev-itzi2hgi`
✅ **SageMaker Execution Role**: `arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role`
✅ **SageMaker Domain**: `d-rr0shep9nrmf` (house-price-mlops-domain)
✅ **User Profile**: `data-scientist`
✅ **Raw Data**: Uploaded to `s3://house-price-mlops-dev-itzi2hgi/data/raw/house_data.csv`

## Getting Started with SageMaker Studio

### 1. Access SageMaker Studio
- Open AWS Console → SageMaker → Studio
- Select Domain: `house-price-mlops-domain`
- Select User Profile: `data-scientist`
- Launch Studio

### 2. Connect to GitHub Repository
```bash
git clone https://github.com/your-org/house-price-predictor.git
cd house-price-predictor
pip install -r requirements.txt
```

### 3. Available Notebooks
- `notebooks/00_data_engineering.ipynb` - Data cleaning
- `notebooks/01_exploratory_data_analysis.ipynb` - EDA
- `notebooks/02_feature_engineering.ipynb` - Feature creation
- `notebooks/03_experimentation.ipynb` - Model training

### 4. S3 Data Access
```python
import pandas as pd
s3_bucket = "house-price-mlops-dev-itzi2hgi"
df = pd.read_csv(f"s3://{s3_bucket}/data/raw/house_data.csv")
```

### 5. Model Training with SageMaker
```python
import sagemaker
role = "arn:aws:iam::482227257362:role/house-price-sagemaker-execution-role"
session = sagemaker.Session()
```

## Workflow
1. **Experimentation** - Use notebooks for exploration
2. **Model Development** - Convert to production scripts  
3. **Handoff** - Commit code and model artifacts