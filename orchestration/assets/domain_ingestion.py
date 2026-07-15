"""Dagster assets for marketing and inventory ingestion."""

import os

import dagster as dg
import dlt

from ingestion.sources.marketing_api import marketing_source
from ingestion.sources.inventory_api import inventory_source


@dg.asset(
    description="Ingest marketing data (campaigns, ads, performance) into BigQuery.",
    group_name="ingestion",
    tags={"layer": "raw", "domain": "marketing"},
    kinds={"bigquery", "dlt"},
)
def raw_marketing_data(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    api_url = os.environ.get("SOURCE_API_URL", "http://127.0.0.1:8000")
    api_key = os.environ.get("SOURCE_API_KEY", "fashionflow-dev-api-key-change-me")
    dataset = os.environ.get("BQ_DATASET_RAW", "fashionflow_raw")

    context.log.info(f"Starting marketing ingestion → BigQuery.{dataset}")

    pipeline = dlt.pipeline(
        pipeline_name="fashionflow_marketing",
        destination="bigquery",
        dataset_name=dataset,
    )
    load_info = pipeline.run(marketing_source(api_url=api_url, api_key=api_key))
    context.log.info(f"Marketing pipeline completed: {load_info}")

    row_counts = {}
    with pipeline.sql_client() as client:
        for table in ["campaigns", "ad_sets", "ads", "daily_performance"]:
            try:
                result = client.execute_sql(f"SELECT COUNT(*) FROM {table}")
                row_counts[table] = result[0][0] if result else 0
            except Exception:
                row_counts[table] = 0

    return dg.MaterializeResult(
        metadata={
            "total_rows": dg.MetadataValue.int(sum(row_counts.values())),
            **{f"rows_{t}": dg.MetadataValue.int(c) for t, c in row_counts.items()},
        }
    )


@dg.asset(
    description="Ingest inventory data (snapshots, movements) into BigQuery.",
    group_name="ingestion",
    tags={"layer": "raw", "domain": "inventory"},
    kinds={"bigquery", "dlt"},
)
def raw_inventory_data(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    api_url = os.environ.get("SOURCE_API_URL", "http://127.0.0.1:8000")
    api_key = os.environ.get("SOURCE_API_KEY", "fashionflow-dev-api-key-change-me")
    dataset = os.environ.get("BQ_DATASET_RAW", "fashionflow_raw")

    context.log.info(f"Starting inventory ingestion → BigQuery.{dataset}")

    pipeline = dlt.pipeline(
        pipeline_name="fashionflow_inventory",
        destination="bigquery",
        dataset_name=dataset,
    )
    load_info = pipeline.run(inventory_source(api_url=api_url, api_key=api_key))
    context.log.info(f"Inventory pipeline completed: {load_info}")

    row_counts = {}
    with pipeline.sql_client() as client:
        for table in ["inventory_snapshots", "inventory_movements"]:
            try:
                result = client.execute_sql(f"SELECT COUNT(*) FROM {table}")
                row_counts[table] = result[0][0] if result else 0
            except Exception:
                row_counts[table] = 0

    return dg.MaterializeResult(
        metadata={
            "total_rows": dg.MetadataValue.int(sum(row_counts.values())),
            **{f"rows_{t}": dg.MetadataValue.int(c) for t, c in row_counts.items()},
        }
    )
