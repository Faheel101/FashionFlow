"""Validate the database schema by creating all tables and inspecting them.

Run: uv run python scripts/validate_schema.py
"""

from sqlalchemy import inspect

from source_system.database.connection import init_db, reset_engine


def validate_schema() -> None:
    """Create all tables and print validation results."""
    reset_engine()
    engine = init_db("data/fashionflow.db")
    inspector = inspect(engine)

    table_names = inspector.get_table_names()
    expected_tables = [
        "categories",
        "products",
        "customers",
        "orders",
        "order_items",
        "payments",
        "refunds",
    ]

    print("=" * 60)
    print("FashionFlow — Schema Validation")
    print("=" * 60)

    # Check all tables exist
    print(f"\nTables found: {len(table_names)}")
    for table in expected_tables:
        status = "OK" if table in table_names else "MISSING"
        columns = inspector.get_columns(table) if table in table_names else []
        fks = inspector.get_foreign_keys(table) if table in table_names else []
        print(f"  {table:15s} [{status}]  {len(columns)} columns, {len(fks)} FKs")

    # Detailed FK validation
    print(f"\n{'─' * 60}")
    print("Foreign Key Relationships")
    print(f"{'─' * 60}")
    for table in table_names:
        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            ref_table = fk["referred_table"]
            ref_cols = fk["referred_columns"]
            local_cols = fk["constrained_columns"]
            print(f"  {table}.{local_cols[0]:20s} → {ref_table}.{ref_cols[0]}")

    print(f"\n{'=' * 60}")
    print("Schema validation complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    validate_schema()
