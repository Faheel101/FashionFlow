"""Seed the FashionFlow SQLite database with all domain data.

Generates and loads: commerce, marketing, and inventory data.

Usage::

    uv run python -m source_system.database.seed
"""

import argparse
import sys
import time
from pathlib import Path

from sqlalchemy import func, text

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
from source_system.database.marketing_models import (
    Ad,
    AdSet,
    Campaign,
    DailyPerformance,
)
from source_system.database.inventory_models import (
    InventoryMovement,
    InventorySnapshot,
)
from source_system.generators.historical import generate_historical_data
from source_system.generators.marketing import generate_marketing_data
from source_system.generators.inventory import generate_inventory_data

BATCH_SIZE = 5_000

# Ordered insertion: (data_key, model_class)
COMMERCE_TABLES: list[tuple[str, type]] = [
    ("categories", Category),
    ("products", Product),
    ("customers", Customer),
    ("orders", Order),
    ("order_items", OrderItem),
    ("payments", Payment),
    ("refunds", Refund),
]

MARKETING_TABLES: list[tuple[str, type]] = [
    ("campaigns", Campaign),
    ("ad_sets", AdSet),
    ("ads", Ad),
    ("daily_performance", DailyPerformance),
]

INVENTORY_TABLES: list[tuple[str, type]] = [
    ("inventory_snapshots", InventorySnapshot),
    ("inventory_movements", InventoryMovement),
]


def seed_database(db_path: str = "data/fashionflow.db", seed: int = 42) -> None:
    """Generate all domain data and load into SQLite."""
    total_start = time.time()

    print("=" * 60)
    print("FashionFlow — Database Seed (All Domains)")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Seed: {seed}\n")

    # ── Step 1: Generate data ────────────────────────────────────────
    print("[1/5] Generating commerce data...")
    gen_start = time.time()
    commerce_data = generate_historical_data(seed=seed)
    print(f"      Done in {time.time() - gen_start:.1f}s")
    for name, records in commerce_data.items():
        print(f"      {name:20s} {len(records):>8,} records")

    print("\n[2/5] Generating marketing data...")
    gen_start = time.time()
    marketing_data = generate_marketing_data(seed=seed)
    print(f"      Done in {time.time() - gen_start:.1f}s")
    for name, records in marketing_data.items():
        print(f"      {name:20s} {len(records):>8,} records")

    print("\n[3/5] Generating inventory data...")
    gen_start = time.time()
    product_ids = [p["id"] for p in commerce_data["products"]]
    inventory_data = generate_inventory_data(product_ids=product_ids, seed=seed)
    print(f"      Done in {time.time() - gen_start:.1f}s")
    for name, records in inventory_data.items():
        print(f"      {name:25s} {len(records):>8,} records")

    # ── Step 3: Initialize database ──────────────────────────────────
    print("\n[4/5] Initializing database...")
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
        print(f"      Removed existing database: {db_path}")

    reset_engine()
    engine = init_db(db_path)
    print("      Tables created successfully")

    # ── Step 4: Bulk insert ──────────────────────────────────────────
    print("\n[5/5] Loading all data into SQLite...")
    load_start = time.time()

    all_tables = [
        ("Commerce", COMMERCE_TABLES, commerce_data),
        ("Marketing", MARKETING_TABLES, marketing_data),
        ("Inventory", INVENTORY_TABLES, inventory_data),
    ]

    with get_session(engine) as session:
        for domain_name, table_list, data in all_tables:
            print(f"\n      {domain_name}:")
            for table_name, model_class in table_list:
                records = data[table_name]
                if not records:
                    continue
                t = time.time()
                for i in range(0, len(records), BATCH_SIZE):
                    batch = records[i : i + BATCH_SIZE]
                    session.execute(model_class.__table__.insert(), batch)
                    session.flush()
                elapsed = time.time() - t
                print(f"        {table_name:25s} {len(records):>8,} rows  ({elapsed:.1f}s)")

    load_elapsed = time.time() - load_start
    print(f"\n      Total load time: {load_elapsed:.1f}s")

    # ── Summary ──────────────────────────────────────────────────────
    total_records = (
        sum(len(r) for r in commerce_data.values())
        + sum(len(r) for r in marketing_data.values())
        + sum(len(r) for r in inventory_data.values())
    )
    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"Seed complete in {total_elapsed:.1f}s — {total_records:,} total records")
    print(f"Database: {Path(db_path).resolve()}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the FashionFlow database")
    parser.add_argument("--db-path", default="data/fashionflow.db")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    seed_database(db_path=args.db_path, seed=args.seed)
