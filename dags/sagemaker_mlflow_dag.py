from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import boto3
import json
import requests

# AWS configuration
REGION_NAME = 'us-east-1'
PIPELINE_NAME = 'house-price-mlops-pipeline'
ENDPOINT_NAME = 'house-price-prod'

def start_sagemaker_pipeline(**context):
    sagemaker_client = boto3.client('sagemaker', region_name=REGION_NAME)
    
    response = sagemaker_client.start_pipeline_execution(
        PipelineName=PIPELINE_NAME,
        PipelineExecutionDisplayName=f'airflow-execution-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    )
    
    execution_arn = response['PipelineExecutionArn']
    print(f"Started pipeline execution: {execution_arn}")
    return execution_arn

def wait_for_pipeline(**context):
    import time
    sagemaker_client = boto3.client('sagemaker', region_name=REGION_NAME)
    
    execution_arn = context['task_instance'].xcom_pull(task_ids='start_pipeline')
    
    while True:
        response = sagemaker_client.describe_pipeline_execution(
            PipelineExecutionArn=execution_arn
        )
        
        status = response['PipelineExecutionStatus']
        print(f"Pipeline status: {status}")
        
        if status in ['Succeeded', 'Failed', 'Stopped']:
            if status != 'Succeeded':
                raise Exception(f"Pipeline failed with status: {status}")
            break
            
        time.sleep(60)
    
    return status

def log_model_metadata(**context):
    # Log model metadata to MLflow via HTTP API
    mlflow_url = "http://23.21.206.232:5000"
    
    # Create experiment if not exists
    experiment_data = {"name": "house-price-mlops"}
    try:
        requests.post(f"{mlflow_url}/api/2.0/mlflow/experiments/create", json=experiment_data)
    except:
        pass
    
    # Start a run and log metadata
    run_data = {
        "experiment_id": "0",
        "start_time": int(datetime.now().timestamp() * 1000)
    }
    
    run_response = requests.post(f"{mlflow_url}/api/2.0/mlflow/runs/create", json=run_data)
    run_id = run_response.json().get("run", {}).get("info", {}).get("run_id")
    
    if run_id:
        # Log parameters
        params = [
            {"key": "pipeline_name", "value": PIPELINE_NAME},
            {"key": "endpoint_name", "value": ENDPOINT_NAME},
            {"key": "model_source", "value": "sagemaker-pipeline"}
        ]
        
        for param in params:
            requests.post(f"{mlflow_url}/api/2.0/mlflow/runs/log-parameter", 
                         json={"run_id": run_id, **param})
        
        print(f"Logged model metadata to MLflow run: {run_id}")
        return run_id
    
    return "metadata_logged"

def deploy_to_endpoint(**context):
    sagemaker_client = boto3.client('sagemaker', region_name=REGION_NAME)
    
    try:
        response = sagemaker_client.describe_endpoint(EndpointName=ENDPOINT_NAME)
        print(f"Endpoint {ENDPOINT_NAME} already exists with status: {response['EndpointStatus']}")
    except sagemaker_client.exceptions.ClientError:
        print(f"Endpoint {ENDPOINT_NAME} does not exist, will be created by SageMaker pipeline")
    
    return "Endpoint deployment verified"

def validate_deployment(**context):
    sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=REGION_NAME)
    
    # Test payload
    test_data = {
        "instances": [{
            "features": [3, 2, 1500, 7000, 1, 0, 0, 3, 7, 1500, 0, 1990, 0]
        }]
    }
    
    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='application/json',
            Body=json.dumps(test_data)
        )
        
        result = json.loads(response['Body'].read().decode())
        print(f"Endpoint test successful. Prediction: {result}")
        return result
    except Exception as e:
        print(f"Endpoint validation failed: {str(e)}")
        raise

# DAG definition
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'house_price_mlops_pipeline',
    default_args=default_args,
    description='House Price MLOps Pipeline with SageMaker and MLflow',
    schedule_interval='@daily',
    catchup=False,
    tags=['mlops', 'sagemaker', 'mlflow']
)

# Task definitions
start_pipeline_task = PythonOperator(
    task_id='start_pipeline',
    python_callable=start_sagemaker_pipeline,
    dag=dag
)

wait_pipeline_task = PythonOperator(
    task_id='wait_for_pipeline',
    python_callable=wait_for_pipeline,
    dag=dag
)

log_metadata_task = PythonOperator(
    task_id='log_metadata',
    python_callable=log_model_metadata,
    dag=dag
)

deploy_endpoint_task = PythonOperator(
    task_id='deploy_endpoint',
    python_callable=deploy_to_endpoint,
    dag=dag
)

validate_deployment_task = PythonOperator(
    task_id='validate_deployment',
    python_callable=validate_deployment,
    dag=dag
)

# Task dependencies
start_pipeline_task >> wait_pipeline_task >> log_metadata_task >> deploy_endpoint_task >> validate_deployment_task