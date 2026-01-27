# XGBoost model training script for SageMaker MLOps pipeline
import argparse
import os
import glob
import json
import pandas as pd
import pickle
import shutil
import numpy as np
import sys
from sklearn.metrics import mean_squared_error, r2_score

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
    print("⚠️ MLflow not available in local environment — using dummy mode.")
    mlflow = None

# SageMaker standard paths
TRAIN_CHANNEL = "/opt/ml/input/data/train"
MODEL_DIR = "/opt/ml/model"

def parse_args():
    p = argparse.ArgumentParser()

    # XGBoost hyperparameters
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

    dfs = []
    for path in csvs:
        df = pd.read_csv(path)
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in {path}")
        dfs.append(df)
    
    data = pd.concat(dfs, ignore_index=True)
    y = data[target_col]
    X = data.drop(columns=[target_col])

    # Convert objects to category codes (XGBoost dtrain requires numeric)
    for col in X.select_dtypes(include=["object"]).columns:
        X[col] = X[col].astype("category").cat.codes
    
    print(f"Training data shape: {X.shape}")
    
    if not XGBOOST_AVAILABLE:
        return None
        
    return xgb.DMatrix(X, label=y)

def main():
    args = parse_args()
    print(">>> Training starting...")
    
    if not XGBOOST_AVAILABLE:
        print("⚠ Skipping training: XGBoost missing.")
        return

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

    # Train model
    model = xgb.train(params, dtrain, num_boost_round=args.num_round)
    
    # Calculate metrics
    train_pred = model.predict(dtrain)
    train_labels = dtrain.get_label()
    rmse = np.sqrt(mean_squared_error(train_labels, train_pred))
    r2 = r2_score(train_labels, train_pred)
    
    print(f"Training RMSE: {rmse:.2f}")
    print(f"Training R²: {r2:.4f}")
    
    # MLflow Tracking
    if mlflow:
        try:
            tracking_uri = os.environ.get('MLFLOW_TRACKING_URI')
            if tracking_uri:
                mlflow.set_tracking_uri(tracking_uri)
                mlflow.set_experiment("house-price-prediction")
                
                with mlflow.start_run(run_name="sagemaker_training"):
                    mlflow.log_params(params)
                    mlflow.log_metric("train_rmse", rmse)
                    mlflow.log_metric("train_r2", r2)
                    mlflow.xgboost.log_model(model, "model")
                    print("✅ Logged to MLflow")
        except Exception as e:
            print(f"MLflow logging failed: {e}")

    # --- CRITICAL FIX FOR SAGEMAKER INFERENCE ---
    print(">>> Preparing MODEL_DIR for export...")
    
    # 1. Purge the directory to remove feature_names.json or other metadata
    if os.path.exists(MODEL_DIR):
        for filename in os.listdir(MODEL_DIR):
            file_path = os.path.join(MODEL_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"⚠️ Could not delete {file_path}: {e}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # 2. Save using Pickle with the exact name 'xgboost-model'
    # This prevents the 'invalid load key' error by ensuring a valid pickle file is found first
    model_path = os.path.join(MODEL_DIR, "xgboost-model")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    
    # 3. Final Verification
    final_files = os.listdir(MODEL_DIR)
    print(f"✅ Final contents of MODEL_DIR: {final_files}")
    if len(final_files) != 1:
        print(f"⚠️ WARNING: MODEL_DIR contains multiple files. This may cause 502 errors.")

if __name__ == "__main__":
    main()