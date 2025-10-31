import os
import json
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def evaluate_model():
    try:
        print("Model Evaluation Started")
        
        # Load test data
        print("Loading test data...")
        test_file = "/opt/ml/processing/input/data/test.csv"
        df = pd.read_csv(test_file)
        print(f"Test data shape: {df.shape}")
        
        # For demonstration, create mock predictions
        # In a real scenario, you'd load and use the actual model
        y_test = df['price']
        
        # Generate mock predictions (mean + some noise)
        # This is just for pipeline testing - replace with actual model predictions
        mean_price = y_test.mean()
        y_pred = np.random.normal(mean_price, mean_price * 0.1, len(y_test))
        
        print(f"Generated {len(y_pred)} predictions")
        
        # Calculate metrics
        metrics = {
            'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
            'mae': float(mean_absolute_error(y_test, y_pred)),
            'r2_score': float(r2_score(y_test, y_pred))
        }
        
        report = {
            'evaluation_metrics': metrics,
            'model_performance': 'PASS' if metrics['r2_score'] > 0.0 else 'FAIL',
            'note': 'Mock evaluation for pipeline testing'
        }
        
        # Save report
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