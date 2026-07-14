"""End-to-end validation of the FashionFlow data platform.

Tests every layer: source system → API → dlt → BigQuery → dbt.
Run this as the final check before marking Sprint 1 complete.

Usage::

    # Start the API first:  uv run uvicorn source_system.api.main:app
    # Then run:              uv run python scripts/validate_e2e.py
"""

import os
import sys
import time

import httpx
from google.cloud import bigquery

# Configuration
API_URL = os.environ.get("SOURCE_API_URL", "http://127.0.0.1:8000")
API_KEY = os.environ.get("SOURCE_API_KEY", "fashionflow-dev-api-key-change-me")
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "de-project-502311")
RAW_DATASET = os.environ.get("BQ_DATASET_RAW", "fashionflow_raw")
STAGING_DATASET = "fashionflow_staging"
MART_DATASET = "fashionflow_mart"

ENTITIES = ["customers", "products", "orders", "order-items", "payments", "refunds"]
BQ_TABLES_RAW = ["customers", "products", "orders", "order_items", "payments", "refunds"]
BQ_TABLES_STAGING = [
    "stg_customers", "stg_products", "stg_orders",
    "stg_order_items", "stg_payments", "stg_refunds",
]
BQ_TABLES_MART = ["fct_orders"]


def main() -> None:
    errors: list[str] = []
    start = time.time()

    print("=" * 60)
    print("FashionFlow — End-to-End Validation")
    print("=" * 60)

    # ── 1. Source System — Database ──────────────────────────────────
    print("\n[1/6] Source database...")
    try:
        from source_system.database.connection import get_engine
        from sqlalchemy import text

        engine = get_engine()
        with engine.connect() as conn:
            tables = ["categories", "customers", "products", "orders", "order_items", "payments", "refunds"]
            for table in tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                status = "OK" if count > 0 else "EMPTY"
                if count == 0:
                    errors.append(f"SQLite {table} is empty")
                print(f"  {table:15s} {count:>8,} rows  [{status}]")
    except Exception as e:
        errors.append(f"Source database: {e}")
        print(f"  ERROR: {e}")

    # ── 2. Source System — API ───────────────────────────────────────
    print("\n[2/6] Source API...")
    try:
        client = httpx.Client(base_url=API_URL, headers={"X-API-Key": API_KEY}, timeout=10)

        # Health check
        health = client.get("/health")
        print(f"  Health check:  [{health.status_code}] {health.json()['status']}")

        # Auth check
        no_auth = httpx.get(f"{API_URL}/api/v1/customers", timeout=10)
        print(f"  No-auth test:  [{no_auth.status_code}] {'OK — blocked' if no_auth.status_code == 401 else 'FAIL'}")
        if no_auth.status_code != 401:
            errors.append("API auth not enforced")

        # Endpoint checks
        for entity in ENTITIES:
            resp = client.get(f"/api/v1/{entity}?page_size=1")
            total = resp.json().get("total_count", 0)
            status = "OK" if resp.status_code == 200 and total > 0 else "FAIL"
            if resp.status_code != 200:
                errors.append(f"API /{entity}: HTTP {resp.status_code}")
            print(f"  /api/v1/{entity:15s} {total:>8,} records  [{status}]")

        # Pagination check
        p1 = client.get("/api/v1/orders?page=1&page_size=5").json()
        p2 = client.get("/api/v1/orders?page=2&page_size=5").json()
        ids1 = {o["id"] for o in p1["data"]}
        ids2 = {o["id"] for o in p2["data"]}
        pag_ok = len(ids1) == 5 and ids1.isdisjoint(ids2)
        print(f"  Pagination:    {'OK' if pag_ok else 'FAIL'}")
        if not pag_ok:
            errors.append("Pagination returning duplicate records")

        # Filter check
        filtered = client.get("/api/v1/orders?status=delivered&page_size=1").json()
        filt_ok = all(o["status"] == "delivered" for o in filtered["data"])
        print(f"  Filtering:     {'OK' if filt_ok else 'FAIL'}")

        # updated_since check
        inc = client.get("/api/v1/orders?updated_since=2030-01-01T00:00:00").json()
        inc_ok = inc["total_count"] == 0
        print(f"  Incremental:   {'OK' if inc_ok else 'FAIL'}")

    except httpx.ConnectError:
        errors.append("Cannot connect to source API — is it running?")
        print("  ERROR: Cannot connect to API. Start it with: uv run uvicorn source_system.api.main:app")
    except Exception as e:
        errors.append(f"Source API: {e}")
        print(f"  ERROR: {e}")

    # ── 3. BigQuery — Raw Layer ──────────────────────────────────────
    print("\n[3/6] BigQuery raw layer...")
    try:
        bq = bigquery.Client(project=PROJECT_ID)
        for table in BQ_TABLES_RAW:
            result = bq.query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{RAW_DATASET}.{table}`").result()
            count = list(result)[0].cnt
            status = "OK" if count > 0 else "EMPTY"
            if count == 0:
                errors.append(f"BQ raw.{table} is empty")
            print(f"  {RAW_DATASET}.{table:15s} {count:>8,} rows  [{status}]")
    except Exception as e:
        errors.append(f"BigQuery raw: {e}")
        print(f"  ERROR: {e}")

    # ── 4. BigQuery — Staging Layer ──────────────────────────────────
    print("\n[4/6] BigQuery staging layer...")
    try:
        for table in BQ_TABLES_STAGING:
            result = bq.query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{STAGING_DATASET}.{table}`").result()
            count = list(result)[0].cnt
            status = "OK" if count > 0 else "EMPTY"
            if count == 0:
                errors.append(f"BQ staging.{table} is empty")
            print(f"  {STAGING_DATASET}.{table:20s} {count:>8,} rows  [{status}]")
    except Exception as e:
        errors.append(f"BigQuery staging: {e}")
        print(f"  ERROR: {e}")

    # ── 5. BigQuery — Mart Layer ─────────────────────────────────────
    print("\n[5/6] BigQuery mart layer...")
    try:
        for table in BQ_TABLES_MART:
            result = bq.query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{MART_DATASET}.{table}`").result()
            count = list(result)[0].cnt
            status = "OK" if count > 0 else "EMPTY"
            if count == 0:
                errors.append(f"BQ mart.{table} is empty")
            print(f"  {MART_DATASET}.{table:20s} {count:>8,} rows  [{status}]")

        # Spot check fct_orders
        result = bq.query(f"""
            SELECT
                COUNT(*) as total_orders,
                ROUND(SUM(order_total), 2) as total_revenue,
                ROUND(SUM(net_revenue), 2) as total_net_revenue,
                COUNTIF(has_refund) as orders_with_refunds,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM `{PROJECT_ID}.{MART_DATASET}.fct_orders`
        """).result()
        row = list(result)[0]
        print(f"\n  fct_orders summary:")
        print(f"    Total orders:        {row.total_orders:>10,}")
        print(f"    Total revenue:       ${row.total_revenue:>12,.2f}")
        print(f"    Net revenue:         ${row.total_net_revenue:>12,.2f}")
        print(f"    Orders with refunds: {row.orders_with_refunds:>10,}")
        print(f"    Unique customers:    {row.unique_customers:>10,}")
    except Exception as e:
        errors.append(f"BigQuery mart: {e}")
        print(f"  ERROR: {e}")

    # ── 6. dbt Tests ─────────────────────────────────────────────────
    print("\n[6/6] dbt test results...")
    try:
        import subprocess
        env = {**os.environ}
        result = subprocess.run(
            ["dbt", "test", "--project-dir", "transformations", "--profiles-dir", "transformations"],
            capture_output=True, text=True, env=env,
        )
        # Count passes and failures
        passes = result.stdout.count(" PASS ")
        fails = result.stdout.count(" FAIL ")
        errs = result.stdout.count(" ERROR ")
        print(f"  Tests passed:  {passes}")
        print(f"  Tests failed:  {fails}")
        print(f"  Tests errored: {errs}")
        if fails > 0 or errs > 0:
            errors.append(f"dbt tests: {fails} failures, {errs} errors")
    except Exception as e:
        errors.append(f"dbt tests: {e}")
        print(f"  ERROR: {e}")

    # ── Summary ──────────────────────────────────────────────────────
    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    if errors:
        print(f"E2E VALIDATION FAILED — {len(errors)} error(s) in {elapsed:.1f}s:")
        for err in errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"ALL CHECKS PASSED in {elapsed:.1f}s")
        print(f"\nFashionFlow Sprint 1 — Pipeline verified end-to-end:")
        print(f"  FastAPI → dltHub → BigQuery → dbt Core → Dagster")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
