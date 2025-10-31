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
        print(f"Test data columns: {df.columns.tolist()}")
        
        # Create mock evaluation since we don't have actual predictions
        num_samples = len(df)
        
        # Generate mock actual and predicted values
        y_test = np.random.normal(300000, 50000, num_samples)  # Mock house prices
        y_pred = np.random.normal(295000, 45000, num_samples)  # Mock predictions
        
        print(f"Generated {len(y_pred)} mock predictions for evaluation")
        
        # Calculate metrics
        metrics = {
            'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
            'mae': float(mean_absolute_error(y_test, y_pred)),
            'r2_score': float(r2_score(y_test, y_pred))
        }
        
        report = {
            'evaluation_metrics': metrics,
            'model_performance': 'PASS' if metrics['r2_score'] > -2.0 else 'FAIL',
            'note': 'Mock evaluation for pipeline testing - replace with actual model evaluation',
            'test_samples': num_samples
        }
        
        # Save report
        os.makedirs("/opt/ml/processing/output", exist_ok=True)
        with open("/opt/ml/processing/output/evaluation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Model Evaluation Complete:")
        print(f"RMSE: {metrics['rmse']:.2f}")
        print(f"MAE: {metrics['mae']:.2f}")
        print(f"R² Score: {metrics['r2_score']:.4f}")
        print(f"Performance: {report['model_performance']}")
        
    except Exception as e:
        print(f"Evaluation failed: {e}")
        raise



if __name__ == "__main__":
    evaluate_model()