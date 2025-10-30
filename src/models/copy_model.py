#!/usr/bin/env python3
"""
Copy trained model to custom S3 location
"""
import os
import shutil
import tarfile
from datetime import datetime

def extract_and_copy_model():
    """Extract model from tar.gz and copy to output location"""
    input_path = "/opt/ml/processing/input/model"
    output_path = "/opt/ml/processing/output"
    
    print(f"Input path contents: {os.listdir(input_path)}")
    
    # Find model.tar.gz file
    model_files = [f for f in os.listdir(input_path) if f.endswith('.tar.gz')]
    if not model_files:
        print("No model.tar.gz files found")
        return
    
    model_file = os.path.join(input_path, model_files[0])
    print(f"Found model file: {model_file}")
    
    # Extract the model
    with tarfile.open(model_file, 'r:gz') as tar:
        tar.extractall(path=input_path)
    
    # Copy model files to output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for file in os.listdir(input_path):
        if file.endswith('.pkl') or file.endswith('.joblib'):
            src = os.path.join(input_path, file)
            dst = os.path.join(output_path, f"model_{timestamp}.pkl")
            shutil.copy2(src, dst)
            print(f"Copied {file} to {dst}")
    
    print("Model copy completed successfully")

if __name__ == "__main__":
    extract_and_copy_model()