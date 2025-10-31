import os
import json
import pandas as pd
import numpy as np
import pickle
import tarfile
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb

def load_model():
    try:
        print("Loading model...")
        model_path = "/opt/ml/processing/input/model"
        print(f"Model directory contents: {os.listdir(model_path)}")
        
        # Find and extract tar.gz file
        for file in os.listdir(model_path):
            if file.endswith('.tar.gz'):
                tar_path = os.path.join(model_path, file)
                print(f"Extracting {tar_path}")
                with tarfile.open(tar_path, "r:gz") as tar:
                    tar.extractall("/tmp/model")
                break
        
        print(f"Extracted model contents: {os.listdir('/tmp/model')}")
        
        # Load XGBoost model
        model_file = "/tmp/model/xgboost-model"
        if os.path.exists(model_file):
            print(f"Loading XGBoost model from {model_file}")
            model = xgb.Booster()
            model.load_model(model_file)
            return model
        
        print("XGBoost model file not found")
        return None
            
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def load_test_data():
    try:
        print("Loading test data...")
        data_path = "/opt/ml/processing/input/data"
        print(f"Data directory contents: {os.listdir(data_path)}")
        
        test_file = "/opt/ml/processing/input/data/test.csv"
        df = pd.read_csv(test_file)
        print(f"Test data shape: {df.shape}")
        print(f"Test data columns: {df.columns.tolist()}")
        
        X_test = df.drop('price', axis=1)
        y_test = df['price']
        return X_test, y_test
        
    except Exception as e:
        print(f"Error loading test data: {e}")
        return None, None

def evaluate_model():
    try:
        model = load_model()
        if model is None:
            raise Exception("Failed to load model")
            
        X_test, y_test = load_test_data()
        if X_test is None:
            raise Exception("Failed to load test data")
        
        # Convert to DMatrix for XGBoost
        dtest = xgb.DMatrix(X_test)
        y_pred = model.predict(dtest)
        
        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mae': mean_absolute_error(y_test, y_pred),
            'r2_score': r2_score(y_test, y_pred)
        }
        
        report = {
            'evaluation_metrics': metrics,
            'model_performance': 'PASS' if metrics['r2_score'] > 0.7 else 'FAIL'
        }
        
        os.makedirs("/opt/ml/processing/output", exist_ok=True)
        with open("/opt/ml/processing/output/evaluation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Model Evaluation Complete:")
        print(f"RMSE: {metrics['rmse']:.2f}")
        print(f"MAE: {metrics['mae']:.2f}")
        print(f"R² Score: {metrics['r2_score']:.4f}")
        
    except Exception as e:
        print(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    evaluate_model()