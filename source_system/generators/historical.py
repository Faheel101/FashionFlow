"""Historical ecommerce data generator for FashionFlow.

Generates realistic historical data for a fashion ecommerce business:
    - ~30 categories (hierarchical)
    - ~500 products
    - ~10,000 customers
    - ~50,000 orders over 2 years with seasonal patterns
    - ~120,000 order items
    - ~50,000 payments
    - ~3,500 refunds

Usage::

    from source_system.generators.historical import HistoricalDataGenerator

    generator = HistoricalDataGenerator(seed=42)
    data = generator.generate()
"""

import random
import uuid
from datetime import datetime, timedelta

from faker import Faker

from source_system.generators.catalog import (
    BRANDS,
    CATEGORY_TREE,
    COLORS,
    DISCOUNT_CHANCE,
    DISCOUNT_RANGE,
    MATERIALS,
    MONTHLY_ORDER_WEIGHTS,
    ORDER_STATUS_WEIGHTS,
    PAYMENT_METHODS,
    PRICE_RANGES,
    PRODUCT_STYLES,
    REFUND_REASONS,
    SHIPPING_RATES,
    SIZES,
    TAX_RATE,
)

# Type alias for generated data
GeneratedData = dict[str, list[dict]]


class HistoricalDataGenerator:
    """Generate realistic historical ecommerce data.

    Args:
        seed: Random seed for reproducible output.
        num_customers: Number of customers to generate.
        num_products: Number of products to generate.
        num_orders: Approximate number of orders to generate.
        history_days: Number of days of historical data.
    """

    def __init__(
        self,
        seed: int = 42,
        num_customers: int = 10_000,
        num_products: int = 500,
        num_orders: int = 50_000,
        history_days: int = 730,  # 2 years
    ) -> None:
        self.seed = seed
        self.num_customers = num_customers
        self.num_products = num_products
        self.num_orders = num_orders
        self.history_days = history_days

        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

        self.end_date = datetime(2026, 7, 13, 23, 59, 59)
        self.start_date = self.end_date - timedelta(days=history_days)

        # Internal state
        self._categories: list[dict] = []
        self._category_id_map: dict[str, int] = {}
        self._leaf_category_ids: list[int] = []
        self._products: list[dict] = []
        self._customers: list[dict] = []
        self._orders: list[dict] = []
        self._order_items: list[dict] = []
        self._payments: list[dict] = []
        self._refunds: list[dict] = []

    def generate(self) -> GeneratedData:
        """Generate all data and return as a dictionary of record lists."""
        self._generate_categories()
        self._generate_products()
        self._generate_customers()
        self._generate_orders()

        return {
            "categories": self._categories,
            "products": self._products,
            "customers": self._customers,
            "orders": self._orders,
            "order_items": self._order_items,
            "payments": self._payments,
            "refunds": self._refunds,
        }

    # ── Categories ───────────────────────────────────────────────────────

    def _generate_categories(self) -> None:
        """Build hierarchical category tree."""
        cat_id = 1

        for parent_name, parent_desc, children in CATEGORY_TREE:
            parent_created = self._random_date(
                self.start_date - timedelta(days=90),
                self.start_date,
            )
            self._categories.append({
                "id": cat_id,
                "name": parent_name,
                "description": parent_desc,
                "parent_category_id": None,
                "is_active": True,
                "created_at": parent_created,
                "updated_at": parent_created,
            })
            parent_id = cat_id
            cat_id += 1

            for child_name, child_desc in children:
                child_created = self._random_date(
                    parent_created,
                    parent_created + timedelta(days=7),
                )
                full_name = f"{parent_name} > {child_name}"
                self._categories.append({
                    "id": cat_id,
                    "name": child_name,
                    "description": child_desc,
                    "parent_category_id": parent_id,
                    "is_active": True,
                    "created_at": child_created,
                    "updated_at": child_created,
                })
                self._category_id_map[child_name] = cat_id
                self._leaf_category_ids.append(cat_id)
                cat_id += 1

    # ── Products ─────────────────────────────────────────────────────────

    def _generate_products(self) -> None:
        """Generate product catalog across all leaf categories."""
        all_brands = (
            BRANDS["premium"] + BRANDS["mid_range"] + BRANDS["budget"]
        )
        product_id = 1
        sku_counter = 1000

        # Distribute products roughly evenly across leaf categories
        products_per_cat = max(1, self.num_products // len(self._leaf_category_ids))

        for cat_id in self._leaf_category_ids:
            cat = next(c for c in self._categories if c["id"] == cat_id)
            cat_name = cat["name"]
            parent = next(c for c in self._categories if c["id"] == cat["parent_category_id"])
            parent_name = parent["name"]

            styles = PRODUCT_STYLES.get(cat_name, ["Classic"])
            price_min, price_max = PRICE_RANGES.get(cat_name, (29.99, 149.99))

            # Determine size/material type
            if parent_name == "Shoes":
                size_type = "shoes"
                mat_type = "shoes"
            elif parent_name == "Accessories":
                size_type = "accessories"
                mat_type = "accessories"
            else:
                size_type = "clothing"
                mat_type = "clothing"

            count = products_per_cat + random.randint(-3, 3)
            count = max(1, count)

            for _ in range(count):
                if product_id > self.num_products:
                    break

                brand_tier = random.choices(
                    ["premium", "mid_range", "budget"],
                    weights=[0.2, 0.5, 0.3],
                )[0]
                brand = random.choice(BRANDS[brand_tier])

                style = random.choice(styles)
                color = random.choice(COLORS)
                material = random.choice(MATERIALS[mat_type])
                size = random.choice(SIZES[size_type])

                # Premium brands get higher prices
                tier_multiplier = {
                    "premium": 1.6,
                    "mid_range": 1.0,
                    "budget": 0.7,
                }[brand_tier]

                base_price = round(
                    random.uniform(price_min, price_max) * tier_multiplier, 2
                )
                cost_price = round(base_price * random.uniform(0.30, 0.55), 2)

                sku = f"FF-{cat_name[:3].upper()}-{sku_counter:05d}"
                sku_counter += 1

                product_name = f"{color} {style}"

                created_at = self._random_date(
                    self.start_date - timedelta(days=30),
                    self.start_date + timedelta(days=self.history_days // 2),
                )

                self._products.append({
                    "id": product_id,
                    "sku": sku,
                    "name": product_name,
                    "description": f"{brand} {product_name}. Made from {material.lower()}. "
                    f"Available in {color.lower()}.",
                    "category_id": cat_id,
                    "brand": brand,
                    "price": base_price,
                    "cost_price": cost_price,
                    "size": size,
                    "color": color,
                    "material": material,
                    "stock_quantity": random.randint(0, 200),
                    "is_active": random.random() > 0.05,  # 5% discontinued
                    "created_at": created_at,
                    "updated_at": created_at,
                })
                product_id += 1

            if product_id > self.num_products:
                break

    # ── Customers ────────────────────────────────────────────────────────

    def _generate_customers(self) -> None:
        """Generate customer profiles spread over the history window."""
        used_emails: set[str] = set()

        for i in range(1, self.num_customers + 1):
            # Customers join gradually — more in recent months
            days_ago = int(
                self.history_days * (1 - random.betavariate(2, 5))
            )
            created_at = self.start_date + timedelta(
                days=days_ago,
                hours=random.randint(6, 23),
                minutes=random.randint(0, 59),
            )
            created_at = min(created_at, self.end_date)

            # Ensure unique email
            while True:
                email = self.fake.email()
                if email not in used_emails:
                    used_emails.add(email)
                    break

            gender = random.choices(
                ["Female", "Male", "Non-binary", "Prefer not to say"],
                weights=[0.48, 0.45, 0.04, 0.03],
            )[0]

            self._customers.append({
                "id": i,
                "email": email,
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "phone": self.fake.phone_number()[:20] if random.random() > 0.2 else None,
                "date_of_birth": (
                    self.fake.date_of_birth(minimum_age=18, maximum_age=70).isoformat()
                    if random.random() > 0.3
                    else None
                ),
                "gender": gender,
                "address_line1": self.fake.street_address(),
                "address_line2": self.fake.secondary_address() if random.random() > 0.7 else None,
                "city": self.fake.city(),
                "state": self.fake.state_abbr(),
                "postal_code": self.fake.zipcode(),
                "country": "US",
                "is_active": random.random() > 0.03,  # 3% churned
                "created_at": created_at,
                "updated_at": created_at + timedelta(
                    days=random.randint(0, 30),
                ),
            })

    # ── Orders, Items, Payments, Refunds ─────────────────────────────────

    def _generate_orders(self) -> None:
        """Generate orders with items, payments, and refunds."""
        order_id = 1
        item_id = 1
        payment_id = 1
        refund_id = 1

        # Pre-compute daily order targets with seasonal weighting
        daily_targets = self._compute_daily_order_targets()

        # Build customer lookup sorted by created_at for realistic ordering
        sorted_customers = sorted(self._customers, key=lambda c: c["created_at"])
        active_products = [p for p in self._products if p["is_active"]]

        for day_offset, target_count in enumerate(daily_targets):
            current_date = self.start_date + timedelta(days=day_offset)

            # Only customers who existed by this date can order
            eligible_customers = [
                c for c in sorted_customers if c["created_at"] <= current_date
            ]
            if not eligible_customers:
                continue

            for _ in range(target_count):
                customer = random.choice(eligible_customers)

                # Order timestamp — random time during the day
                order_time = current_date.replace(
                    hour=random.randint(6, 23),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )

                order_number = f"FF-{order_time.strftime('%Y%m%d')}-{order_id:06d}"

                # Determine final status
                final_status = random.choices(
                    list(ORDER_STATUS_WEIGHTS.keys()),
                    weights=list(ORDER_STATUS_WEIGHTS.values()),
                )[0]

                # Generate items
                num_items = random.choices(
                    [1, 2, 3, 4, 5],
                    weights=[0.30, 0.35, 0.20, 0.10, 0.05],
                )[0]
                order_products = random.sample(
                    active_products, min(num_items, len(active_products))
                )

                subtotal = 0.0
                order_items_batch: list[dict] = []

                for product in order_products:
                    quantity = random.choices(
                        [1, 2, 3],
                        weights=[0.75, 0.20, 0.05],
                    )[0]
                    unit_price = product["price"]

                    # Per-item discount
                    item_discount = 0.0
                    if random.random() < 0.10:  # 10% of items on sale
                        item_discount = round(
                            unit_price * quantity * random.uniform(0.05, 0.20), 2
                        )

                    total_price = round(unit_price * quantity - item_discount, 2)
                    subtotal += total_price

                    order_items_batch.append({
                        "id": item_id,
                        "order_id": order_id,
                        "product_id": product["id"],
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "discount_amount": item_discount,
                        "total_price": total_price,
                        "created_at": order_time,
                        "updated_at": order_time,
                    })
                    item_id += 1

                # Order-level discount
                discount_amount = 0.0
                if random.random() < DISCOUNT_CHANCE:
                    pct = random.uniform(*DISCOUNT_RANGE)
                    discount_amount = round(subtotal * pct, 2)

                tax_amount = round((subtotal - discount_amount) * TAX_RATE, 2)

                shipping_amount = random.choices(
                    [s[0] for s in SHIPPING_RATES],
                    weights=[s[1] for s in SHIPPING_RATES],
                )[0]

                total_amount = round(
                    subtotal - discount_amount + tax_amount + shipping_amount, 2
                )

                # Status timestamps
                updated_at = self._compute_order_updated_at(
                    order_time, final_status
                )

                order = {
                    "id": order_id,
                    "order_number": order_number,
                    "customer_id": customer["id"],
                    "status": final_status,
                    "subtotal": round(subtotal, 2),
                    "discount_amount": discount_amount,
                    "tax_amount": tax_amount,
                    "shipping_amount": shipping_amount,
                    "total_amount": total_amount,
                    "shipping_address_line1": customer["address_line1"],
                    "shipping_address_line2": customer["address_line2"],
                    "shipping_city": customer["city"],
                    "shipping_state": customer["state"],
                    "shipping_postal_code": customer["postal_code"],
                    "shipping_country": customer["country"],
                    "notes": self._maybe_order_note(),
                    "created_at": order_time,
                    "updated_at": updated_at,
                }

                self._orders.append(order)
                self._order_items.extend(order_items_batch)

                # Payment
                payment_method = random.choices(
                    [p[0] for p in PAYMENT_METHODS],
                    weights=[p[1] for p in PAYMENT_METHODS],
                )[0]

                if final_status == "cancelled":
                    payment_status = random.choice(["failed", "completed"])
                elif final_status == "returned":
                    payment_status = "refunded"
                else:
                    payment_status = "completed" if final_status != "pending" else "pending"

                payment_time = order_time + timedelta(minutes=random.randint(1, 10))

                self._payments.append({
                    "id": payment_id,
                    "order_id": order_id,
                    "payment_method": payment_method,
                    "payment_status": payment_status,
                    "amount": total_amount,
                    "transaction_id": f"txn_{uuid.uuid4().hex[:16]}",
                    "created_at": payment_time,
                    "updated_at": updated_at,
                })

                # Refund — for returned/delivered orders with issues
                if final_status == "returned" or (
                    final_status == "delivered" and random.random() < 0.06
                ):
                    reason = random.choices(
                        [r[0] for r in REFUND_REASONS],
                        weights=[r[1] for r in REFUND_REASONS],
                    )[0]

                    # Full or partial refund
                    if random.random() < 0.7:
                        refund_amount = total_amount  # Full refund
                        refund_item_id = None
                    else:
                        # Partial — refund a single item
                        refund_item = random.choice(order_items_batch)
                        refund_amount = refund_item["total_price"]
                        refund_item_id = refund_item["id"]

                    refund_status = random.choices(
                        ["processed", "approved", "pending", "rejected"],
                        weights=[0.70, 0.15, 0.10, 0.05],
                    )[0]

                    refund_time = updated_at + timedelta(
                        days=random.randint(1, 14),
                        hours=random.randint(0, 12),
                    )
                    refund_time = min(refund_time, self.end_date)

                    self._refunds.append({
                        "id": refund_id,
                        "order_id": order_id,
                        "payment_id": payment_id,
                        "order_item_id": refund_item_id,
                        "reason": reason,
                        "status": refund_status,
                        "amount": round(refund_amount, 2),
                        "notes": f"Customer reported: {reason.replace('_', ' ')}"
                        if random.random() > 0.4
                        else None,
                        "created_at": refund_time,
                        "updated_at": refund_time + timedelta(
                            days=random.randint(0, 5)
                        ),
                    })
                    refund_id += 1

                payment_id += 1
                order_id += 1

    # ── Helpers ──────────────────────────────────────────────────────────

    def _compute_daily_order_targets(self) -> list[int]:
        """Compute target order count per day with seasonal weighting."""
        base_daily = self.num_orders / self.history_days
        targets: list[int] = []

        for day_offset in range(self.history_days):
            current_date = self.start_date + timedelta(days=day_offset)
            month_weight = MONTHLY_ORDER_WEIGHTS[current_date.month - 1]

            # Weekday boost (more orders on weekdays)
            weekday = current_date.weekday()
            day_weight = 1.1 if weekday < 5 else 0.85

            # Growth trend — 30% more orders at end vs start
            growth = 1.0 + 0.30 * (day_offset / self.history_days)

            daily = base_daily * month_weight * day_weight * growth
            # Add randomness
            daily *= random.uniform(0.8, 1.2)

            targets.append(max(1, int(round(daily))))

        return targets

    def _compute_order_updated_at(
        self, created_at: datetime, status: str
    ) -> datetime:
        """Compute realistic updated_at based on final status."""
        days_map: dict[str, tuple[int, int]] = {
            "pending": (0, 0),
            "confirmed": (0, 1),
            "processing": (1, 3),
            "shipped": (2, 5),
            "delivered": (3, 10),
            "cancelled": (0, 2),
            "returned": (7, 21),
        }
        min_d, max_d = days_map.get(status, (0, 1))
        delta = timedelta(
            days=random.randint(min_d, max_d),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        updated = created_at + delta
        return min(updated, self.end_date)

    def _maybe_order_note(self) -> str | None:
        """Occasionally generate an order note."""
        if random.random() > 0.08:
            return None
        notes = [
            "Please leave at front door",
            "Gift — please do not include receipt",
            "Fragile items, handle with care",
            "Deliver after 5 PM",
            "Call before delivery",
            "Use side entrance",
            "Birthday gift — gift wrap if possible",
            "Rush order",
        ]
        return random.choice(notes)

    def _random_date(self, start: datetime, end: datetime) -> datetime:
        """Generate a random datetime between start and end."""
        delta = end - start
        seconds = int(delta.total_seconds())
        if seconds <= 0:
            return start
        random_seconds = random.randint(0, seconds)
        return start + timedelta(seconds=random_seconds)


def generate_historical_data(seed: int = 42) -> GeneratedData:
    """Convenience function to generate all historical data.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        Dictionary with keys: categories, products, customers,
        orders, order_items, payments, refunds.
    """
    generator = HistoricalDataGenerator(seed=seed)
    return generator.generate()


if __name__ == "__main__":
    import time

    print("Generating FashionFlow historical data...")
    start = time.time()
    data = generate_historical_data()
    elapsed = time.time() - start

    print(f"\nGenerated in {elapsed:.1f}s:")
    for table, records in data.items():
        print(f"  {table:15s} {len(records):>8,} records")
