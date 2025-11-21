# src/data/processor.py
# Updated to trigger pipeline execution
# Sample echo for workflow trigger
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json
import os

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
logger = logging.getLogger('data-processor')

def load_data(file_path):
    """Load data from a CSV file."""
    logger.info(f"Loading data from {file_path}")
    return pd.read_csv(file_path)

def clean_data(df):
    """Clean the dataset by handling missing values and outliers."""
    logger.info("Cleaning dataset")
    
    # Make a copy to avoid modifying the original dataframe
    df_cleaned = df.copy()
    
    # Handle missing values
    for column in df_cleaned.columns:
        missing_count = df_cleaned[column].isnull().sum()
        if missing_count > 0:
            logger.info(f"Found {missing_count} missing values in {column}")
            
            # For numeric columns, fill with median
            if pd.api.types.is_numeric_dtype(df_cleaned[column]):
                median_value = df_cleaned[column].median()
                df_cleaned[column] = df_cleaned[column].fillna(median_value)
                logger.info(f"Filled missing values in {column} with median: {median_value}")
            # For categorical columns, fill with mode
            else:
                mode_value = df_cleaned[column].mode()[0]
                df_cleaned[column] = df_cleaned[column].fillna(mode_value)
                logger.info(f"Filled missing values in {column} with mode: {mode_value}")
    
    # Handle outliers in price (target variable)
    # Using IQR method to identify outliers
    Q1 = df_cleaned['price'].quantile(0.25)
    Q3 = df_cleaned['price'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    # Filter out extreme outliers
    outliers = df_cleaned[(df_cleaned['price'] < lower_bound) | 
                          (df_cleaned['price'] > upper_bound)]
    
    if not outliers.empty:
        logger.info(f"Found {len(outliers)} outliers in price column")
        df_cleaned = df_cleaned[(df_cleaned['price'] >= lower_bound) & 
                                (df_cleaned['price'] <= upper_bound)]
        logger.info(f"Removed outliers. New dataset shape: {df_cleaned.shape}")
    
    return df_cleaned

def process_data(input_file, output_file):
    """Full data processing pipeline."""
    # Create output directory if it doesn't exist
    output_path = Path(output_file).parent
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_data(input_file)
    logger.info(f"Loaded data with shape: {df.shape}")
    
    # Clean data
    df_cleaned = clean_data(df)
    
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
                with mlflow.start_run(run_name="data_processing"):
                    mlflow.log_param("input_shape", str(df.shape))
                    mlflow.log_param("output_shape", str(df_cleaned.shape))
                    mlflow.log_metric("rows_processed", len(df_cleaned))
                    mlflow.log_metric("missing_values_handled", df.isnull().sum().sum())
                    
                    print("✅ Successfully logged data processing to MLflow")
            else:
                print("⚠️ MLFLOW_TRACKING_URI not set, skipping MLflow logging")
        except Exception as e:
            logger.warning(f"MLflow logging failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Save processed data
    df_cleaned.to_csv(output_file, index=False)
    logger.info(f"Saved processed data to {output_file}")
    
    return df_cleaned

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
    output_file = os.path.join(output_path, "processed_house_data.csv")
    
    process_data(input_file, output_file)
# Updated Thu Oct 30 16:55:09 CDT 2025
