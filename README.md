# Insurance Claims ETL & Warehouse Platform

A production-style batch data pipeline that ingests synthetic insurance claims data, transforms it through a multi-layer warehouse using dbt, validates data quality at every stage, and serves analytics through an interactive Streamlit dashboard.

## Architecture

```
Raw CSVs ──→ Airflow DAG ──→ PostgreSQL (raw) ──→ dbt (staging → intermediate → marts) ──→ Streamlit Dashboard
                                                          ↓
                                                  Data Quality Checks
                                                  Pipeline Metrics
```

**Pipeline Flow (8 Airflow Tasks):**
```
generate_data → validate_data → load_raw_data → dbt_deps → dbt_run → dbt_test → post_load_validation → log_pipeline_metrics
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | Apache Airflow 2.10 |
| Database | PostgreSQL 16 |
| Transformations | dbt-postgres 1.9 |
| Data Generation | Python + Faker |
| Dashboard | Streamlit + Plotly |
| Containerization | Docker + Docker Compose |
| Admin | pgAdmin 4 |

## Data Model

**Star Schema (marts layer):**

- `fact_claims` — 50K claims with surrogate keys linking to all dimensions
- `dim_policyholder` — 10K policyholders with demographics and policy details
- `dim_vehicle` — 12K vehicles with make, model, age buckets, mileage categories
- `dim_region` — US states mapped to 4 regions (Northeast, South, Midwest, West)
- `agg_monthly_claims` — Pre-aggregated monthly KPIs (approval rate, fraud rate, claim breakdowns)

## Project Structure

```
insurance-claims-pipeline/
├── docker-compose.yml              # All services (Airflow, PostgreSQL x2, pgAdmin, Streamlit)
├── Dockerfile                      # Custom Airflow image with dbt + dependencies
├── requirements.txt                # Python dependencies for Airflow image
│
├── dags/
│   └── insurance_etl_dag.py        # Main DAG: 8-task pipeline
│
├── scripts/
│   └── generate_data.py            # Faker-based synthetic data generator
│
├── include/
│   ├── ingestion/
│   │   └── load_raw.py             # Bulk CSV → PostgreSQL loader (psycopg2 COPY)
│   ├── quality/
│   │   ├── checks.py               # Pre-load CSV validation
│   │   └── post_load_checks.py     # Post-dbt warehouse integrity checks
│   └── observability/
│       └── metrics.py              # Pipeline metrics logger
│
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── packages.yml                # dbt_utils for surrogate keys
│   └── models/
│       ├── sources.yml             # Raw schema source definitions
│       ├── staging/                # 1:1 clean/cast/rename from raw
│       ├── intermediate/           # Enriched joins + derived metrics
│       └── marts/                  # Star schema fact + dimensions
│
├── streamlit_app/
│   ├── Dockerfile                  # Lightweight Python image for dashboard
│   ├── requirements.txt
│   ├── db.py                       # Database connection + cached queries
│   └── app.py                      # Interactive analytics dashboard
│
└── data/raw/                       # Generated CSVs (gitignored)
```

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/insurance-claims-etl-warehouse.git
cd insurance-claims-etl-warehouse

# Start all services
docker-compose up -d
```

Wait ~60 seconds for all services to initialize, then:

1. **Airflow UI** — http://localhost:8080 (login: `admin` / `admin`)
2. Trigger the `insurance_claims_etl` DAG
3. Wait for all 8 tasks to turn green
4. **Streamlit Dashboard** — http://localhost:8501
5. **pgAdmin** — http://localhost:5050 (login: `admin@admin.com` / `admin123`)

### Tear Down

```bash
docker-compose down           # Stop containers (keeps data)
docker-compose down -v        # Stop containers + delete volumes
```

## Dashboard

The Streamlit dashboard connects directly to the warehouse marts and displays:

- **KPI Cards** — Total claims, average claim amount, approval rate, fraud rate
- **Monthly Claims Trend** — Line chart tracking claim volume over time
- **Claims by Type** — Collision, Liability, Comprehensive, Theft breakdown
- **Claims by Region** — Geographic distribution across US regions
- **Fraud Rate Over Time** — Monthly fraud trend
- **Claim Amount Distribution** — Histogram of claim values
- **Top Vehicle Makes** — Which car brands have the most claims
- **Approval vs Denial Rate** — Monthly approval/denial trends
- **Sidebar Filters** — Filter by claim type, region, and fraud flag

## Data Quality

Quality is enforced at 3 levels:

1. **Pre-load validation** (`checks.py`) — Schema validation, null thresholds, duplicate detection, row count minimums on raw CSVs
2. **dbt tests** (37 tests) — Unique keys, not-null constraints, accepted values, referential integrity, no negative amounts
3. **Post-load validation** (`post_load_checks.py`) — Cross-layer row count comparison, data freshness, referential integrity between fact and dimensions

## Observability

Every pipeline run logs metrics to `observability.pipeline_metrics`:
- Row counts across all layers (raw, staging, marts)
- Task status (success/fail) with duration
- Error messages and metadata (JSONB)

## Services & Ports

| Service | Port | Description |
|---------|------|-------------|
| Airflow Webserver | 8080 | DAG management and monitoring |
| Streamlit | 8501 | Analytics dashboard |
| pgAdmin | 5050 | Database administration |
| Warehouse DB | 5432 | Project PostgreSQL (insurance_warehouse) |
| Airflow DB | 5433 | Airflow metadata PostgreSQL |

## Built With

Python 3.11 | Apache Airflow 2.10 | dbt 1.9 | PostgreSQL 16 | Streamlit 1.41 | Plotly 5.24 | Docker Compose
