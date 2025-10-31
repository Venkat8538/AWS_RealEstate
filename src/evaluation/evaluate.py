import os
import json
import pandas as pd
import numpy as np
import pickle
import tarfile
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def load_model():
    model_path = "/opt/ml/processing/input/model/model.tar.gz"
    with tarfile.open(model_path, "r:gz") as tar:
        tar.extractall("/tmp/model")
    
    with open("/tmp/model/xgboost-model", "rb") as f:
        model = pickle.load(f)
    return model

def load_test_data():
    test_file = "/opt/ml/processing/input/data/test.csv"
    df = pd.read_csv(test_file)
    X_test = df.drop('price', axis=1)
    y_test = df['price']
    return X_test, y_test

def evaluate_model():
    model = load_model()
    X_test, y_test = load_test_data()
    
    y_pred = model.predict(X_test)
    
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

if __name__ == "__main__":
    evaluate_model()