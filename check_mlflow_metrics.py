#!/usr/bin/env python3

import mlflow
import pandas as pd
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
try:
    from src.mlflow_config import setup_mlflow_tracking
except ImportError:
    print("MLflow config not available, using basic setup")
    def setup_mlflow_tracking(**kwargs):
        return False

def check_mlflow_connection():
    """Test MLflow connection with multiple URIs"""
    uris_to_test = [
        "http://localhost:5001",
        "http://mlflow-service:5000", 
        "http://127.0.0.1:5000",
        os.environ.get('MLFLOW_TRACKING_URI')
    ]
    
    for uri in uris_to_test:
        if uri is None:
            continue
            
        try:
            print(f"Testing connection to: {uri}")
            mlflow.set_tracking_uri(uri)
            experiments = mlflow.search_experiments()
            print(f"✅ Connected to {uri} - Found {len(experiments)} experiments")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to {uri}: {e}")
    
    return False

def check_mlflow_metrics():
    """Check what metrics are recorded in MLflow"""
    print("=== MLflow Model Tracking Diagnostics ===")
    
    # Test connection
    if not check_mlflow_connection():
        print("❌ Could not connect to any MLflow server")
        return
    
    try:
        # Try using the setup function
        if setup_mlflow_tracking():
            print("✅ MLflow setup successful")
        
        # Get experiment
        experiment = mlflow.get_experiment_by_name("house-price-prediction")
        if not experiment:
            print("❌ Experiment 'house-price-prediction' not found")
            
            # List all experiments
            all_experiments = mlflow.search_experiments()
            if all_experiments:
                print("Available experiments:")
                for exp in all_experiments:
                    print(f"  - {exp.name} (ID: {exp.experiment_id})")
            return
            
        print(f"✅ Found experiment: {experiment.name} (ID: {experiment.experiment_id})")
        
        # Get all runs
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        
        if runs.empty:
            print("❌ No runs found in experiment")
            return
            
        print(f"\n📊 Found {len(runs)} runs:")
        
        # Group runs by type
        run_types = {}
        for idx, run in runs.iterrows():
            run_name = run.get('tags.mlflow.runName', 'unnamed')
            run_type = 'unknown'
            
            if 'sagemaker' in run_name.lower():
                run_type = 'sagemaker'
            elif 'airflow' in run_name.lower():
                run_type = 'airflow'
            elif 'training' in run_name.lower():
                run_type = 'training'
            elif 'registration' in run_name.lower():
                run_type = 'registration'
            
            if run_type not in run_types:
                run_types[run_type] = []
            run_types[run_type].append(run)
        
        # Display runs by type
        for run_type, type_runs in run_types.items():
            print(f"\n📝 {run_type.upper()} RUNS ({len(type_runs)}):")
            
            for run in type_runs:
                run_name = run.get('tags.mlflow.runName', 'unnamed')
                print(f"\n  🔍 {run_name}")
                print(f"     Status: {run['status']}")
                print(f"     Start: {run['start_time']}")
                
                # Check metrics
                metrics = [col for col in run.index if col.startswith('metrics.')]
                if metrics:
                    print("     📈 Metrics:")
                    for metric in metrics[:5]:  # Show first 5 metrics
                        metric_name = metric.replace('metrics.', '')
                        value = run[metric]
                        if pd.notna(value):
                            print(f"       - {metric_name}: {value}")
                    if len(metrics) > 5:
                        print(f"       ... and {len(metrics) - 5} more")
                else:
                    print("     ❌ No metrics")
                
                # Check key parameters
                key_params = ['model_name', 'model_status', 'sagemaker_job_name', 'final_status']
                found_params = []
                for param in key_params:
                    param_col = f'params.{param}'
                    if param_col in run.index and pd.notna(run[param_col]):
                        found_params.append(f"{param}: {run[param_col]}")
                
                if found_params:
                    print("     📋 Key Parameters:")
                    for param_info in found_params:
                        print(f"       - {param_info}")
        
        # Summary
        total_metrics = sum(len([col for col in run.index if col.startswith('metrics.')]) for _, run in runs.iterrows())
        print(f"\n📊 SUMMARY:")
        print(f"  Total runs: {len(runs)}")
        print(f"  Total metrics logged: {total_metrics}")
        print(f"  Run types: {list(run_types.keys())}")
        
    except Exception as e:
        print(f"❌ Error checking MLflow: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    check_mlflow_metrics()