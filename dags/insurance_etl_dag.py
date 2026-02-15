"""
Insurance Claims ETL DAG - Phase 1
Tasks: generate synthetic data → validate quality → load into raw schema
"""

import os
import sys
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Add project root to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)

DATA_DIR = "/opt/airflow/data/raw"

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


with DAG(
    dag_id="insurance_claims_etl",
    default_args=default_args,
    description="Insurance Claims ETL Pipeline - Batch Processing",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["insurance", "etl", "phase1"],
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

    generate >> validate >> load_raw
