"""
Pipeline observability module.
Logs pipeline metrics to observability.pipeline_metrics table for audit and monitoring.
"""

import os
import logging
from datetime import datetime

import psycopg2
import psycopg2.extras
from psycopg2 import sql

logger = logging.getLogger(__name__)


def get_connection():
    """Create a psycopg2 connection to the warehouse database."""
    return psycopg2.connect(
        host=os.environ.get("WAREHOUSE_HOST", "localhost"),
        port=os.environ.get("WAREHOUSE_PORT", "5432"),
        dbname=os.environ.get("WAREHOUSE_DB", "insurance_warehouse"),
        user=os.environ.get("WAREHOUSE_USER", "warehouse"),
        password=os.environ.get("WAREHOUSE_PASSWORD", "warehouse123"),
    )


def ensure_metrics_table(conn):
    """Create the observability schema and pipeline_metrics table if they don't exist."""
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS observability")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS observability.pipeline_metrics (
                id SERIAL PRIMARY KEY,
                run_id VARCHAR(200),
                dag_id VARCHAR(100),
                task_id VARCHAR(100),
                run_timestamp TIMESTAMP DEFAULT NOW(),
                table_name VARCHAR(100),
                row_count INTEGER,
                status VARCHAR(20),
                duration_seconds NUMERIC(10,2),
                error_message TEXT,
                metadata JSONB
            )
        """)
    conn.commit()
    logger.info("observability.pipeline_metrics table ensured.")


def log_metric(run_id, dag_id, task_id, table_name=None, row_count=None,
               status="success", duration_seconds=None, error_message=None, metadata=None):
    """Log a single pipeline metric row."""
    conn = get_connection()
    try:
        ensure_metrics_table(conn)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO observability.pipeline_metrics
                    (run_id, dag_id, task_id, table_name, row_count, status,
                     duration_seconds, error_message, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                run_id, dag_id, task_id, table_name, row_count,
                status, duration_seconds, error_message,
                psycopg2.extras.Json(metadata) if metadata else None,
            ))
        conn.commit()
        logger.info(f"Metric logged: {task_id} | {table_name} | {status}")
    finally:
        conn.close()


def log_row_counts(run_id, dag_id):
    """Query row counts across all layers and log them as metrics."""
    conn = get_connection()
    try:
        ensure_metrics_table(conn)

        layer_tables = [
            ("raw", "claims", "raw"),
            ("raw", "policyholders", "raw"),
            ("raw", "vehicles", "raw"),
            ("public_staging", "stg_claims", "staging"),
            ("public_staging", "stg_policyholders", "staging"),
            ("public_staging", "stg_vehicles", "staging"),
            ("public_marts", "fact_claims", "marts"),
            ("public_marts", "dim_policyholder", "marts"),
            ("public_marts", "dim_vehicle", "marts"),
            ("public_marts", "dim_region", "marts"),
            ("public_marts", "agg_monthly_claims", "marts"),
        ]

        results = {}
        with conn.cursor() as cur:
            for schema, table_name, layer in layer_tables:
                table = f"{schema}.{table_name}"
                try:
                    table_ref = sql.SQL("{}.{}").format(
                        sql.Identifier(schema), sql.Identifier(table_name)
                    )
                    cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(table_ref))
                    count = cur.fetchone()[0]
                    results[table] = count

                    cur.execute("""
                        INSERT INTO observability.pipeline_metrics
                            (run_id, dag_id, task_id, table_name, row_count, status, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        run_id, dag_id, "log_pipeline_metrics", table, count,
                        "success", psycopg2.extras.Json({"layer": layer}),
                    ))
                except Exception as e:
                    logger.warning(f"Could not count {table}: {e}")
                    results[table] = f"ERROR: {e}"

        conn.commit()
        logger.info(f"Row counts logged: {results}")
        return results
    finally:
        conn.close()


def get_run_summary(run_id):
    """Get all metrics for a given run_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT task_id, table_name, row_count, status, duration_seconds, error_message
                FROM observability.pipeline_metrics
                WHERE run_id = %s
                ORDER BY run_timestamp
            """, (run_id,))
            rows = cur.fetchall()
        return rows
    finally:
        conn.close()
