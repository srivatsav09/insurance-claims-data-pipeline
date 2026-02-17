"""
Post-load warehouse validation checks.
Runs after dbt transformations to verify data integrity across all layers.
"""

import os
import logging

import psycopg2

from psycopg2 import sql

logger = logging.getLogger(__name__)


def _table_ref(schema, table):
    """Build a properly quoted schema.table reference for psycopg2."""
    return sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(table))


def get_connection():
    """Create a psycopg2 connection to the warehouse database."""
    return psycopg2.connect(
        host=os.environ.get("WAREHOUSE_HOST", "localhost"),
        port=os.environ.get("WAREHOUSE_PORT", "5432"),
        dbname=os.environ.get("WAREHOUSE_DB", "insurance_warehouse"),
        user=os.environ.get("WAREHOUSE_USER", "warehouse"),
        password=os.environ.get("WAREHOUSE_PASSWORD", "warehouse123"),
    )


class WarehouseValidationError(Exception):
    """Raised when a warehouse validation check fails."""
    pass


def check_row_counts_across_layers(conn):
    """Verify no significant data loss between raw → staging → marts."""
    checks = [
        ("raw", "claims", "public_staging", "stg_claims", "claims"),
        ("raw", "policyholders", "public_staging", "stg_policyholders", "policyholders"),
        ("raw", "vehicles", "public_staging", "stg_vehicles", "vehicles"),
    ]

    results = {}
    with conn.cursor() as cur:
        for raw_schema, raw_table, stg_schema, stg_table, label in checks:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(_table_ref(raw_schema, raw_table)))
            raw_count = cur.fetchone()[0]

            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(_table_ref(stg_schema, stg_table)))
            staging_count = cur.fetchone()[0]

            if raw_count != staging_count:
                raise WarehouseValidationError(
                    f"Row count mismatch for {label}: raw={raw_count}, staging={staging_count}"
                )

            results[label] = {"raw": raw_count, "staging": staging_count}
            logger.info(f"PASS: {label} row count match: raw={raw_count}, staging={staging_count}")

    # Check fact table has expected rows
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(_table_ref("raw", "claims")))
        raw_claims = cur.fetchone()[0]

        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(_table_ref("public_marts", "fact_claims")))
        fact_count = cur.fetchone()[0]

        if fact_count != raw_claims:
            raise WarehouseValidationError(
                f"fact_claims row count ({fact_count}) doesn't match raw claims ({raw_claims})"
            )
        logger.info(f"PASS: fact_claims count matches raw: {fact_count}")

    return results


def check_referential_integrity(conn):
    """Verify all foreign keys in fact_claims point to valid dimension records."""
    checks = [
        ("policyholder_key", "public_marts", "dim_policyholder"),
        ("vehicle_key", "public_marts", "dim_vehicle"),
    ]

    fact_ref = _table_ref("public_marts", "fact_claims")
    with conn.cursor() as cur:
        for fk_col, dim_schema, dim_table in checks:
            dim_ref = _table_ref(dim_schema, dim_table)
            fk = sql.Identifier(fk_col)
            query = sql.SQL("""
                SELECT COUNT(*)
                FROM {} f
                LEFT JOIN {} d ON f.{} = d.{}
                WHERE d.{} IS NULL
            """).format(fact_ref, dim_ref, fk, fk, fk)
            cur.execute(query)
            orphan_count = cur.fetchone()[0]

            if orphan_count > 0:
                raise WarehouseValidationError(
                    f"Referential integrity violation: {orphan_count} orphan records "
                    f"in fact_claims.{fk_col} not found in {dim_schema}.{dim_table}"
                )
            logger.info(f"PASS: Referential integrity for {fk_col} → {dim_schema}.{dim_table}")


def check_data_freshness(conn, max_stale_days=1095):
    """Verify the most recent claim date is within expected range."""
    stg_ref = _table_ref("public_staging", "stg_claims")
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT MAX(claim_date) FROM {}").format(stg_ref))
        max_date = cur.fetchone()[0]

        cur.execute("SELECT CURRENT_DATE - %s::date", (max_date,))
        days_stale = cur.fetchone()[0]

    if days_stale > max_stale_days:
        raise WarehouseValidationError(
            f"Data is stale: most recent claim is {days_stale} days old (max: {max_stale_days})"
        )

    logger.info(f"PASS: Data freshness OK. Most recent claim: {max_date} ({days_stale} days ago)")
    return {"max_claim_date": str(max_date), "days_stale": days_stale}


def check_null_rates(conn):
    """Log null rates for critical columns in fact_claims."""
    critical_columns = [
        "claim_key", "policyholder_key", "vehicle_key",
        "claim_date", "claim_amount", "claim_type", "claim_status",
    ]

    fact_ref = _table_ref("public_marts", "fact_claims")
    results = {}
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(fact_ref))
        total = cur.fetchone()[0]

        for col in critical_columns:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {} WHERE {} IS NULL").format(
                fact_ref, sql.Identifier(col)
            ))
            null_count = cur.fetchone()[0]
            null_pct = (null_count / total * 100) if total > 0 else 0

            results[col] = {"null_count": null_count, "null_pct": round(null_pct, 2)}

            if null_pct > 5:
                raise WarehouseValidationError(
                    f"High null rate in fact_claims.{col}: {null_pct:.1f}% (threshold: 5%)"
                )

    logger.info(f"PASS: Null rate check complete. Results: {results}")
    return results


def run_all_post_load_checks():
    """Run all post-load warehouse validation checks."""
    conn = get_connection()
    try:
        logger.info("=" * 60)
        logger.info("POST-LOAD WAREHOUSE VALIDATION")
        logger.info("=" * 60)

        row_counts = check_row_counts_across_layers(conn)
        check_referential_integrity(conn)
        freshness = check_data_freshness(conn)
        null_rates = check_null_rates(conn)

        summary = {
            "row_counts": row_counts,
            "freshness": freshness,
            "null_rates": null_rates,
            "status": "ALL CHECKS PASSED",
        }

        logger.info("=" * 60)
        logger.info(f"VALIDATION COMPLETE: {summary['status']}")
        logger.info("=" * 60)

        return summary
    finally:
        conn.close()
