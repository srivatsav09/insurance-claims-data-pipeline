"""
Data quality validation checks for raw CSV files.
Run before loading into the warehouse to catch issues early.
"""

import os
import logging

import pandas as pd

logger = logging.getLogger(__name__)

EXPECTED_SCHEMAS = {
    "claims": {
        "required_columns": [
            "claim_id", "policy_id", "vehicle_id", "claim_date",
            "claim_amount", "claim_type", "status",
        ],
        "primary_key": "claim_id",
        "min_rows": 1000,
    },
    "policyholders": {
        "required_columns": [
            "policy_id", "first_name", "last_name", "age",
            "policy_start_date", "premium_amount",
        ],
        "primary_key": "policy_id",
        "min_rows": 500,
    },
    "vehicles": {
        "required_columns": [
            "vehicle_id", "policy_id", "make", "model", "year",
        ],
        "primary_key": "vehicle_id",
        "min_rows": 500,
    },
}


class DataQualityError(Exception):
    """Raised when a data quality check fails."""
    pass


def check_file_exists(filepath):
    """Verify the CSV file exists and is non-empty."""
    if not os.path.exists(filepath):
        raise DataQualityError(f"File not found: {filepath}")
    if os.path.getsize(filepath) == 0:
        raise DataQualityError(f"File is empty: {filepath}")
    logger.info(f"PASS: File exists and non-empty: {filepath}")


def check_schema(df, table_name):
    """Verify all required columns are present."""
    schema = EXPECTED_SCHEMAS[table_name]
    missing = set(schema["required_columns"]) - set(df.columns)
    if missing:
        raise DataQualityError(
            f"Missing columns in {table_name}: {missing}"
        )
    logger.info(f"PASS: Schema valid for {table_name} ({len(df.columns)} columns)")


def check_row_count(df, table_name):
    """Verify minimum row count."""
    schema = EXPECTED_SCHEMAS[table_name]
    if len(df) < schema["min_rows"]:
        raise DataQualityError(
            f"{table_name} has {len(df)} rows, expected >= {schema['min_rows']}"
        )
    logger.info(f"PASS: Row count for {table_name}: {len(df):,}")


def check_no_duplicate_keys(df, table_name):
    """Verify no duplicate primary keys."""
    schema = EXPECTED_SCHEMAS[table_name]
    pk = schema["primary_key"]
    duplicates = df[pk].duplicated().sum()
    if duplicates > 0:
        raise DataQualityError(
            f"{table_name} has {duplicates} duplicate {pk} values"
        )
    logger.info(f"PASS: No duplicate keys in {table_name}")


def check_null_threshold(df, table_name, threshold=0.1):
    """Verify required columns don't exceed null threshold."""
    schema = EXPECTED_SCHEMAS[table_name]
    for col in schema["required_columns"]:
        null_pct = df[col].isnull().mean()
        if null_pct > threshold:
            raise DataQualityError(
                f"{table_name}.{col} has {null_pct:.1%} nulls (threshold: {threshold:.0%})"
            )
    logger.info(f"PASS: Null check for {table_name} (threshold={threshold:.0%})")


def validate_all(data_dir):
    """Run all quality checks on all CSV files. Returns summary dict."""
    results = {}

    for table_name, schema in EXPECTED_SCHEMAS.items():
        filepath = os.path.join(data_dir, f"{table_name}.csv")
        logger.info(f"--- Validating {table_name} ---")

        check_file_exists(filepath)
        df = pd.read_csv(filepath)
        check_schema(df, table_name)
        check_row_count(df, table_name)
        check_no_duplicate_keys(df, table_name)
        check_null_threshold(df, table_name)

        results[table_name] = {
            "rows": len(df),
            "columns": len(df.columns),
            "status": "PASSED",
        }

    logger.info(f"All quality checks passed: {results}")
    return results
