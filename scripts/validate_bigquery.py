"""Validate the FashionFlow raw layer in BigQuery.

Checks record counts, schema correctness, null rates, data consistency,
and cross-table referential integrity in the raw dataset.

Usage::

    uv run python scripts/validate_bigquery.py
"""

import os
import sys

from google.cloud import bigquery

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "de-project-502311")
DATASET = os.environ.get("BQ_DATASET_RAW", "fashionflow_raw")

EXPECTED_TABLES = [
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "refunds",
]

# Columns that should never be null
NOT_NULL_COLUMNS: dict[str, list[str]] = {
    "customers": ["id", "email", "first_name", "last_name", "country", "created_at", "updated_at"],
    "products": ["id", "sku", "name", "category_id", "brand", "price", "cost_price", "created_at", "updated_at"],
    "orders": ["id", "order_number", "customer_id", "status", "total_amount", "created_at", "updated_at"],
    "order_items": ["id", "order_id", "product_id", "quantity", "unit_price", "total_price", "created_at", "updated_at"],
    "payments": ["id", "order_id", "payment_method", "payment_status", "amount", "transaction_id", "created_at", "updated_at"],
    "refunds": ["id", "order_id", "payment_id", "reason", "status", "amount", "created_at", "updated_at"],
}

# Cross-table FK checks: (child_table, child_col, parent_table, parent_col)
FK_CHECKS = [
    ("orders", "customer_id", "customers", "id"),
    ("order_items", "order_id", "orders", "id"),
    ("order_items", "product_id", "products", "id"),
    ("payments", "order_id", "orders", "id"),
    ("refunds", "order_id", "orders", "id"),
    ("refunds", "payment_id", "payments", "id"),
]


def validate() -> None:
    """Run all validation checks against BigQuery raw tables."""
    client = bigquery.Client(project=PROJECT_ID)
    errors: list[str] = []
    full_dataset = f"{PROJECT_ID}.{DATASET}"

    print("=" * 60)
    print("FashionFlow — BigQuery Raw Layer Validation")
    print("=" * 60)
    print(f"Project:  {PROJECT_ID}")
    print(f"Dataset:  {DATASET}")

    # ── 1. Table Existence & Row Counts ──────────────────────────────
    print("\n[1/5] Table existence & row counts:")

    table_counts: dict[str, int] = {}
    for table in EXPECTED_TABLES:
        try:
            result = client.query(
                f"SELECT COUNT(*) as cnt FROM `{full_dataset}.{table}`"
            ).result()
            count = list(result)[0].cnt
            table_counts[table] = count
            status = "OK" if count > 0 else "EMPTY"
            if count == 0:
                errors.append(f"{table}: table is empty")
            print(f"  {table:15s} {count:>8,} rows  [{status}]")
        except Exception as e:
            table_counts[table] = 0
            errors.append(f"{table}: {e}")
            print(f"  {table:15s} {'MISSING':>8s}       [ERROR]")

    # ── 2. Schema Validation ─────────────────────────────────────────
    print("\n[2/5] Schema validation:")

    for table in EXPECTED_TABLES:
        try:
            bq_table = client.get_table(f"{full_dataset}.{table}")
            col_names = [f.name for f in bq_table.schema]
            # Check that dlt metadata columns exist
            has_load_id = "_dlt_load_id" in col_names
            has_dlt_id = "_dlt_id" in col_names
            col_count = len([c for c in col_names if not c.startswith("_dlt")])
            print(
                f"  {table:15s} {col_count:>3d} columns  "
                f"dlt_metadata={'OK' if has_load_id and has_dlt_id else 'MISSING'}"
            )
            if not has_load_id or not has_dlt_id:
                errors.append(f"{table}: missing dlt metadata columns")
        except Exception as e:
            print(f"  {table:15s} [ERROR: {e}]")

    # ── 3. Null Checks ───────────────────────────────────────────────
    print("\n[3/5] Not-null column checks:")

    for table, columns in NOT_NULL_COLUMNS.items():
        if table_counts.get(table, 0) == 0:
            continue

        null_checks = ", ".join(
            f"COUNTIF({col} IS NULL) as null_{col}" for col in columns
        )
        query = f"SELECT {null_checks} FROM `{full_dataset}.{table}`"

        try:
            result = list(client.query(query).result())[0]
            table_ok = True
            for col in columns:
                null_count = getattr(result, f"null_{col}")
                if null_count > 0:
                    table_ok = False
                    errors.append(f"{table}.{col}: {null_count:,} null values")
            status = "OK" if table_ok else "NULLS FOUND"
            print(f"  {table:15s} [{status}]")
        except Exception as e:
            print(f"  {table:15s} [ERROR: {e}]")

    # ── 4. Referential Integrity ─────────────────────────────────────
    print("\n[4/5] Cross-table referential integrity:")

    for child, child_col, parent, parent_col in FK_CHECKS:
        if table_counts.get(child, 0) == 0:
            continue

        query = f"""
            SELECT COUNT(*) as orphans
            FROM `{full_dataset}.{child}` c
            WHERE NOT EXISTS (
                SELECT 1 FROM `{full_dataset}.{parent}` p
                WHERE p.{parent_col} = c.{child_col}
            )
        """
        try:
            result = list(client.query(query).result())[0]
            orphans = result.orphans
            status = "OK" if orphans == 0 else f"ORPHANS: {orphans:,}"
            if orphans > 0:
                errors.append(
                    f"{child}.{child_col} → {parent}.{parent_col}: "
                    f"{orphans:,} orphaned rows"
                )
            print(
                f"  {child:15s}.{child_col:15s} → "
                f"{parent:15s}.{parent_col:5s} [{status}]"
            )
        except Exception as e:
            print(f"  {child}.{child_col} → {parent}.{parent_col} [ERROR: {e}]")

    # ── 5. Data Quality Spot Checks ──────────────────────────────────
    print("\n[5/5] Data quality spot checks:")

    quality_checks = [
        (
            "Orders: positive totals",
            f"SELECT COUNTIF(total_amount < 0) as bad FROM `{full_dataset}.orders`",
        ),
        (
            "Products: price > cost",
            f"SELECT COUNTIF(cost_price >= price) as bad FROM `{full_dataset}.products`",
        ),
        (
            "Products: positive prices",
            f"SELECT COUNTIF(price <= 0) as bad FROM `{full_dataset}.products`",
        ),
        (
            "Orders: valid statuses",
            f"SELECT COUNTIF(status NOT IN ('pending','confirmed','processing','shipped','delivered','cancelled','returned')) as bad FROM `{full_dataset}.orders`",
        ),
        (
            "Payments: valid statuses",
            f"SELECT COUNTIF(payment_status NOT IN ('pending','completed','failed','refunded')) as bad FROM `{full_dataset}.payments`",
        ),
        (
            "Every order has items",
            f"SELECT COUNT(*) as bad FROM `{full_dataset}.orders` o WHERE NOT EXISTS (SELECT 1 FROM `{full_dataset}.order_items` i WHERE i.order_id = o.id)",
        ),
        (
            "Every order has payment",
            f"SELECT COUNT(*) as bad FROM `{full_dataset}.orders` o WHERE NOT EXISTS (SELECT 1 FROM `{full_dataset}.payments` p WHERE p.order_id = o.id)",
        ),
    ]

    for check_name, query in quality_checks:
        try:
            result = list(client.query(query).result())[0]
            bad_count = result.bad
            status = "OK" if bad_count == 0 else f"FAILED: {bad_count:,}"
            if bad_count > 0:
                errors.append(f"{check_name}: {bad_count:,} invalid records")
            print(f"  {check_name:35s} [{status}]")
        except Exception as e:
            print(f"  {check_name:35s} [ERROR: {e}]")

    # ── Summary ──────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        total_rows = sum(table_counts.values())
        print(f"All validations passed! ({total_rows:,} total rows across {len(EXPECTED_TABLES)} tables)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    validate()
