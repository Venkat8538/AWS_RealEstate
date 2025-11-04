import argparse
import os
import glob
import json
import pandas as pd
import xgboost as xgb
import mlflow
import mlflow.xgboost
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import sys

print("MLflow training script loaded - testing workflow with setup.py")

# Simple MLflow setup without external dependencies
def setup_mlflow_tracking(tracking_uri=None, experiment_name="house-price-prediction"):
    try:
        uri = tracking_uri or os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow-service:5000')
        mlflow.set_tracking_uri(uri)
        mlflow.set_experiment(experiment_name)
        return True
    except:
        return False

def log_sagemaker_job_info(job_name, job_type):
    pass  # Simplified for SageMaker

TRAIN_CHANNEL = "/opt/ml/input/data/train"
MODEL_DIR = "/opt/ml/model"

def parse_args():
    p = argparse.ArgumentParser()

    # XGBoost hyperparameters (must match what you pass from SageMaker)
    p.add_argument("--objective", type=str, default="reg:squarederror")
    p.add_argument("--num_round", type=int, default=100)
    p.add_argument("--max_depth", type=int, default=5)
    p.add_argument("--eta", type=float, default=0.2)
    p.add_argument("--gamma", type=float, default=4.0)
    p.add_argument("--min_child_weight", type=float, default=6.0)
    p.add_argument("--subsample", type=float, default=0.8)
    p.add_argument("--verbosity", type=int, default=1)

    # Data options
    p.add_argument("--target", type=str, default="Price",
                   help="Name of the target column in the CSVs")
    p.add_argument("--mlflow_tracking_uri", type=str, 
                   default=os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow-service:5000'),
                   help="MLflow tracking server URI")
    return p.parse_args()

def load_train_dataframe(train_dir: str, target_col: str) -> xgb.DMatrix:
    csvs = sorted(glob.glob(os.path.join(train_dir, "*.csv")))
    if not csvs:
        raise FileNotFoundError(f"No CSV files found under {train_dir}")

    # Concatenate all CSVs; header is OK in script mode
    dfs = []
    for path in csvs:
        df = pd.read_csv(path)
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in {path}. "
                             f"Columns present: {list(df.columns)}")
        dfs.append(df)
    data = pd.concat(dfs, ignore_index=True)

    y = data[target_col]
    X = data.drop(columns=[target_col])

    # Save feature names for later use
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(os.path.join(MODEL_DIR, "feature_names.json"), "w") as f:
        json.dump(list(X.columns), f)
    
    print(f"Training data shape: {X.shape}")
    print(f"Target column: {target_col}")
    print(f"Number of features: {len(X.columns)}")
    print(f"Sample features: {list(X.columns)[:5]}{'...' if len(X.columns) > 5 else ''}")

    dtrain = xgb.DMatrix(X, label=y, feature_names=list(X.columns))
    return dtrain

def main():
    args = parse_args()
    print(">>> MLflow-enabled training starting...")
    print(">>> Received hyperparameters:", vars(args))

    # Setup MLflow tracking
    mlflow_enabled = setup_mlflow_tracking(
        tracking_uri=args.mlflow_tracking_uri,
        experiment_name="house-price-prediction"
    )
    
    if mlflow_enabled:
        print("MLflow tracking enabled")
        # Log SageMaker job info
        job_name = os.environ.get('TRAINING_JOB_NAME', 'unknown-training-job')
        log_sagemaker_job_info(job_name, 'training')
    else:
        print("MLflow tracking disabled - continuing without tracking")

    dtrain = load_train_dataframe(TRAIN_CHANNEL, args.target)

    # Train with MLflow tracking
    params = {
        "objective": args.objective,
        "max_depth": args.max_depth,
        "eta": args.eta,
        "gamma": args.gamma,
        "min_child_weight": args.min_child_weight,
        "subsample": args.subsample,
        "verbosity": args.verbosity,
    }
    print(">>> XGBoost params:", params)
    
    # Train model
    model = xgb.train(params, dtrain, num_boost_round=args.num_round)
    
    # Calculate training metrics
    train_pred = model.predict(dtrain)
    train_labels = dtrain.get_label()
    train_rmse = np.sqrt(mean_squared_error(train_labels, train_pred))
    train_r2 = r2_score(train_labels, train_pred)
    
    print(f"Training RMSE: {train_rmse:.2f}")
    print(f"Training R²: {train_r2:.4f}")
    
    # Log to MLflow if enabled
    if mlflow_enabled:
        try:
            with mlflow.start_run(run_name="sagemaker_training"):
                # Log hyperparameters
                mlflow.log_params(params)
                mlflow.log_param("num_round", args.num_round)
                mlflow.log_param("target_column", args.target)
                mlflow.log_param("training_data_shape", str(dtrain.num_row()))
                
                # Log metrics
                mlflow.log_metric("train_rmse", train_rmse)
                mlflow.log_metric("train_r2", train_r2)
                mlflow.log_metric("num_features", dtrain.num_col())
                
                # Log model
                mlflow.xgboost.log_model(model, "model")
                
                print("Model and metrics logged to MLflow")
                
        except Exception as e:
            print(f"MLflow logging failed: {e}")
    else:
        print("MLflow not available - metrics not logged")

    # Save model — SageMaker will package everything in /opt/ml/model into model.tar.gz
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_model(os.path.join(MODEL_DIR, "xgboost-model"))
    print("✅ Saved model to /opt/ml/model/xgboost-model")

if __name__ == "__main__":
    main()
