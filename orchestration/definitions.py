"""FashionFlow — Dagster definitions.

This is the main entry point for the Dagster project.
All assets, jobs, resources, schedules, and sensors are registered here.

Asset graph:
    raw_commerce_data (dlt → BigQuery)
        └── dbt_models (dbt run + test)
"""

import dagster as dg

from orchestration.assets.ingestion import raw_commerce_data
from orchestration.assets.transformations import dbt_models

all_assets = [raw_commerce_data, dbt_models]

# Job that runs the full pipeline: ingest → transform
fashionflow_pipeline_job = dg.define_asset_job(
    name="fashionflow_pipeline",
    selection=dg.AssetSelection.all(),
    description="Full pipeline: dlt ingestion → dbt transformations",
)

defs = dg.Definitions(
    assets=all_assets,
    jobs=[fashionflow_pipeline_job],
    schedules=[],
    sensors=[],
    resources={},
)
