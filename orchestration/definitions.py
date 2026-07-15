"""FashionFlow — Dagster definitions (multi-domain).

Asset graph:
    raw_commerce_data ──┐
    raw_marketing_data ─┤── dbt_models
    raw_inventory_data ─┘

Jobs:
    commerce_pipeline   — Commerce ingestion + dbt
    marketing_pipeline  — Marketing ingestion + dbt
    inventory_pipeline  — Inventory ingestion + dbt
    full_pipeline       — All domains
"""

import dagster as dg

from orchestration.assets.ingestion import raw_commerce_data
from orchestration.assets.domain_ingestion import raw_marketing_data, raw_inventory_data
from orchestration.assets.transformations import dbt_models

all_assets = [raw_commerce_data, raw_marketing_data, raw_inventory_data, dbt_models]

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

defs = dg.Definitions(
    assets=all_assets,
    jobs=[
        full_pipeline_job,
        commerce_pipeline_job,
        marketing_pipeline_job,
        inventory_pipeline_job,
    ],
    schedules=[],
    sensors=[],
    resources={},
)
