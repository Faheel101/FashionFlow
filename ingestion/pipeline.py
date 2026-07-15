"""FashionFlow dlt ingestion pipeline — multi-domain.

Supports: commerce, marketing, inventory.

Usage::

    uv run python -m ingestion.pipeline                    # All domains
    uv run python -m ingestion.pipeline --domain commerce   # Commerce only
    uv run python -m ingestion.pipeline --domain marketing  # Marketing only
    uv run python -m ingestion.pipeline --domain inventory  # Inventory only
"""

import argparse
import os
import time

import dlt

from ingestion.sources.commerce_api import fashionflow_source
from ingestion.sources.marketing_api import marketing_source
from ingestion.sources.inventory_api import inventory_source

DOMAIN_CONFIG = {
    "commerce": {
        "source_fn": fashionflow_source,
        "pipeline_name": "fashionflow_commerce",
        "dataset": "fashionflow_raw",
        "tables": ["customers", "products", "orders", "order_items", "payments", "refunds"],
    },
    "marketing": {
        "source_fn": marketing_source,
        "pipeline_name": "fashionflow_marketing",
        "dataset": "fashionflow_raw",
        "tables": ["campaigns", "ad_sets", "ads", "daily_performance"],
    },
    "inventory": {
        "source_fn": inventory_source,
        "pipeline_name": "fashionflow_inventory",
        "dataset": "fashionflow_raw",
        "tables": ["inventory_snapshots", "inventory_movements"],
    },
}


def run_domain_pipeline(
    domain: str,
    api_url: str = "http://127.0.0.1:8000",
    api_key: str | None = None,
) -> None:
    """Run the pipeline for a single domain."""
    config = DOMAIN_CONFIG[domain]
    api_key = api_key or os.environ.get("SOURCE_API_KEY", "fashionflow-dev-api-key-change-me")

    print(f"\n  [{domain.upper()}] {config['pipeline_name']} → {config['dataset']}")

    pipeline = dlt.pipeline(
        pipeline_name=config["pipeline_name"],
        destination="bigquery",
        dataset_name=config["dataset"],
    )

    source = config["source_fn"](api_url=api_url, api_key=api_key)
    start = time.time()
    load_info = pipeline.run(source)
    elapsed = time.time() - start

    print(f"  Completed in {elapsed:.1f}s")

    # Row counts
    with pipeline.sql_client() as client:
        for table in config["tables"]:
            try:
                result = client.execute_sql(f"SELECT COUNT(*) FROM {table}")
                count = result[0][0] if result else 0
                print(f"    {table:25s} {count:>8,} rows")
            except Exception:
                print(f"    {table:25s} (not found)")


def run_pipeline(
    domains: list[str] | None = None,
    api_url: str = "http://127.0.0.1:8000",
    api_key: str | None = None,
) -> None:
    """Run pipelines for specified domains (default: all)."""
    domains = domains or list(DOMAIN_CONFIG.keys())

    print("=" * 60)
    print("FashionFlow — dlt Ingestion Pipeline (Multi-Domain)")
    print("=" * 60)
    print(f"Source API:  {api_url}")
    print(f"Domains:     {', '.join(domains)}")

    total_start = time.time()

    for domain in domains:
        if domain not in DOMAIN_CONFIG:
            print(f"\n  [SKIP] Unknown domain: {domain}")
            continue
        run_domain_pipeline(domain, api_url, api_key)

    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"All pipelines completed in {total_elapsed:.1f}s")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FashionFlow dlt pipelines")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--domain", default=None, help="Run specific domain (commerce/marketing/inventory)")
    args = parser.parse_args()

    domains = [args.domain] if args.domain else None
    run_pipeline(domains=domains, api_url=args.api_url, api_key=args.api_key)
