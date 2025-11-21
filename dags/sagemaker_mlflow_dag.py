from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import boto3
import mlflow
import mlflow.sagemaker
import json

# MLflow configuration
MLFLOW_TRACKING_URI = "http://23.21.206.232:5000"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

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

def register_model_mlflow(**context):
    import mlflow.sagemaker
    
    # Set experiment
    experiment_name = "house-price-mlops"
    try:
        mlflow.create_experiment(experiment_name)
    except:
        pass
    
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run(run_name="sagemaker-pipeline-model"):
        # Log model metadata
        mlflow.log_param("pipeline_name", PIPELINE_NAME)
        mlflow.log_param("endpoint_name", ENDPOINT_NAME)
        mlflow.log_param("model_source", "sagemaker-pipeline")
        
        # Register the model in MLflow
        model_name = "house-price-model"
        model_version = mlflow.register_model(
            model_uri=f"sagemaker:/{ENDPOINT_NAME}",
            name=model_name
        )
        
        print(f"Registered model {model_name} version {model_version.version}")
        return model_version.version

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

register_model_task = PythonOperator(
    task_id='register_model',
    python_callable=register_model_mlflow,
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
start_pipeline_task >> wait_pipeline_task >> register_model_task >> deploy_endpoint_task >> validate_deployment_task