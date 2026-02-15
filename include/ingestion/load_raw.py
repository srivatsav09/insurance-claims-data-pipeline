"""
Raw data ingestion module.
Loads CSV files from data/raw/ into PostgreSQL raw schema.
Uses psycopg2 COPY for fast bulk loading.
"""

import io
import os
import logging

import pandas as pd
import psycopg2

logger = logging.getLogger(__name__)

TABLE_SCHEMAS = {
    "claims": {
        "claim_id": "VARCHAR(20) PRIMARY KEY",
        "policy_id": "VARCHAR(20) NOT NULL",
        "vehicle_id": "VARCHAR(20) NOT NULL",
        "claim_date": "DATE NOT NULL",
        "claim_amount": "NUMERIC(12,2) NOT NULL",
        "claim_type": "VARCHAR(20) NOT NULL",
        "status": "VARCHAR(20) NOT NULL",
        "fraud_flag": "BOOLEAN",
        "incident_city": "VARCHAR(100)",
        "incident_state": "VARCHAR(5)",
        "police_report_filed": "BOOLEAN",
        "witnesses": "INTEGER",
        "injury_claim": "NUMERIC(12,2)",
        "property_claim": "NUMERIC(12,2)",
    },
    "policyholders": {
        "policy_id": "VARCHAR(20) PRIMARY KEY",
        "first_name": "VARCHAR(50)",
        "last_name": "VARCHAR(50)",
        "gender": "VARCHAR(5)",
        "age": "INTEGER",
        "income_bracket": "VARCHAR(20)",
        "education": "VARCHAR(30)",
        "occupation": "VARCHAR(30)",
        "marital_status": "VARCHAR(20)",
        "policy_start_date": "DATE",
        "policy_end_date": "DATE",
        "premium_amount": "NUMERIC(10,2)",
        "deductible": "NUMERIC(10,2)",
        "region_code": "VARCHAR(20)",
        "state": "VARCHAR(5)",
    },
    "vehicles": {
        "vehicle_id": "VARCHAR(20) PRIMARY KEY",
        "policy_id": "VARCHAR(20) NOT NULL",
        "make": "VARCHAR(30)",
        "model": "VARCHAR(30)",
        "year": "INTEGER",
        "vehicle_age": "INTEGER",
        "fuel_type": "VARCHAR(20)",
        "annual_mileage": "INTEGER",
    },
}


def get_connection():
    """Create a psycopg2 connection to the warehouse database."""
    return psycopg2.connect(
        host=os.environ.get("WAREHOUSE_HOST", "localhost"),
        port=os.environ.get("WAREHOUSE_PORT", "5432"),
        dbname=os.environ.get("WAREHOUSE_DB", "insurance_warehouse"),
        user=os.environ.get("WAREHOUSE_USER", "warehouse"),
        password=os.environ.get("WAREHOUSE_PASSWORD", "warehouse123"),
    )


def create_raw_schema(conn):
    """Create the raw schema if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw")
    conn.commit()
    logger.info("Schema 'raw' ensured.")


def create_table(conn, table_name, columns):
    """Drop and recreate a table in the raw schema."""
    col_defs = ", ".join(f"{col} {dtype}" for col, dtype in columns.items())
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS raw.{table_name} CASCADE")
        cur.execute(f"CREATE TABLE raw.{table_name} ({col_defs})")
    conn.commit()
    logger.info(f"Table raw.{table_name} created.")


def load_csv_to_table(conn, table_name, csv_path):
    """Load a CSV file into a raw schema table using COPY for performance."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    row_count = len(df)
    logger.info(f"Loading {row_count:,} rows from {csv_path} into raw.{table_name}...")

    # Create the table first
    create_table(conn, table_name, TABLE_SCHEMAS[table_name])

    # Use COPY for fast bulk loading
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, sep="\t", na_rep="\\N")
    buffer.seek(0)

    columns = list(TABLE_SCHEMAS[table_name].keys())
    with conn.cursor() as cur:
        cur.execute("SET search_path TO raw")
        cur.copy_from(
            file=buffer,
            table=table_name,
            sep="\t",
            null="\\N",
            columns=columns,
        )
    conn.commit()

    # Verify row count
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM raw.{table_name}")
        db_count = cur.fetchone()[0]

    if db_count != row_count:
        raise RuntimeError(
            f"Row count mismatch for {table_name}: CSV={row_count}, DB={db_count}"
        )

    logger.info(f"Successfully loaded {db_count:,} rows into raw.{table_name}.")
    return db_count


def load_all_raw_data(data_dir=None):
    """Main entry point: load all CSV files into the raw schema."""
    if data_dir is None:
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "raw",
        )

    conn = get_connection()
    try:
        create_raw_schema(conn)

        results = {}
        for table_name in TABLE_SCHEMAS:
            csv_path = os.path.join(data_dir, f"{table_name}.csv")
            count = load_csv_to_table(conn, table_name, csv_path)
            results[table_name] = count

        logger.info(f"All raw data loaded: {results}")
        return results
    finally:
        conn.close()
