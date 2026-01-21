# XGBoost model training script for SageMaker MLOps pipeline
import argparse
import os
import glob
import json
import pandas as pd

# Try importing XGBoost normally (SageMaker will have it)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    print("⚠ XGBoost is not available in this environment. Training will be skipped.")
    XGBOOST_AVAILABLE = False

# Try importing MLflow (SageMaker Studio will have it)
try:
    import mlflow
    import mlflow.xgboost
except ImportError:
    print("⚠️ MLflow not available in local Docker — using dummy mode.")
    mlflow = None

from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import sys

print("MLflow training script loaded - clean build without requirements.txt")

try:
    from mlflow_helper import init_mlflow
except ImportError:
    init_mlflow = None

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
    p.add_argument("--target", type=str, default="price",
                   help="Name of the target column in the CSVs")
    return p.parse_args()

def load_train_dataframe(train_dir: str, target_col: str):
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

    # 🔥 Fix for XGBoost: convert object columns to categorical
    for col in X.select_dtypes(include=["object"]).columns:
        X[col] = X[col].astype("category")

    # Save feature names for later use
    feature_names_list = list(X.columns)
    
    print(f"Training data shape: {X.shape}")
    print(f"Target column: {target_col}")
    print(f"Number of features: {len(X.columns)}")
    print(f"Sample features: {list(X.columns)[:5]}{'...' if len(X.columns) > 5 else ''}")

    if not XGBOOST_AVAILABLE:
        return None
        
    dtrain = xgb.DMatrix(
        X,
        label=y,
        feature_names=feature_names_list,
        enable_categorical=True,
    )
    return dtrain

def main():
    args = parse_args()
    print(">>> MLflow-enabled training starting...")
    print(">>> Received hyperparameters:", vars(args))
    
    if not XGBOOST_AVAILABLE:
        print("⚠ Skipping training because XGBoost is not available (local Docker test mode).")
        return

    if mlflow is None:
        print("MLflow tracking disabled - continuing without tracking")

    dtrain = load_train_dataframe(TRAIN_CHANNEL, args.target)

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

    if not XGBOOST_AVAILABLE:
        print("⚠ Skipped model training because XGBoost is not available.")
        return

    model = xgb.train(params, dtrain, num_boost_round=args.num_round)
    
    train_pred = model.predict(dtrain)
    train_labels = dtrain.get_label()
    train_rmse = np.sqrt(mean_squared_error(train_labels, train_pred))
    train_r2 = r2_score(train_labels, train_pred)
    
    print(f"Training RMSE: {train_rmse:.2f}")
    print(f"Training R²: {train_r2:.4f}")
    
    # Log to MLflow
    if mlflow:
        try:
            # Use S3 tracking URI from environment
            tracking_uri = os.environ.get('MLFLOW_TRACKING_URI')
            if tracking_uri:
                print(f"Setting MLflow tracking URI to: {tracking_uri}")
                mlflow.set_tracking_uri(tracking_uri)
                
                # Set experiment
                experiment_name = "house-price-prediction"
                try:
                    mlflow.set_experiment(experiment_name)
                except Exception:
                    # Create experiment if it doesn't exist
                    mlflow.create_experiment(experiment_name)
                    mlflow.set_experiment(experiment_name)
                
                # Start run and log metrics
                with mlflow.start_run(run_name="sagemaker_training"):
                    mlflow.log_params(params)
                    mlflow.log_param("num_round", args.num_round)
                    mlflow.log_metric("train_rmse", train_rmse)
                    mlflow.log_metric("train_r2", train_r2)
                    
                    # Log model
                    mlflow.xgboost.log_model(model, "model")
                    
                    print("✅ Successfully logged to MLflow")
            else:
                print("⚠️ MLFLOW_TRACKING_URI not set, skipping MLflow logging")
        except Exception as e:
            print(f"MLflow logging failed: {e}")
            import traceback
            traceback.print_exc()

    os.makedirs(MODEL_DIR, exist_ok=True)
    # Save using save_raw() to get legacy binary format (not UBJSON)
    raw_bytes = model.save_raw("deprecated")
    with open(os.path.join(MODEL_DIR, "xgboost-model"), "wb") as f:
        f.write(raw_bytes)
    print("✅ Saved model in legacy binary format using save_raw()")
    
    # Verify first byte is not '{' (0x7b)
    with open(os.path.join(MODEL_DIR, "xgboost-model"), "rb") as f:
        first_byte = f.read(1)
        if first_byte == b'{':
            print("⚠️ WARNING: Model still starts with '{' - may be UBJSON")
        else:
            print(f"✅ Model first byte: {first_byte.hex()} (not UBJSON)")
    
    # Save feature names after model (for tar.gz ordering)
    with open(os.path.join(MODEL_DIR, "feature_names.json"), "w") as f:
        json.dump(list(dtrain.feature_names), f)

if __name__ == "__main__":
    main()
