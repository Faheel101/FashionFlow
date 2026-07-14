"""FashionFlow dlt ingestion pipeline.

Loads commerce data from the source API into BigQuery raw layer.

Usage::

    # Full load (replace all tables)
    uv run python -m ingestion.pipeline

    # With custom API URL
    uv run python -m ingestion.pipeline --api-url http://localhost:8000
"""

import argparse
import os
import sys
import time

import dlt

from ingestion.sources.commerce_api import fashionflow_source


def run_pipeline(
    api_url: str = "http://127.0.0.1:8000",
    api_key: str | None = None,
    dataset_name: str = "fashionflow_raw",
    full_refresh: bool = False,
) -> None:
    """Run the dlt pipeline to load commerce data into BigQuery.

    Args:
        api_url: Base URL of the FashionFlow source API.
        api_key: API key for source authentication.
        dataset_name: BigQuery dataset name for raw data.
        full_refresh: If True, drop and recreate all tables.
    """
    # Resolve API key from argument or environment
    api_key = api_key or os.environ.get(
        "SOURCE_API_KEY", "fashionflow-dev-api-key-change-me"
    )

    print("=" * 60)
    print("FashionFlow — dlt Ingestion Pipeline")
    print("=" * 60)
    print(f"Source API:  {api_url}")
    print(f"Destination: BigQuery → {dataset_name}")
    print(f"Mode:        {'Full Refresh' if full_refresh else 'Replace'}")
    print()

    # Create pipeline
    pipeline = dlt.pipeline(
        pipeline_name="fashionflow_commerce",
        destination="bigquery",
        dataset_name=dataset_name,
        dev_mode=full_refresh,
    )

    # Create source
    source = fashionflow_source(
        api_url=api_url,
        api_key=api_key,
    )

    # Run pipeline
    start = time.time()
    print("Loading data...")

    load_info = pipeline.run(source)

    elapsed = time.time() - start

    # Print results
    print(f"\nPipeline completed in {elapsed:.1f}s")
    print(f"\n{load_info}")

    # Print row counts
    print("\nRow counts loaded:")
    with pipeline.sql_client() as client:
        for table in [
            "customers",
            "products",
            "orders",
            "order_items",
            "payments",
            "refunds",
        ]:
            try:
                result = client.execute_sql(f"SELECT COUNT(*) FROM {table}")
                count = result[0][0] if result else 0
                print(f"  {table:15s} {count:>8,} rows")
            except Exception:
                print(f"  {table:15s} (not found)")

    print(f"\n{'=' * 60}")
    print("Ingestion complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FashionFlow dlt pipeline")
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000",
        help="Source API URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Source API key (default: from SOURCE_API_KEY env var)",
    )
    parser.add_argument(
        "--dataset",
        default="fashionflow_raw",
        help="BigQuery dataset name (default: fashionflow_raw)",
    )
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="Drop and recreate all tables",
    )
    args = parser.parse_args()

    run_pipeline(
        api_url=args.api_url,
        api_key=args.api_key,
        dataset_name=args.dataset,
        full_refresh=args.full_refresh,
    )
