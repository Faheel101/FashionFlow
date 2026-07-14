"""Dagster asset for dlt ingestion — loads source API data into BigQuery."""

import os

import dagster as dg
import dlt

from ingestion.sources.commerce_api import fashionflow_source


@dg.asset(
    description="Ingest commerce data from the source API into BigQuery raw layer using dlt.",
    group_name="ingestion",
    tags={"layer": "raw"},
    kinds={"bigquery", "dlt"},
)
def raw_commerce_data(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Run the dlt pipeline to load commerce data into BigQuery."""
    api_url = os.environ.get("SOURCE_API_URL", "http://127.0.0.1:8000")
    api_key = os.environ.get("SOURCE_API_KEY", "fashionflow-dev-api-key-change-me")
    dataset_name = os.environ.get("BQ_DATASET_RAW", "fashionflow_raw")

    context.log.info(f"Starting dlt ingestion: {api_url} → BigQuery.{dataset_name}")

    pipeline = dlt.pipeline(
        pipeline_name="fashionflow_commerce",
        destination="bigquery",
        dataset_name=dataset_name,
    )

    source = fashionflow_source(api_url=api_url, api_key=api_key)
    load_info = pipeline.run(source)

    context.log.info(f"Pipeline completed: {load_info}")

    # Collect row counts for metadata
    row_counts = {}
    tables = ["customers", "products", "orders", "order_items", "payments", "refunds"]
    with pipeline.sql_client() as client:
        for table in tables:
            try:
                result = client.execute_sql(f"SELECT COUNT(*) FROM {table}")
                row_counts[table] = result[0][0] if result else 0
            except Exception:
                row_counts[table] = 0

    total_rows = sum(row_counts.values())
    context.log.info(f"Total rows loaded: {total_rows:,}")

    return dg.MaterializeResult(
        metadata={
            "total_rows": dg.MetadataValue.int(total_rows),
            **{
                f"rows_{table}": dg.MetadataValue.int(count)
                for table, count in row_counts.items()
            },
        }
    )
