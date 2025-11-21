# MLflow Integration Fix for SageMaker Pipeline

## 🔥 Problem Identified

Your SageMaker pipeline stages were **NOT** logging to MLflow because:

1. **AWS default containers don't have MLflow installed**
2. **No MLflow logging code in processing scripts**  
3. **Training container showed "MLflow not available — using dummy mode"**

## ✅ Solution Implemented

### 1. Custom Docker Containers with MLflow

Created MLflow-enabled containers for each stage:

```
docker/
├── data_processing/Dockerfile     # MLflow + pandas + scikit-learn
├── feature_engineering/Dockerfile # MLflow + scikit-learn + joblib  
├── training/Dockerfile            # MLflow + XGBoost + sagemaker
├── evaluation/Dockerfile          # MLflow + scikit-learn
└── model_registration/Dockerfile  # Already had MLflow
```

### 2. Added MLflow Logging to All Scripts

**DataProcessing (`src/data/run_processing.py`)**:
```python
with mlflow.start_run(run_name="data_processing"):
    mlflow.log_param("input_shape", str(df.shape))
    mlflow.log_param("output_shape", str(df_cleaned.shape))
    mlflow.log_metric("rows_processed", len(df_cleaned))
    mlflow.log_artifact("processing_stats.json")
```

**FeatureEngineering (`src/features/engineer.py`)**:
```python
with mlflow.start_run(run_name="feature_engineering"):
    mlflow.log_param("features_created", ["house_age", "price_per_sqft", "bed_bath_ratio"])
    mlflow.log_metric("num_features", len(df_featured.columns))
    mlflow.log_artifact("feature_stats.json")
```

**ModelTraining (`src/models/train_model.py`)**:
```python
with mlflow.start_run(run_name="sagemaker_training"):
    mlflow.log_params(params)
    mlflow.log_metric("train_rmse", train_rmse)
    mlflow.log_metric("train_r2", train_r2)
    mlflow.xgboost.log_model(model, "model")
```

**ModelEvaluation (`src/evaluation/evaluate.py`)**:
```python
with mlflow.start_run(run_name="model_evaluation"):
    mlflow.log_metric("eval_rmse", metrics['rmse'])
    mlflow.log_metric("eval_mae", metrics['mae'])
    mlflow.log_metric("eval_r2", metrics['r2_score'])
    mlflow.log_artifact("evaluation_report.json")
```

### 3. Updated Terraform Pipeline

**Before** (AWS default containers):
```hcl
ImageUri = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.0-1-cpu-py3"
```

**After** (Custom MLflow containers):
```hcl
ImageUri = "${var.account_id}.dkr.ecr.us-east-1.amazonaws.com/data-processing:latest"
ImageUri = "${var.account_id}.dkr.ecr.us-east-1.amazonaws.com/feature-engineering:latest"  
ImageUri = "${var.account_id}.dkr.ecr.us-east-1.amazonaws.com/training:latest"
ImageUri = "${var.account_id}.dkr.ecr.us-east-1.amazonaws.com/evaluation:latest"
```

### 4. Added ECR Repositories

Created ECR repos for all custom containers:
- `data-processing`
- `feature-engineering` 
- `training`
- `evaluation`
- `model-registration` (existing)

## 🚀 Deployment Steps

### 1. Apply Terraform (Create ECR repos)
```bash
cd terraform/
terraform plan
terraform apply
```

### 2. Build and Push Containers
```bash
./build_mlflow_containers.sh
```

### 3. Run Pipeline
Your SageMaker pipeline will now log metrics to MLflow from **ALL stages**.

## 📊 Expected MLflow Metrics

After running the pipeline, MLflow UI will show:

### Data Processing Run
- `input_shape`: Original dataset dimensions
- `output_shape`: Cleaned dataset dimensions  
- `rows_processed`: Number of rows processed
- `processing_stats.json`: Artifact with processing details

### Feature Engineering Run  
- `features_created`: List of new features
- `num_features`: Total feature count
- `feature_stats.json`: Artifact with feature details

### Model Training Run
- `train_rmse`: Training RMSE
- `train_r2`: Training R² score
- `num_round`: XGBoost rounds
- `model`: XGBoost model artifact

### Model Evaluation Run
- `eval_rmse`: Evaluation RMSE
- `eval_mae`: Evaluation MAE  
- `eval_r2`: Evaluation R² score
- `evaluation_report.json`: Full evaluation report

### Model Registration Run (existing)
- `model_package_arn`: SageMaker model package ARN
- `model_status`: Registration status

## 🎯 Result

**Before**: Only ModelRegistration logged to MLflow
**After**: ALL 5 pipeline stages log comprehensive metrics to MLflow

Your MLflow UI will now show the complete ML pipeline execution with metrics from every stage, giving you full observability into your MLOps workflow.