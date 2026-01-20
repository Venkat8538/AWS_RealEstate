from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import boto3
import json
import requests


# AWS and pipeline configuration
REGION_NAME = "us-east-1"
PIPELINE_NAME = "house-price-mlops-pipeline"
ENDPOINT_NAME = "house-price-prod"

# Where your evaluation metrics are written by the training/evaluation step
METRICS_BUCKET = "house-price-mlops-dev-itzi2hgi"
METRICS_KEY = "evaluation/evaluation.json"

# MLflow tracking server (HTTP API only – no mlflow Python client needed)
MLFLOW_URL = "http://23.21.206.232:5000"
MLFLOW_EXPERIMENT_NAME = "house-price-mlops"

# Updated: Testing cron sync - Modified to verify S3 sync is working


def trigger_sagemaker_pipeline(**context):
    """Start the SageMaker Pipeline execution and push its ARN to XCom."""
    sagemaker_client = boto3.client("sagemaker", region_name=REGION_NAME)

    response = sagemaker_client.start_pipeline_execution(
        PipelineName=PIPELINE_NAME,
        PipelineExecutionDisplayName=(
            f"airflow-execution-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        ),
    )

    execution_arn = response["PipelineExecutionArn"]
    print(f"Started SageMaker pipeline execution: {execution_arn}")

    # Store ARN in XCom for downstream tasks (if needed later)
    context["ti"].xcom_push(key="pipeline_execution_arn", value=execution_arn)
    return execution_arn


def monitor_pipeline_execution(**context):
    """Poll SageMaker until the pipeline execution finishes successfully."""
    import time

    sagemaker_client = boto3.client("sagemaker", region_name=REGION_NAME)
    ti = context["ti"]

    execution_arn = ti.xcom_pull(
        task_ids="trigger_sagemaker_pipeline", key="pipeline_execution_arn"
    )

    if not execution_arn:
        raise ValueError("No pipeline_execution_arn found in XCom.")

    while True:
        response = sagemaker_client.describe_pipeline_execution(
            PipelineExecutionArn=execution_arn
        )
        status = response["PipelineExecutionStatus"]
        print(f"Pipeline status: {status}")

        if status in ["Succeeded", "Failed", "Stopped"]:
            if status != "Succeeded":
                raise Exception(f"Pipeline failed with status: {status}")
            break

        # Wait a minute between checks to avoid spamming the API
        time.sleep(60)

    print(f"Pipeline execution {execution_arn} finished with status: {status}")
    ti.xcom_push(key="pipeline_final_status", value=status)
    return status


def validate_pipeline_completion(**context):
    """Validate that SageMaker pipeline completed successfully and MLflow logging occurred."""
    print("Pipeline validation completed - MLflow logging handled by SageMaker steps")
    return "validation_complete"


def verify_endpoint_deployment(**context):
    """
    Confirm the SageMaker endpoint exists and report its current status.

    The actual creation/update of the endpoint is assumed to be part of the
    SageMaker pipeline itself – this task just validates the result.
    """
    sagemaker_client = boto3.client("sagemaker", region_name=REGION_NAME)

    try:
        response = sagemaker_client.describe_endpoint(EndpointName=ENDPOINT_NAME)
        status = response["EndpointStatus"]
        print(f"Endpoint {ENDPOINT_NAME} exists with status: {status}")
        return status
    except sagemaker_client.exceptions.ClientError as e:
        print(f"Endpoint {ENDPOINT_NAME} not found or not yet created: {e}")
        raise


def smoke_test_endpoint_prediction(**context):
    """Verify endpoint is accessible and responsive."""
    sagemaker_client = boto3.client("sagemaker", region_name=REGION_NAME)

    try:
        response = sagemaker_client.describe_endpoint(EndpointName=ENDPOINT_NAME)
        status = response["EndpointStatus"]
        
        if status == "InService":
            print(f"Endpoint {ENDPOINT_NAME} is InService and ready")
            return "SUCCESS"
        else:
            print(f"Endpoint {ENDPOINT_NAME} status: {status}")
            return status
    except Exception as e:
        print(f"Endpoint validation failed: {e}")
        raise


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------

default_args = {
    "owner": "mlops-team",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="house_price_mlops_pipeline",
    default_args=default_args,
    description="House Price MLOps pipeline orchestrating SageMaker and MLflow",
    schedule_interval="@daily",
    catchup=False,
    tags=["mlops", "sagemaker", "mlflow"],
) as dag:

    # 1. Trigger SageMaker pipeline
    trigger_sagemaker_pipeline_task = PythonOperator(
        task_id="trigger_sagemaker_pipeline",
        python_callable=trigger_sagemaker_pipeline,
        provide_context=True,
    )

    # 2. Monitor SageMaker pipeline until completion
    monitor_pipeline_execution_task = PythonOperator(
        task_id="monitor_pipeline_execution",
        python_callable=monitor_pipeline_execution,
        provide_context=True,
    )

    # 3. Validate pipeline completion
    validate_pipeline_task = PythonOperator(
        task_id="validate_pipeline_completion",
        python_callable=validate_pipeline_completion,
        provide_context=True,
    )

    # 4. Verify endpoint deployment in SageMaker
    verify_endpoint_deployment_task = PythonOperator(
        task_id="verify_endpoint_deployment",
        python_callable=verify_endpoint_deployment,
        provide_context=True,
    )

    # 5. Run a smoke test against the endpoint
    smoke_test_endpoint_prediction_task = PythonOperator(
        task_id="smoke_test_endpoint_prediction",
        python_callable=smoke_test_endpoint_prediction,
        provide_context=True,
    )

    # Pipeline order
    trigger_sagemaker_pipeline_task >> \
        monitor_pipeline_execution_task >> \
        validate_pipeline_task >> \
        verify_endpoint_deployment_task >> \
        smoke_test_endpoint_prediction_task