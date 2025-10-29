import pandas as pd
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import os
import sys

if __name__ == "__main__":
    try:
        # SageMaker training paths
        input_path = "/opt/ml/input/data/training"
        model_path = "/opt/ml/model"
        
        # Find CSV file
        csv_files = [f for f in os.listdir(input_path) if f.endswith('.csv')]
        if not csv_files:
            print("No CSV files found")
            sys.exit(1)
        
        # Load data
        data = pd.read_csv(os.path.join(input_path, csv_files[0]))
        print(f"Data shape: {data.shape}")
        
        # Split features and target (price is last column)
        X = data.iloc[:, :-1]
        y = data.iloc[:, -1]
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        model = xgb.XGBRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"MAE: {mae:.2f}, R²: {r2:.4f}")
        
        # Save model
        joblib.dump(model, os.path.join(model_path, "model.pkl"))
        print("Model saved successfully")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)