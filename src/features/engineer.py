# src/features/engineer.py
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import json
import os
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib

try:
    import mlflow
    from mlflow_helper import init_mlflow
except ImportError:
    mlflow = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('feature-engineering')

def create_features(df):
    """Create new features from existing data."""
    logger.info("Creating new features")
    
    # Make a copy to avoid modifying the original dataframe
    df_featured = df.copy()
    
    # Calculate house age
    current_year = datetime.now().year
    df_featured['house_age'] = current_year - df_featured['year_built']
    logger.info("Created 'house_age' feature")
    
    # Price per square foot
    df_featured['price_per_sqft'] = df_featured['price'] / df_featured['sqft']
    logger.info("Created 'price_per_sqft' feature")
    
    # Bedroom to bathroom ratio
    df_featured['bed_bath_ratio'] = df_featured['bedrooms'] / df_featured['bathrooms']
    # Handle division by zero
    df_featured['bed_bath_ratio'] = df_featured['bed_bath_ratio'].replace([np.inf, -np.inf], np.nan)
    df_featured['bed_bath_ratio'] = df_featured['bed_bath_ratio'].fillna(0)
    logger.info("Created 'bed_bath_ratio' feature")
    
    # Do NOT one-hot encode categorical variables here; let the preprocessor handle it
    return df_featured

def create_preprocessor():
    """Create a preprocessing pipeline."""
    logger.info("Creating preprocessor pipeline")
    
    # Define feature groups
    categorical_features = ['location', 'condition']
    numerical_features = ['sqft', 'bedrooms', 'bathrooms', 'house_age', 'price_per_sqft', 'bed_bath_ratio']
    
    # Preprocessing for numerical features
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean'))
    ])
    
    # Preprocessing for categorical features
    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    # Combine preprocessors in a column transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )
    
    return preprocessor

def run_feature_engineering(input_file, output_file, preprocessor_file):
    """Full feature engineering pipeline."""
    # Load cleaned data
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Create features
    df_featured = create_features(df)
    logger.info(f"Created featured dataset with shape: {df_featured.shape}")
    
    # Create and fit the preprocessor
    preprocessor = create_preprocessor()
    X = df_featured.drop(columns=['price'], errors='ignore')  # Features only
    y = df_featured['price'] if 'price' in df_featured.columns else None  # Target column (if available)
    X_transformed = preprocessor.fit_transform(X)
    logger.info("Fitted the preprocessor and transformed the features")
    
    # Save the preprocessor
    joblib.dump(preprocessor, preprocessor_file)
    logger.info(f"Saved preprocessor to {preprocessor_file}")
    
    # MLflow logging
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
                with mlflow.start_run(run_name="feature_engineering"):
                    mlflow.log_param("features_created", ["house_age", "price_per_sqft", "bed_bath_ratio"])
                    mlflow.log_metric("num_features", len(df_featured.columns))
                    mlflow.log_metric("transformed_features", X_transformed.shape[1])
                    
                    print("✅ Successfully logged feature engineering to MLflow")
            else:
                print("⚠️ MLFLOW_TRACKING_URI not set, skipping MLflow logging")
        except Exception as e:
            logger.warning(f"MLflow logging failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Save simple CSV for XGBoost
    # Just use the original featured data without complex preprocessing
    if y is not None:
        # Create simple dataframe with target first, then features
        simple_data = df_featured[['price'] + [col for col in df_featured.columns if col != 'price']]
        # Keep only numeric columns
        numeric_cols = simple_data.select_dtypes(include=[np.number]).columns
        simple_data = simple_data[numeric_cols]
        # Clean data
        simple_data = simple_data.replace([np.inf, -np.inf], 0).fillna(0)
        # Save without headers
        simple_data.to_csv(output_file, index=False, header=False)
        logger.info(f"Saved simple numeric CSV (target first) to {output_file}")
        return simple_data
    else:
        logger.error("No target variable found")
        return None


    
    return df_transformed

if __name__ == "__main__":
    import os
    import sys
    
    # SageMaker paths
    input_path = "/opt/ml/processing/input"
    output_path = "/opt/ml/processing/output"
    
    # Find CSV file in input directory
    input_files = [f for f in os.listdir(input_path) if f.endswith('.csv')]
    if not input_files:
        print("No CSV files found in input directory")
        sys.exit(1)
    
    input_file = os.path.join(input_path, input_files[0])
    output_file = os.path.join(output_path, "featured_house_data.csv")
    preprocessor_file = os.path.join(output_path, "preprocessor.pkl")
    
    run_feature_engineering(input_file, output_file, preprocessor_file)
