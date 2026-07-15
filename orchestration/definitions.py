"""FashionFlow — Dagster definitions (Sprint 3).

Features:
    - Multi-domain assets (commerce, marketing, inventory)
    - dbt transformation asset
    - Asset checks (row counts, mart validation)
    - Retry policies on all assets
    - Per-domain and full pipeline jobs
    - Backfill job for historical reprocessing
"""

import dagster as dg

from orchestration.assets.ingestion import raw_commerce_data
from orchestration.assets.domain_ingestion import raw_marketing_data, raw_inventory_data
from orchestration.assets.transformations import dbt_models
from orchestration.assets.checks import ALL_ASSET_CHECKS

# ── Retry Policy ─────────────────────────────────────────────────────────────

default_retry = dg.RetryPolicy(
    max_retries=2,
    delay=30,
    backoff=dg.Backoff.EXPONENTIAL,
    jitter=dg.Jitter.PLUS_MINUS,
)

# Apply retry to all assets
all_assets = [
    raw_commerce_data.with_retry_policy(default_retry),
    raw_marketing_data.with_retry_policy(default_retry),
    raw_inventory_data.with_retry_policy(default_retry),
    dbt_models.with_retry_policy(default_retry),
]

# ── Jobs ─────────────────────────────────────────────────────────────────────

full_pipeline_job = dg.define_asset_job(
    name="full_pipeline",
    selection=dg.AssetSelection.all(),
    description="Full pipeline: all domains → dbt",
)

commerce_pipeline_job = dg.define_asset_job(
    name="commerce_pipeline",
    selection=dg.AssetSelection.assets(raw_commerce_data, dbt_models),
    description="Commerce ingestion → dbt",
)

marketing_pipeline_job = dg.define_asset_job(
    name="marketing_pipeline",
    selection=dg.AssetSelection.assets(raw_marketing_data, dbt_models),
    description="Marketing ingestion → dbt",
)

inventory_pipeline_job = dg.define_asset_job(
    name="inventory_pipeline",
    selection=dg.AssetSelection.assets(raw_inventory_data, dbt_models),
    description="Inventory ingestion → dbt",
)

# Backfill job — same as full but named for clarity
backfill_job = dg.define_asset_job(
    name="backfill_pipeline",
    selection=dg.AssetSelection.all(),
    description="Historical backfill: reprocess all domains",
    config={
        "execution": {"config": {"multiprocess": {"max_concurrent": 1}}},
    },
)

# ── Definitions ──────────────────────────────────────────────────────────────

defs = dg.Definitions(
    assets=all_assets,
    asset_checks=ALL_ASSET_CHECKS,
    jobs=[
        full_pipeline_job,
        commerce_pipeline_job,
        marketing_pipeline_job,
        inventory_pipeline_job,
        backfill_job,
    ],
    schedules=[],
    sensors=[],
    resources={},
)
