"""
Insurance Claims ETL DAG
Tasks: generate → validate → load_raw → dbt_deps → dbt_run → dbt_test
       → post_load_validation → log_pipeline_metrics
"""

import os
import sys
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Add project root to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)

DATA_DIR = "/opt/airflow/data/raw"
DBT_PROJECT_DIR = "/opt/airflow/dbt_project"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def task_generate_data(**kwargs):
    """Generate synthetic insurance data CSVs."""
    from scripts.generate_data import main as generate_main

    # Check if files already exist and skip if so (idempotent)
    files = ["claims.csv", "policyholders.csv", "vehicles.csv"]
    all_exist = all(
        os.path.exists(os.path.join(DATA_DIR, f)) for f in files
    )

    if all_exist:
        logger.info("Data files already exist. Regenerating for fresh run...")

    generate_main()
    logger.info("Data generation complete.")


def task_validate_data(**kwargs):
    """Run data quality checks on generated CSVs."""
    from include.quality.checks import validate_all

    results = validate_all(DATA_DIR)

    # Push results to XCom for downstream visibility
    kwargs["ti"].xcom_push(key="validation_results", value=results)
    logger.info(f"Validation results: {results}")


def task_load_raw(**kwargs):
    """Load validated CSVs into PostgreSQL raw schema."""
    from include.ingestion.load_raw import load_all_raw_data

    results = load_all_raw_data(data_dir=DATA_DIR)

    kwargs["ti"].xcom_push(key="load_results", value=results)
    logger.info(f"Load results: {results}")


def task_post_load_validation(**kwargs):
    """Run post-load warehouse validation checks."""
    from include.quality.post_load_checks import run_all_post_load_checks

    results = run_all_post_load_checks()

    kwargs["ti"].xcom_push(key="validation_summary", value=results)
    logger.info(f"Post-load validation: {results['status']}")


def task_log_pipeline_metrics(**kwargs):
    """Log pipeline metrics for this run to the observability table."""
    from include.observability.metrics import log_row_counts, log_metric

    run_id = kwargs["run_id"]
    dag_id = kwargs["dag"].dag_id

    # Log row counts across all layers
    row_counts = log_row_counts(run_id, dag_id)

    # Log overall pipeline success
    log_metric(
        run_id=run_id,
        dag_id=dag_id,
        task_id="pipeline_summary",
        status="success",
        metadata={"row_counts": {k: v for k, v in row_counts.items() if isinstance(v, int)}},
    )

    logger.info(f"Pipeline metrics logged for run: {run_id}")


with DAG(
    dag_id="insurance_claims_etl",
    default_args=default_args,
    description="Insurance Claims ETL Pipeline - Batch Processing",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["insurance", "etl", "dbt", "observability"],
) as dag:

    generate = PythonOperator(
        task_id="generate_data",
        python_callable=task_generate_data,
    )

    validate = PythonOperator(
        task_id="validate_data",
        python_callable=task_validate_data,
    )

    load_raw = PythonOperator(
        task_id="load_raw_data",
        python_callable=task_load_raw,
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps --profiles-dir {DBT_PROJECT_DIR} --project-dir {DBT_PROJECT_DIR}",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt run --profiles-dir {DBT_PROJECT_DIR} --project-dir {DBT_PROJECT_DIR}",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt test --profiles-dir {DBT_PROJECT_DIR} --project-dir {DBT_PROJECT_DIR}",
    )

    post_load_validation = PythonOperator(
        task_id="post_load_validation",
        python_callable=task_post_load_validation,
    )

    log_metrics = PythonOperator(
        task_id="log_pipeline_metrics",
        python_callable=task_log_pipeline_metrics,
    )

    generate >> validate >> load_raw >> dbt_deps >> dbt_run >> dbt_test >> post_load_validation >> log_metrics
