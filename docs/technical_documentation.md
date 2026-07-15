# FashionFlow — Technical Documentation

## Architecture Overview

FashionFlow is an enterprise-grade data platform for a simulated fashion ecommerce business. It demonstrates a complete vertical slice from source system to analytics-ready warehouse.

```
                           FastAPI Source Systems
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
   Commerce (7)              Marketing (4)              Inventory (2)
   ├ customers               ├ campaigns                ├ inventory_snapshots
   ├ products                ├ ad_sets                  └ inventory_movements
   ├ categories              ├ ads
   ├ orders                  └ daily_performance
   ├ order_items
   ├ payments
   └ refunds
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                              dltHub Pipelines
                          (incremental merge loading)
                                    │
                                    ▼
                         BigQuery Raw Layer (13 tables)
                                    │
                                    ▼
                     dbt Staging Models (12 views)
                                    │
                          ┌─────────┼─────────┐
                          │         │         │
                     Fact Tables  Snapshots  Reconciliation
                     (2 tables)  (products)  (3 models)
                                    │
                                    ▼
                    Dagster Orchestration (5 jobs)
                    ├ Asset checks (freshness, row counts)
                    ├ Retry policies (exponential backoff)
                    └ Backfill support
                                    │
                                    ▼
                    Audit Logging → BigQuery (fashionflow_audit)
                    Quarantine    → BigQuery (fashionflow_quarantine)
```

## Data Flow

1. **Source System**: FastAPI serves data from SQLite. Historical data generated via Faker. Continuous generator simulates live activity.
2. **Ingestion**: dltHub pipelines extract from API with pagination, load into BigQuery raw layer using merge (upsert) with `updated_at` cursor.
3. **Transformation**: dbt Core builds staging views (type casting, renaming, standardization) and fact tables (aggregated business metrics).
4. **Orchestration**: Dagster coordinates the flow with asset dependencies, retry policies, and asset checks.

## Warehouse Design

| Dataset | Purpose | Materialization |
|---------|---------|-----------------|
| `fashionflow_raw` | Source-conformed data from dlt | Tables (merge) |
| `fashionflow_staging` | Cleaned, typed, renamed models | Views |
| `fashionflow_mart` | Business-layer analytics tables | Tables |
| `fashionflow_snapshots` | Historical product SCD Type 2 | Tables |
| `fashionflow_audit` | Pipeline execution metadata | Tables |
| `fashionflow_quarantine` | Invalid records for investigation | Tables |

## Pipeline Descriptions

### Commerce Pipeline
Loads customers, products, orders, order items, payments, and refunds. Supports incremental merge with 1-hour lookback window.

### Marketing Pipeline
Loads campaigns, ad sets, ads, and daily performance metrics across Google Ads and Meta Ads platforms.

### Inventory Pipeline
Loads weekly inventory snapshots and daily inventory movements linked to product catalog.

## Configuration Guide

All configuration is environment-driven via `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud project | — |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | — |
| `BQ_DATASET_RAW` | Raw dataset name | `fashionflow_raw` |
| `SOURCE_API_KEY` | API authentication key | — |
| `SOURCE_DB_PATH` | SQLite database path | `data/fashionflow.db` |
| `DAGSTER_HOME` | Dagster instance directory | `.dagster` |

## Runbook

### Initial Setup
```bash
uv sync --extra dev
cp .env.example .env
# Edit .env with your GCP credentials
uv run python -m source_system.database.seed
```

### Run Full Pipeline
```bash
# Terminal 1: Start API
uv run uvicorn source_system.api.main:app

# Terminal 2: Run ingestion
uv run python -m ingestion.pipeline

# Terminal 3: Run dbt
uv run dbt run --project-dir transformations --profiles-dir transformations
uv run dbt test --project-dir transformations --profiles-dir transformations
```

### Run via Dagster
```bash
uv run dagster dev
# Open http://localhost:3000 → Materialize all
```

### Schema Evolution
```bash
uv run python -m source_system.database.schema_evolution
uv run python -m ingestion.pipeline  # Re-ingest to pick up new fields
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| BigQuery auth error | Check `GOOGLE_APPLICATION_CREDENTIALS` path |
| dbt test failures | Run `dbt debug` to verify connection |
| API 401 | Set `SOURCE_API_KEY` env var |
| Dagster home error | Set `DAGSTER_HOME` to absolute path |
| dlt pending packages | Run `dlt pipeline <name> drop-pending-packages` |
