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


def log_model_to_mlflow(**context):
    """Create an MLflow run and log model metadata + evaluation metrics from S3."""
    s3_client = boto3.client("s3", region_name=REGION_NAME)

    # 1. Get or create experiment
    experiment_id = "0"  # default
    try:
        # Try to create experiment
        experiment_payload = {"name": MLFLOW_EXPERIMENT_NAME}
        create_response = requests.post(
            f"{MLFLOW_URL}/api/2.0/mlflow/experiments/create",
            json=experiment_payload,
            timeout=5,
        )
        if create_response.status_code == 200:
            experiment_id = create_response.json().get("experiment_id", "0")
            print(f"Created experiment: {MLFLOW_EXPERIMENT_NAME} with ID: {experiment_id}")
    except Exception as e:
        print(f"Experiment create failed, trying to get existing: {e}")
        
    # Try to get existing experiment if create failed
    if experiment_id == "0":
        try:
            get_response = requests.get(
                f"{MLFLOW_URL}/api/2.0/mlflow/experiments/get-by-name",
                params={"experiment_name": MLFLOW_EXPERIMENT_NAME},
                timeout=5,
            )
            if get_response.status_code == 200:
                experiment_id = get_response.json().get("experiment", {}).get("experiment_id", "0")
                print(f"Found existing experiment: {MLFLOW_EXPERIMENT_NAME} with ID: {experiment_id}")
        except Exception as e:
            print(f"Could not get experiment, using default: {e}")

    # 2. Start a new run
    run_payload = {
        "experiment_id": experiment_id,
        "start_time": int(datetime.now().timestamp() * 1000),
    }
    run_response = requests.post(
        f"{MLFLOW_URL}/api/2.0/mlflow/runs/create", json=run_payload
    )
    run_json = run_response.json()
    run_id = run_json.get("run", {}).get("info", {}).get("run_id")

    if not run_id:
        print(f"Failed to create MLflow run. Response was: {run_json}")
        return "mlflow_run_not_created"

    print(f"Created MLflow run: {run_id}")

    # 3. Log high-level parameters about this deployment
    params = [
        {"key": "pipeline_name", "value": PIPELINE_NAME},
        {"key": "endpoint_name", "value": ENDPOINT_NAME},
        {"key": "model_source", "value": "sagemaker-pipeline"},
    ]

    for param in params:
        requests.post(
            f"{MLFLOW_URL}/api/2.0/mlflow/runs/log-parameter",
            json={"run_id": run_id, **param},
        )

    # 4. Pull evaluation metrics from S3 and send to MLflow as metrics
    try:
        response = s3_client.get_object(Bucket=METRICS_BUCKET, Key=METRICS_KEY)
        metrics_data = json.loads(response["Body"].read().decode("utf-8"))

        if not isinstance(metrics_data, dict):
            print(
                f"Metrics file {METRICS_BUCKET}/{METRICS_KEY} did not contain a "
                f"JSON object. Got: {metrics_data}"
            )
        else:
            for metric_name, metric_value in metrics_data.items():
                requests.post(
                    f"{MLFLOW_URL}/api/2.0/mlflow/runs/log-metric",
                    json={
                        "run_id": run_id,
                        "key": metric_name,
                        "value": float(metric_value),
                    },
                )

            print(
                f"Logged metrics to MLflow run {run_id}: {list(metrics_data.keys())}"
            )
    except Exception as e:
        print(f"Could not retrieve or log metrics from S3: {e}")

    print(f"Finished logging model metadata to MLflow run: {run_id}")
    return run_id


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
    """Send a small test payload to the endpoint to verify predictions work."""
    sagemaker_runtime = boto3.client("sagemaker-runtime", region_name=REGION_NAME)

    # This payload must match your model's expected input format
    test_data = {
        "instances": [
            {
                "features": [
                    3,
                    2,
                    1500,
                    7000,
                    1,
                    0,
                    0,
                    3,
                    7,
                    1500,
                    0,
                    1990,
                    0,
                ]
            }
        ]
    }

    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Body=json.dumps(test_data),
        )

        result = json.loads(response["Body"].read().decode())
        print(f"Endpoint smoke test successful. Prediction: {result}")
        return result
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

    # 3. Log model metadata + evaluation metrics to MLflow
    log_model_to_mlflow_task = PythonOperator(
        task_id="log_model_to_mlflow",
        python_callable=log_model_to_mlflow,
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
        log_model_to_mlflow_task >> \
        verify_endpoint_deployment_task >> \
        smoke_test_endpoint_prediction_task