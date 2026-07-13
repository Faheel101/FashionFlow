# FashionFlow — Enterprise Ecommerce Data Platform

An enterprise-grade data platform demonstrating a production-ready pipeline for a simulated fashion ecommerce business.

## Architecture

```
┌─────────────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Source System   │     │ Ingestion│     │Transformation│     │   BI /   │
│                  │────▶│          │────▶│              │────▶│ Analytics│
│ FastAPI + SQLite │     │  dltHub  │     │  dbt Core    │     │          │
└─────────────────┘     └──────────┘     └──────────────┘     └──────────┘
        │                     │                 │
        │                     ▼                 │
        │               ┌──────────┐            │
        │               │ BigQuery │◀───────────┘
        │               │  (DWH)   │
        │               └──────────┘
        │                     ▲
        └─────────────────────┘
                    Dagster (Orchestration)
```

**Pipeline flow:** FastAPI → dltHub → BigQuery → dbt Core → Dagster

## Tech Stack

| Layer           | Technology            |
| --------------- | --------------------- |
| Source System    | FastAPI, SQLAlchemy, SQLite |
| Data Generation  | Faker                 |
| Ingestion       | dltHub                |
| Warehouse       | Google BigQuery       |
| Transformation  | dbt Core              |
| Orchestration   | Dagster               |
| Configuration   | Pydantic Settings     |
| Logging         | structlog             |
| Testing         | pytest                |
| Linting         | Ruff                  |
| Package Manager | uv                    |

## Project Structure

```
fashionflow/
├── config.py                  # Pydantic settings (loads .env)
├── logger.py                  # Structured logging (structlog)
├── source_system/             # Simulated ecommerce backend
│   ├── api/                   # FastAPI application
│   │   ├── main.py
│   │   ├── routes/            # Endpoint routers
│   │   ├── dependencies.py
│   │   └── schemas.py
│   ├── database/              # SQLAlchemy models + connection
│   │   ├── models.py
│   │   ├── connection.py
│   │   └── seed.py
│   └── generators/            # Data generation scripts
│       ├── historical.py
│       └── continuous.py
├── ingestion/                 # dltHub pipelines
│   ├── pipeline.py
│   ├── sources/
│   │   └── commerce_api.py
│   └── config.py
├── transformations/           # dbt Core project
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/           # Source-conformed models
│       └── marts/             # Business-layer fact/dim tables
├── orchestration/             # Dagster project
│   ├── definitions.py
│   ├── assets/
│   ├── jobs/
│   ├── resources/
│   ├── schedules/
│   └── sensors/
├── scripts/                   # Utility scripts
├── tests/                     # pytest test suite
├── docs/                      # Documentation
├── pyproject.toml             # Project config + dependencies
├── .env.example               # Environment variable template
└── .gitignore
```

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud account with BigQuery enabled
- GCP service account key (JSON)

## Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/fashionflow.git
cd fashionflow

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your GCP project ID, credentials path, etc.

# Verify the environment
uv run python -c "from config import get_settings; print('Config OK')"
```

## Usage

```bash
# 1. Generate historical data and seed the database
uv run python -m source_system.database.seed

# 2. Start the source API
uv run uvicorn source_system.api.main:app --reload

# 3. Run the dlt ingestion pipeline
uv run python -m ingestion.pipeline

# 4. Run dbt transformations
cd transformations && uv run dbt run && cd ..

# 5. Launch Dagster UI (orchestrates the full pipeline)
uv run dagster dev
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=source_system --cov=ingestion

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy .
```

## BigQuery Datasets

| Dataset              | Purpose                                  |
| -------------------- | ---------------------------------------- |
| `fashionflow_raw`    | Raw data loaded by dlt (source of truth) |
| `fashionflow_staging`| Cleaned, renamed, typed staging models   |
| `fashionflow_mart`   | Business-layer fact and dimension tables  |

## License

MIT
