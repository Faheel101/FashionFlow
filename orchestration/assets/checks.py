"""Dagster asset checks for data quality and freshness."""

import os

import dagster as dg
from google.cloud import bigquery


def _bq_client() -> bigquery.Client:
    return bigquery.Client(project=os.environ.get("GCP_PROJECT_ID", "de-project-502311"))


def _get_row_count(table: str, dataset: str = "fashionflow_raw") -> int:
    project = os.environ.get("GCP_PROJECT_ID", "de-project-502311")
    client = _bq_client()
    result = list(client.query(f"SELECT COUNT(*) FROM `{project}.{dataset}.{table}`").result())
    return result[0][0] if result else 0


@dg.asset_check(asset="raw_commerce_data", description="Commerce raw tables have rows")
def check_commerce_row_counts() -> dg.AssetCheckResult:
    tables = ["customers", "products", "orders", "order_items", "payments", "refunds"]
    empty = [t for t in tables if _get_row_count(t) == 0]
    passed = len(empty) == 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={"empty_tables": dg.MetadataValue.text(", ".join(empty) if empty else "none")},
    )


@dg.asset_check(asset="raw_marketing_data", description="Marketing raw tables have rows")
def check_marketing_row_counts() -> dg.AssetCheckResult:
    tables = ["campaigns", "ad_sets", "ads", "daily_performance"]
    empty = [t for t in tables if _get_row_count(t) == 0]
    return dg.AssetCheckResult(
        passed=len(empty) == 0,
        metadata={"empty_tables": dg.MetadataValue.text(", ".join(empty) if empty else "none")},
    )


@dg.asset_check(asset="raw_inventory_data", description="Inventory raw tables have rows")
def check_inventory_row_counts() -> dg.AssetCheckResult:
    tables = ["inventory_snapshots", "inventory_movements"]
    empty = [t for t in tables if _get_row_count(t) == 0]
    return dg.AssetCheckResult(
        passed=len(empty) == 0,
        metadata={"empty_tables": dg.MetadataValue.text(", ".join(empty) if empty else "none")},
    )


@dg.asset_check(asset="dbt_models", description="dbt mart tables are populated")
def check_mart_tables() -> dg.AssetCheckResult:
    tables = {"fct_orders": "fashionflow_mart", "fct_daily_marketing_performance": "fashionflow_mart"}
    empty = [t for t, ds in tables.items() if _get_row_count(t, ds) == 0]
    return dg.AssetCheckResult(
        passed=len(empty) == 0,
        metadata={"empty_tables": dg.MetadataValue.text(", ".join(empty) if empty else "none")},
    )


ALL_ASSET_CHECKS = [
    check_commerce_row_counts,
    check_marketing_row_counts,
    check_inventory_row_counts,
    check_mart_tables,
]
