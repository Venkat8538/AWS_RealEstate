import pandas as pd
import pickle
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import os
import sys
import tarfile
from datetime import datetime

# Import boto3 with fallback
try:
    import boto3
except ImportError:
    print("Warning: boto3 not available, S3 upload will be skipped")
    boto3 = None

if __name__ == "__main__":
    try:
        # SageMaker training paths
        input_path = "/opt/ml/input/data/training"
        model_path = "/opt/ml/model"
        
        print(f"Input path contents: {os.listdir(input_path)}")
        
        # Find CSV file
        csv_files = [f for f in os.listdir(input_path) if f.endswith('.csv')]
        if not csv_files:
            print("No CSV files found")
            sys.exit(1)
        
        # Load data
        data = pd.read_csv(os.path.join(input_path, csv_files[0]))
        print(f"Data shape: {data.shape}")
        print(f"Columns: {list(data.columns)}")
        
        # Split features and target (price is last column)
        X = data.iloc[:, :-1]
        y = data.iloc[:, -1]
        
        print(f"Features shape: {X.shape}, Target shape: {y.shape}")
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model with basic parameters
        model = xgb.XGBRegressor(
            n_estimators=100, 
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"MAE: {mae:.2f}, R²: {r2:.4f}")
        
        # Save model using pickle
        model_file = os.path.join(model_path, "model.pkl")
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        print("Model saved successfully")
        
        # Save preprocessor
        preprocessor_file = os.path.join(model_path, "preprocessor.pkl")
        dummy_preprocessor = {"feature_names": list(X.columns), "trained": True}
        with open(preprocessor_file, 'wb') as f:
            pickle.dump(dummy_preprocessor, f)
        
        # Create model.tar.gz for SageMaker deployment
        tar_file = os.path.join(model_path, "model.tar.gz")
        with tarfile.open(tar_file, 'w:gz') as tar:
            tar.add(model_file, arcname="model.pkl")
            tar.add(preprocessor_file, arcname="preprocessor.pkl")
        
        # Upload to S3 if boto3 is available
        if boto3:
            print("Starting S3 upload...")
            s3_client = boto3.client('s3')
            bucket_name = os.environ.get('S3_BUCKET', 'house-price-mlops-dev-itzi2hgi')
            
            # Upload preprocessor to artifacts
            print(f"Uploading preprocessor to s3://{bucket_name}/models/artifacts/preprocessor.pkl")
            s3_client.upload_file(preprocessor_file, bucket_name, "models/artifacts/preprocessor.pkl")
            print("✅ Preprocessor uploaded successfully")
            
            # Upload model.tar.gz to trained
            print(f"Uploading model package to s3://{bucket_name}/models/trained/model.tar.gz")
            s3_client.upload_file(tar_file, bucket_name, "models/trained/model.tar.gz")
            print("✅ Model package uploaded successfully")
            
            print("🎉 All artifacts uploaded to S3 successfully!")
        else:
            print("⚠️ boto3 not available, skipping S3 upload")
            print("Files saved locally in /opt/ml/model/")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)