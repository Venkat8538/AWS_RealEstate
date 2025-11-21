import os
import mlflow

def init_mlflow(run_name: str):
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow-service:5000")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("house-price-prediction")
    return mlflow.start_run(run_name=run_name)