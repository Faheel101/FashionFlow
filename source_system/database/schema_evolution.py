"""Schema evolution additions for FashionFlow.

Adds new fields to existing SQLAlchemy models to demonstrate that
dlt and dbt can handle schema changes gracefully.

Apply by importing this module AFTER the base models are loaded.
The fields are added to the existing tables via ALTER TABLE or
are automatically picked up by dlt's schema evolution.

New fields:
    - customers.loyalty_tier (bronze/silver/gold/platinum)
    - orders.shipping_priority (standard/express/overnight)
    - products.sustainability_flag (boolean)
"""

import random

from sqlalchemy import Boolean, String

from source_system.database.models import Customer, Order, Product

# ── Add columns to existing models ──────────────────────────────────────────
# These are added dynamically; SQLAlchemy will include them in new table creation.
# For existing databases, run the migration script below.

# Note: SQLAlchemy mapped_column additions require table recreation or ALTER TABLE.
# For the demo, we add them to the data generators and API schemas.

LOYALTY_TIERS = ["bronze", "silver", "gold", "platinum"]
SHIPPING_PRIORITIES = ["standard", "express", "overnight"]


def assign_loyalty_tier(customer_id: int) -> str:
    """Deterministic loyalty tier based on customer ID."""
    random.seed(customer_id)
    return random.choices(
        LOYALTY_TIERS,
        weights=[0.40, 0.30, 0.20, 0.10],
    )[0]


def assign_shipping_priority() -> str:
    """Random shipping priority."""
    return random.choices(
        SHIPPING_PRIORITIES,
        weights=[0.60, 0.30, 0.10],
    )[0]


def assign_sustainability_flag() -> bool:
    """Random sustainability flag (~20% of products)."""
    return random.random() < 0.20


def apply_schema_evolution(db_path: str = "data/fashionflow.db") -> dict[str, int]:
    """Apply schema evolution to the existing SQLite database.

    Adds new columns and populates them with realistic values.

    Returns:
        Dictionary of updated record counts per table.
    """
    from sqlalchemy import text
    from source_system.database.connection import get_engine, get_session

    engine = get_engine(db_path)
    counts: dict[str, int] = {}

    with engine.connect() as conn:
        # Add columns (SQLite supports ADD COLUMN)
        for col_sql in [
            "ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(20)",
            "ALTER TABLE orders ADD COLUMN shipping_priority VARCHAR(20)",
            "ALTER TABLE products ADD COLUMN sustainability_flag BOOLEAN",
        ]:
            try:
                conn.execute(text(col_sql))
                conn.commit()
            except Exception:
                pass  # Column already exists

    # Populate new columns
    with get_session(engine) as session:
        # Customers — loyalty tier
        customers = session.execute(text("SELECT id FROM customers")).fetchall()
        for (cid,) in customers:
            tier = assign_loyalty_tier(cid)
            session.execute(
                text("UPDATE customers SET loyalty_tier = :tier WHERE id = :id"),
                {"tier": tier, "id": cid},
            )
        counts["customers"] = len(customers)

        # Orders — shipping priority
        orders = session.execute(text("SELECT id FROM orders")).fetchall()
        random.seed(42)
        for (oid,) in orders:
            priority = assign_shipping_priority()
            session.execute(
                text("UPDATE orders SET shipping_priority = :priority WHERE id = :id"),
                {"priority": priority, "id": oid},
            )
        counts["orders"] = len(orders)

        # Products — sustainability flag
        products = session.execute(text("SELECT id FROM products")).fetchall()
        random.seed(42)
        for (pid,) in products:
            flag = assign_sustainability_flag()
            session.execute(
                text("UPDATE products SET sustainability_flag = :flag WHERE id = :id"),
                {"flag": flag, "id": pid},
            )
        counts["products"] = len(products)

    return counts


if __name__ == "__main__":
    print("Applying schema evolution...")
    counts = apply_schema_evolution()
    for table, count in counts.items():
        print(f"  {table}: {count:,} records updated")
    print("Schema evolution complete. Re-run the dlt pipeline to ingest new fields.")
