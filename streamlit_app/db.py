"""
Database connection and query helpers for the Streamlit dashboard.
Uses psycopg2 with Streamlit caching for performance.
"""

import os

import pandas as pd
import psycopg2
import streamlit as st


def get_connection():
    """Create a psycopg2 connection to the warehouse database."""
    return psycopg2.connect(
        host=os.environ.get("WAREHOUSE_HOST", "localhost"),
        port=os.environ.get("WAREHOUSE_PORT", "5432"),
        dbname=os.environ.get("WAREHOUSE_DB", "insurance_warehouse"),
        user=os.environ.get("WAREHOUSE_USER", "warehouse"),
        password=os.environ.get("WAREHOUSE_PASSWORD", "warehouse123"),
    )


def run_query(query, params=None):
    """Execute a query and return results as a DataFrame."""
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


@st.cache_data(ttl=300)
def get_monthly_claims():
    """Get pre-aggregated monthly claims KPIs."""
    return run_query("""
        SELECT * FROM "public_marts"."agg_monthly_claims"
        ORDER BY month
    """)


@st.cache_data(ttl=300)
def get_fact_claims():
    """Get all fact claims with region info."""
    return run_query("""
        SELECT
            f.*,
            r.region_name,
            r.state
        FROM "public_marts"."fact_claims" f
        LEFT JOIN "public_marts"."dim_region" r ON f.region_key = r.region_key
    """)


@st.cache_data(ttl=300)
def get_claims_by_vehicle():
    """Get claim counts by vehicle make."""
    return run_query("""
        SELECT
            v.make,
            COUNT(*) as claim_count,
            ROUND(AVG(f.claim_amount), 2) as avg_claim_amount
        FROM "public_marts"."fact_claims" f
        JOIN "public_marts"."dim_vehicle" v ON f.vehicle_key = v.vehicle_key
        GROUP BY v.make
        ORDER BY claim_count DESC
    """)


@st.cache_data(ttl=300)
def get_claims_by_region():
    """Get claim counts and averages by region."""
    return run_query("""
        SELECT
            r.region_name,
            COUNT(*) as claim_count,
            ROUND(AVG(f.claim_amount), 2) as avg_claim_amount,
            ROUND(COUNT(*) FILTER (WHERE f.fraud_flag = true)::numeric
                / NULLIF(COUNT(*), 0) * 100, 2) as fraud_rate_pct
        FROM "public_marts"."fact_claims" f
        JOIN "public_marts"."dim_region" r ON f.region_key = r.region_key
        GROUP BY r.region_name
        ORDER BY claim_count DESC
    """)


@st.cache_data(ttl=300)
def get_claims_by_age_group():
    """Get claim stats by policyholder age group."""
    return run_query("""
        SELECT
            p.age_group,
            COUNT(*) as claim_count,
            ROUND(AVG(f.claim_amount), 2) as avg_claim_amount
        FROM "public_marts"."fact_claims" f
        JOIN "public_marts"."dim_policyholder" p ON f.policyholder_key = p.policyholder_key
        GROUP BY p.age_group
        ORDER BY p.age_group
    """)
