"""Seed the FashionFlow SQLite database with historical data.

Generates data using the historical generator, creates all tables,
performs bulk inserts, and validates integrity.

Usage::

    uv run python -m source_system.database.seed
    uv run python -m source_system.database.seed --db-path data/fashionflow.db --seed 42
"""

import argparse
import sys
import time
from pathlib import Path

from sqlalchemy import func, inspect, text

from source_system.database.connection import get_engine, get_session, init_db, reset_engine
from source_system.database.models import (
    Base,
    Category,
    Customer,
    Order,
    OrderItem,
    Payment,
    Product,
    Refund,
)
from source_system.generators.historical import generate_historical_data

# Map table names to ORM models for ordered insertion
TABLE_MODEL_MAP: list[tuple[str, type[Base]]] = [
    ("categories", Category),
    ("products", Product),
    ("customers", Customer),
    ("orders", Order),
    ("order_items", OrderItem),
    ("payments", Payment),
    ("refunds", Refund),
]

BATCH_SIZE = 5_000


def seed_database(db_path: str = "data/fashionflow.db", seed: int = 42) -> None:
    """Generate historical data and load it into SQLite.

    Args:
        db_path: Path to the SQLite database file.
        seed: Random seed for reproducible data generation.
    """
    total_start = time.time()

    # ── Step 1: Generate data ────────────────────────────────────────────
    print("=" * 60)
    print("FashionFlow — Database Seed")
    print("=" * 60)
    print(f"\nDatabase: {db_path}")
    print(f"Seed: {seed}\n")

    print("[1/4] Generating historical data...")
    gen_start = time.time()
    data = generate_historical_data(seed=seed)
    gen_elapsed = time.time() - gen_start
    print(f"      Generated in {gen_elapsed:.1f}s")

    for table_name, records in data.items():
        print(f"      {table_name:15s} {len(records):>8,} records")

    # ── Step 2: Initialize database ──────────────────────────────────────
    print("\n[2/4] Initializing database...")

    # Remove existing database for a clean seed
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
        print(f"      Removed existing database: {db_path}")

    reset_engine()
    engine = init_db(db_path)
    print("      Tables created successfully")

    # ── Step 3: Bulk insert ──────────────────────────────────────────────
    print("\n[3/4] Loading data into SQLite...")
    load_start = time.time()

    with get_session(engine) as session:
        for table_name, model_class in TABLE_MODEL_MAP:
            records = data[table_name]
            if not records:
                continue

            table_start = time.time()

            # Bulk insert in batches
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i : i + BATCH_SIZE]
                session.execute(model_class.__table__.insert(), batch)
                session.flush()

            table_elapsed = time.time() - table_start
            print(
                f"      {table_name:15s} {len(records):>8,} rows  ({table_elapsed:.1f}s)"
            )

    load_elapsed = time.time() - load_start
    print(f"      Total load time: {load_elapsed:.1f}s")

    # ── Step 4: Validate ─────────────────────────────────────────────────
    print("\n[4/4] Validating data integrity...")
    validate_database(engine, data)

    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"Seed complete in {total_elapsed:.1f}s")
    print(f"Database: {Path(db_path).resolve()}")
    print(f"{'=' * 60}")


def validate_database(engine, data: dict) -> None:  # noqa: ANN001
    """Validate row counts, PKs, and FK relationships.

    Args:
        engine: SQLAlchemy Engine.
        data: Generated data dictionary for count comparison.
    """
    errors: list[str] = []

    with get_session(engine) as session:
        # Row count validation
        print("      Row counts:")
        for table_name, model_class in TABLE_MODEL_MAP:
            expected = len(data[table_name])
            actual = session.query(func.count(model_class.id)).scalar() or 0
            status = "OK" if actual == expected else "MISMATCH"

            if actual != expected:
                errors.append(
                    f"{table_name}: expected {expected:,}, got {actual:,}"
                )

            print(
                f"        {table_name:15s} expected={expected:>8,}  "
                f"actual={actual:>8,}  [{status}]"
            )

        # FK relationship validation
        print("\n      Foreign key checks:")

        fk_checks = [
            ("products", "categories", "category_id", "id"),
            ("orders", "customers", "customer_id", "id"),
            ("order_items", "orders", "order_id", "id"),
            ("order_items", "products", "product_id", "id"),
            ("payments", "orders", "order_id", "id"),
            ("refunds", "orders", "order_id", "id"),
            ("refunds", "payments", "payment_id", "id"),
        ]

        for child_table, parent_table, fk_col, pk_col in fk_checks:
            orphan_query = text(
                f"SELECT COUNT(*) FROM {child_table} c "
                f"WHERE NOT EXISTS ("
                f"  SELECT 1 FROM {parent_table} p WHERE p.{pk_col} = c.{fk_col}"
                f")"
            )
            orphan_count = session.execute(orphan_query).scalar() or 0
            status = "OK" if orphan_count == 0 else f"ORPHANS: {orphan_count}"

            if orphan_count > 0:
                errors.append(
                    f"{child_table}.{fk_col} → {parent_table}.{pk_col}: "
                    f"{orphan_count} orphaned rows"
                )

            print(
                f"        {child_table:15s}.{fk_col:20s} → "
                f"{parent_table:15s}.{pk_col:5s} [{status}]"
            )

        # Unique constraint validation
        print("\n      Unique constraint checks:")

        unique_checks = [
            ("customers", "email"),
            ("products", "sku"),
            ("orders", "order_number"),
            ("payments", "transaction_id"),
        ]

        for table_name, col_name in unique_checks:
            dup_query = text(
                f"SELECT COUNT(*) FROM ("
                f"  SELECT {col_name} FROM {table_name} "
                f"  GROUP BY {col_name} HAVING COUNT(*) > 1"
                f")"
            )
            dup_count = session.execute(dup_query).scalar() or 0
            status = "OK" if dup_count == 0 else f"DUPLICATES: {dup_count}"

            if dup_count > 0:
                errors.append(
                    f"{table_name}.{col_name}: {dup_count} duplicate values"
                )

            print(f"        {table_name:15s}.{col_name:20s} [{status}]")

    if errors:
        print(f"\n      VALIDATION FAILED — {len(errors)} error(s):")
        for err in errors:
            print(f"        - {err}")
        sys.exit(1)
    else:
        print("\n      All validations passed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the FashionFlow database")
    parser.add_argument(
        "--db-path",
        default="data/fashionflow.db",
        help="Path to SQLite database (default: data/fashionflow.db)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()
    seed_database(db_path=args.db_path, seed=args.seed)
