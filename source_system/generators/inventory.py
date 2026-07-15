"""Inventory data generator for FashionFlow.

Generates realistic inventory data linked to existing products:
    - Weekly inventory snapshots (~500 products × ~52 weeks ≈ ~26,000 snapshots)
    - Daily inventory movements (~50,000+ movements over 1 year)

Usage::

    from source_system.generators.inventory import generate_inventory_data
    data = generate_inventory_data(product_ids=[1, 2, ...])
"""

import random
from datetime import datetime, timedelta

WAREHOUSES = ["WH-EAST", "WH-WEST", "WH-CENTRAL"]

MOVEMENT_TYPES = [
    ("purchase", 0.25),    # Stock replenishment
    ("sale", 0.40),        # Customer purchase
    ("return", 0.10),      # Customer return
    ("damage", 0.05),      # Damaged goods written off
    ("adjustment", 0.20),  # Inventory count adjustment
]


def generate_inventory_data(
    product_ids: list[int],
    seed: int = 42,
    history_days: int = 365,
) -> dict[str, list[dict]]:
    """Generate inventory snapshots and movements.

    Args:
        product_ids: List of product IDs from the commerce schema.
        seed: Random seed for reproducibility.
        history_days: Days of historical data.

    Returns:
        Dictionary with keys: inventory_snapshots, inventory_movements.
    """
    random.seed(seed)

    end_date = datetime(2026, 7, 13)
    start_date = end_date - timedelta(days=history_days)

    snapshots: list[dict] = []
    movements: list[dict] = []

    snap_id = 1
    move_id = 1

    for product_id in product_ids:
        warehouse = random.choice(WAREHOUSES)
        unit_cost = round(random.uniform(8, 80), 2)
        initial_stock = random.randint(20, 300)
        current_stock = initial_stock

        # ── Weekly Snapshots ─────────────────────────────────────────
        current = start_date
        while current <= end_date:
            reserved = random.randint(0, min(10, max(0, current_stock)))
            available = max(0, current_stock - reserved)

            snapshots.append({
                "id": snap_id,
                "product_id": product_id,
                "snapshot_date": current.strftime("%Y-%m-%d"),
                "quantity_on_hand": max(0, current_stock),
                "quantity_reserved": reserved,
                "quantity_available": available,
                "unit_cost": unit_cost,
                "total_value": round(max(0, current_stock) * unit_cost, 2),
                "warehouse_location": warehouse,
                "created_at": current,
                "updated_at": current,
            })
            snap_id += 1

            # Simulate stock changes during the week
            weekly_movements = random.randint(2, 8)
            for _ in range(weekly_movements):
                mv_type = random.choices(
                    [m[0] for m in MOVEMENT_TYPES],
                    weights=[m[1] for m in MOVEMENT_TYPES],
                )[0]

                if mv_type == "purchase":
                    qty = random.randint(10, 100)
                    current_stock += qty
                elif mv_type == "sale":
                    qty = -min(random.randint(1, 15), max(1, current_stock))
                    current_stock += qty
                elif mv_type == "return":
                    qty = random.randint(1, 5)
                    current_stock += qty
                elif mv_type == "damage":
                    qty = -min(random.randint(1, 3), max(1, current_stock))
                    current_stock += qty
                else:  # adjustment
                    qty = random.randint(-5, 10)
                    current_stock += qty

                current_stock = max(0, current_stock)

                mv_date = current + timedelta(days=random.randint(0, 6))
                mv_date = min(mv_date, end_date)

                ref_id = None
                notes = None
                if mv_type == "sale":
                    ref_id = f"ORD-{random.randint(1, 55000):06d}"
                elif mv_type == "purchase":
                    ref_id = f"PO-{random.randint(1000, 9999)}"
                    notes = f"Replenishment order for {warehouse}"
                elif mv_type == "return":
                    ref_id = f"RET-{random.randint(1, 5000):06d}"
                elif mv_type == "damage":
                    notes = random.choice([
                        "Water damage in transit",
                        "Packaging defect",
                        "Quality control rejection",
                        "Warehouse handling damage",
                    ])

                movements.append({
                    "id": move_id,
                    "product_id": product_id,
                    "movement_type": mv_type,
                    "quantity": qty,
                    "unit_cost": unit_cost,
                    "total_cost": round(abs(qty) * unit_cost, 2),
                    "reference_id": ref_id,
                    "warehouse_location": warehouse,
                    "notes": notes,
                    "movement_date": mv_date.strftime("%Y-%m-%d"),
                    "created_at": mv_date,
                    "updated_at": mv_date,
                })
                move_id += 1

            current += timedelta(days=7)

    return {
        "inventory_snapshots": snapshots,
        "inventory_movements": movements,
    }


if __name__ == "__main__":
    # Test with sample product IDs
    product_ids = list(range(1, 501))
    print("Generating FashionFlow inventory data...")
    data = generate_inventory_data(product_ids)
    for table, records in data.items():
        print(f"  {table:25s} {len(records):>8,} records")
