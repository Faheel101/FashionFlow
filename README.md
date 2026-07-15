# FashionFlow — Enterprise Ecommerce Data Platform

A production-grade data platform demonstrating end-to-end data engineering for a simulated fashion ecommerce business with multi-domain pipelines, incremental loading, warehouse modeling, orchestration, and operational tooling.

## Architecture

```
                           FastAPI Source Systems
        ┌───────────────────────────┼───────────────────────────┐
   Commerce (7 tables)       Marketing (4 tables)       Inventory (2 tables)
        └───────────────────────────┼───────────────────────────┘
                                    │
                         dltHub (incremental merge)
                                    │
                         BigQuery Raw Layer (13 tables)
                                    │
                    dbt Core (12 staging views → 2 fact tables)
                         + snapshots + reconciliation
                                    │
                    Dagster (5 jobs, asset checks, retries)
                                    │
                    Audit Logging + Quarantine + Backfill
```

**Pipeline:** `FastAPI → dltHub → BigQuery → dbt Core → Dagster`

## What This Demonstrates

- **Multi-domain REST API ingestion** with authentication, pagination, filtering, and incremental loading
- **Incremental data loading** using dltHub merge with `updated_at` cursors and lookback windows
- **BigQuery data warehouse** design with raw → staging → mart layers
- **dbt transformations** including staging models, fact tables, Type 2 SCD snapshots, and reconciliation models
- **Dagster orchestration** with asset dependencies, per-domain jobs, retry policies, asset checks, and backfill support
- **Data quality** framework with reusable checks, business-specific dbt tests, and quarantine handling
- **Audit logging** for pipeline observability
- **Schema evolution** handling (new fields without breaking pipelines)
- **127+ automated tests** (pytest + dbt)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Source System | FastAPI, SQLAlchemy, SQLite, Faker |
| Ingestion | dltHub (incremental merge) |
| Warehouse | Google BigQuery |
| Transformation | dbt Core |
| Orchestration | Dagster |
| Data Quality | Custom framework + dbt tests |
| Configuration | Pydantic Settings |
| Logging | structlog |
| Testing | pytest (60+ tests) + dbt (100+ tests) |
| Package Manager | uv |
| Linting | Ruff |

## Data Scale

| Domain | Tables | Records | Fact Models |
|--------|--------|---------|-------------|
| Commerce | 7 | ~248K | fct_orders |
| Marketing | 4 | ~28K | fct_daily_marketing_performance |
| Inventory | 2 | ~159K | — |
| **Total** | **13** | **~435K** | **2** |

## Project Structure

```
fashionflow/
├── source_system/           # Simulated ecommerce backend
│   ├── api/                 # FastAPI (commerce + marketing + inventory endpoints)
│   ├── database/            # SQLAlchemy models (3 domains + schema evolution)
│   └── generators/          # Faker data generators (historical + continuous)
├── ingestion/               # dltHub pipelines
│   ├── sources/             # API sources (commerce, marketing, inventory)
│   ├── pipeline.py          # Multi-domain pipeline runner
│   ├── quality.py           # Data quality framework
│   ├── audit.py             # Pipeline audit logging
│   └── quarantine.py        # Invalid record quarantine
├── transformations/         # dbt Core project
│   ├── models/
│   │   ├── staging/         # 12 staging views (commerce + marketing + inventory)
│   │   └── marts/           # 2 fact tables + 3 reconciliation models
│   ├── snapshots/           # Type 2 SCD product snapshot
│   └── tests/               # Business-specific singular tests
├── orchestration/           # Dagster project
│   ├── assets/              # Ingestion + transformation + check assets
│   └── definitions.py       # 5 jobs, retry policies, asset checks
├── scripts/                 # Validation and utility scripts
├── tests/                   # pytest suite (60+ tests)
├── docs/                    # Technical documentation
├── config.py                # Pydantic Settings
└── logger.py                # structlog configuration
```

## Quick Start

```bash
# Prerequisites: Python 3.12+, uv, GCP account with BigQuery

git clone https://github.com/Faheel101/FashionFlow.git
cd FashionFlow

uv sync --extra dev
cp .env.example .env
# Edit .env with your GCP project ID and credentials path

# Seed the database
uv run python -m source_system.database.seed

# Start the API (Terminal 1)
uv run uvicorn source_system.api.main:app

# Run all pipelines (Terminal 2)
uv run python -m ingestion.pipeline

# Run dbt
uv run dbt run --project-dir transformations --profiles-dir transformations
uv run dbt test --project-dir transformations --profiles-dir transformations

# Or use Dagster to orchestrate everything
uv run dagster dev
```

## BigQuery Datasets

| Dataset | Purpose |
|---------|---------|
| `fashionflow_raw` | Source-conformed data (dlt merge) |
| `fashionflow_staging` | Cleaned, typed staging views |
| `fashionflow_mart` | Business-layer fact tables + reconciliation |
| `fashionflow_snapshots` | Historical product SCD Type 2 |
| `fashionflow_audit` | Pipeline execution metadata |
| `fashionflow_quarantine` | Invalid records for investigation |

## Testing

```bash
uv run pytest                    # 60+ unit/integration tests
uv run dbt test                  # 100+ data quality tests
uv run python scripts/validate_e2e.py  # End-to-end validation
```

## Future Roadmap

- [ ] Dimensional modeling (dim_customers, dim_products)
- [ ] dbt incremental models for large fact tables
- [ ] Dagster schedules and sensors
- [ ] Alerting (Slack/email on pipeline failures)
- [ ] CI/CD with GitHub Actions
- [ ] Dashboard layer (Hex/Looker)

## License

MIT
