"""Continuous order generator for FashionFlow.

Simulates near-real-time ecommerce activity by periodically inserting
new records into the SQLite database:
    - New customer signups
    - New orders with line items
    - Payment processing
    - Order status transitions
    - Refund requests

Designed to run as a background process alongside the FastAPI server,
providing a stream of fresh data for the ingestion pipeline to pick up.

Usage::

    uv run python -m source_system.generators.continuous
    uv run python -m source_system.generators.continuous --interval 10 --batch-size 3
"""

import argparse
import random
import signal
import sys
import time
import uuid
from datetime import datetime

from faker import Faker
from sqlalchemy import func

from source_system.database.connection import get_engine, get_session
from source_system.database.models import (
    Customer,
    Order,
    OrderItem,
    Payment,
    Product,
    Refund,
)
from source_system.generators.catalog import (
    DISCOUNT_CHANCE,
    DISCOUNT_RANGE,
    ORDER_STATUS_WEIGHTS,
    PAYMENT_METHODS,
    REFUND_REASONS,
    SHIPPING_RATES,
    TAX_RATE,
)

fake = Faker()

# Graceful shutdown
_running = True


def _signal_handler(signum: int, frame) -> None:  # noqa: ANN001
    """Handle shutdown signals gracefully."""
    global _running
    print("\n[SHUTDOWN] Stopping continuous generator...")
    _running = False


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


class ContinuousGenerator:
    """Generate ongoing ecommerce activity against the live database.

    Args:
        db_path: Path to the SQLite database.
        batch_size: Number of new orders per cycle.
        new_customer_chance: Probability of creating a new customer per order.
        status_update_count: Number of existing orders to advance per cycle.
        refund_chance: Probability of generating a refund per cycle.
    """

    def __init__(
        self,
        db_path: str = "data/fashionflow.db",
        batch_size: int = 3,
        new_customer_chance: float = 0.3,
        status_update_count: int = 5,
        refund_chance: float = 0.15,
    ) -> None:
        self.db_path = db_path
        self.batch_size = batch_size
        self.new_customer_chance = new_customer_chance
        self.status_update_count = status_update_count
        self.refund_chance = refund_chance

        self.engine = get_engine(db_path)
        self.cycle_count = 0

    def run_cycle(self) -> dict[str, int]:
        """Execute one cycle of data generation.

        Returns:
            Dictionary of counts for each action taken.
        """
        self.cycle_count += 1
        now = datetime.now()
        stats: dict[str, int] = {
            "new_customers": 0,
            "new_orders": 0,
            "new_items": 0,
            "new_payments": 0,
            "status_updates": 0,
            "new_refunds": 0,
        }

        with get_session(self.engine) as session:
            # Load active products for order generation
            active_products = (
                session.query(Product)
                .filter(Product.is_active == True)  # noqa: E712
                .all()
            )
            if not active_products:
                print("[WARN] No active products found. Skipping cycle.")
                return stats

            # ── New Customers ────────────────────────────────────────
            for _ in range(self.batch_size):
                if random.random() < self.new_customer_chance:
                    customer = self._create_customer(session, now)
                    session.flush()
                    stats["new_customers"] += 1

            # ── New Orders ───────────────────────────────────────────
            customer_ids = [
                row[0]
                for row in session.query(Customer.id)
                .filter(Customer.is_active == True)  # noqa: E712
                .all()
            ]

            for _ in range(self.batch_size):
                customer_id = random.choice(customer_ids)
                order, items, payment = self._create_order(
                    session, customer_id, active_products, now
                )
                session.flush()
                stats["new_orders"] += 1
                stats["new_items"] += len(items)
                stats["new_payments"] += 1

            # ── Status Updates ───────────────────────────────────────
            updated = self._update_order_statuses(session, now)
            stats["status_updates"] = updated

            # ── Refunds ──────────────────────────────────────────────
            if random.random() < self.refund_chance:
                refund_count = self._create_refunds(session, now)
                stats["new_refunds"] = refund_count

        return stats

    def _create_customer(self, session, now: datetime) -> Customer:  # noqa: ANN001
        """Insert a new customer."""
        customer = Customer(
            email=fake.unique.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone=fake.phone_number()[:20] if random.random() > 0.2 else None,
            date_of_birth=(
                fake.date_of_birth(minimum_age=18, maximum_age=70).isoformat()
                if random.random() > 0.3
                else None
            ),
            gender=random.choices(
                ["Female", "Male", "Non-binary", "Prefer not to say"],
                weights=[0.48, 0.45, 0.04, 0.03],
            )[0],
            address_line1=fake.street_address(),
            address_line2=fake.secondary_address() if random.random() > 0.7 else None,
            city=fake.city(),
            state=fake.state_abbr(),
            postal_code=fake.zipcode(),
            country="US",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        session.add(customer)
        return customer

    def _create_order(
        self,
        session,  # noqa: ANN001
        customer_id: int,
        active_products: list[Product],
        now: datetime,
    ) -> tuple[Order, list[OrderItem], Payment]:
        """Create a complete order with items and payment."""
        # Get next order ID
        max_order_id = session.query(func.max(Order.id)).scalar() or 0
        order_id = max_order_id + 1

        order_number = f"FF-{now.strftime('%Y%m%d')}-{order_id:06d}"

        # Pick products
        num_items = random.choices([1, 2, 3, 4], weights=[0.35, 0.35, 0.20, 0.10])[0]
        selected = random.sample(active_products, min(num_items, len(active_products)))

        # Build items
        subtotal = 0.0
        items: list[OrderItem] = []
        for product in selected:
            quantity = random.choices([1, 2, 3], weights=[0.75, 0.20, 0.05])[0]
            item_discount = 0.0
            if random.random() < 0.10:
                item_discount = round(
                    product.price * quantity * random.uniform(0.05, 0.20), 2
                )
            total_price = round(product.price * quantity - item_discount, 2)
            subtotal += total_price

            item = OrderItem(
                order_id=order_id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
                discount_amount=item_discount,
                total_price=total_price,
                created_at=now,
                updated_at=now,
            )
            items.append(item)

        # Order-level calculations
        discount_amount = 0.0
        if random.random() < DISCOUNT_CHANCE:
            discount_amount = round(subtotal * random.uniform(*DISCOUNT_RANGE), 2)

        tax_amount = round((subtotal - discount_amount) * TAX_RATE, 2)
        shipping_amount = random.choices(
            [s[0] for s in SHIPPING_RATES],
            weights=[s[1] for s in SHIPPING_RATES],
        )[0]
        total_amount = round(subtotal - discount_amount + tax_amount + shipping_amount, 2)

        # New orders start as pending
        order = Order(
            id=order_id,
            order_number=order_number,
            customer_id=customer_id,
            status="pending",
            subtotal=round(subtotal, 2),
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            total_amount=total_amount,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        session.add(order)
        for item in items:
            session.add(item)

        # Payment
        payment_method = random.choices(
            [p[0] for p in PAYMENT_METHODS],
            weights=[p[1] for p in PAYMENT_METHODS],
        )[0]

        payment = Payment(
            order_id=order_id,
            payment_method=payment_method,
            payment_status="pending",
            amount=total_amount,
            transaction_id=f"txn_{uuid.uuid4().hex[:16]}",
            created_at=now,
            updated_at=now,
        )
        session.add(payment)

        return order, items, payment

    def _update_order_statuses(self, session, now: datetime) -> int:  # noqa: ANN001
        """Advance existing orders through their status lifecycle."""
        status_transitions: dict[str, list[tuple[str, float]]] = {
            "pending": [("confirmed", 0.7), ("cancelled", 0.1)],
            "confirmed": [("processing", 0.8)],
            "processing": [("shipped", 0.7)],
            "shipped": [("delivered", 0.6)],
            "delivered": [("returned", 0.02)],
        }

        updated = 0

        for current_status, transitions in status_transitions.items():
            orders = (
                session.query(Order)
                .filter(Order.status == current_status)
                .order_by(Order.updated_at)
                .limit(self.status_update_count)
                .all()
            )

            for order in orders:
                for next_status, prob in transitions:
                    if random.random() < prob:
                        order.status = next_status
                        order.updated_at = now

                        # Update payment status for cancellations
                        if next_status == "cancelled":
                            payment = (
                                session.query(Payment)
                                .filter(Payment.order_id == order.id)
                                .first()
                            )
                            if payment:
                                payment.payment_status = "failed"
                                payment.updated_at = now

                        # Mark payment as completed for confirmed orders
                        elif next_status == "confirmed":
                            payment = (
                                session.query(Payment)
                                .filter(Payment.order_id == order.id)
                                .first()
                            )
                            if payment and payment.payment_status == "pending":
                                payment.payment_status = "completed"
                                payment.updated_at = now

                        updated += 1
                        break

        return updated

    def _create_refunds(self, session, now: datetime) -> int:  # noqa: ANN001
        """Create refunds for recently delivered orders."""
        delivered_orders = (
            session.query(Order)
            .filter(Order.status == "delivered")
            .order_by(func.random())
            .limit(3)
            .all()
        )

        count = 0
        for order in delivered_orders:
            if random.random() > 0.5:
                continue

            # Check if already refunded
            existing = (
                session.query(Refund)
                .filter(Refund.order_id == order.id)
                .first()
            )
            if existing:
                continue

            payment = (
                session.query(Payment)
                .filter(Payment.order_id == order.id)
                .first()
            )
            if not payment:
                continue

            reason = random.choices(
                [r[0] for r in REFUND_REASONS],
                weights=[r[1] for r in REFUND_REASONS],
            )[0]

            refund = Refund(
                order_id=order.id,
                payment_id=payment.id,
                order_item_id=None,
                reason=reason,
                status="pending",
                amount=order.total_amount,
                notes=f"Customer reported: {reason.replace('_', ' ')}",
                created_at=now,
                updated_at=now,
            )
            session.add(refund)

            order.status = "returned"
            order.updated_at = now
            payment.payment_status = "refunded"
            payment.updated_at = now

            count += 1

        return count


def run_continuous(
    db_path: str = "data/fashionflow.db",
    interval: int = 15,
    batch_size: int = 3,
) -> None:
    """Run the continuous generator in a loop.

    Args:
        db_path: Path to the SQLite database.
        interval: Seconds between each generation cycle.
        batch_size: Number of new orders per cycle.
    """
    generator = ContinuousGenerator(db_path=db_path, batch_size=batch_size)

    print("=" * 60)
    print("FashionFlow — Continuous Order Generator")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Interval: {interval}s")
    print(f"Batch size: {batch_size} orders/cycle")
    print(f"Press Ctrl+C to stop\n")

    while _running:
        cycle_start = time.time()
        stats = generator.run_cycle()
        elapsed = time.time() - cycle_start

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(
            f"[{timestamp}] Cycle {generator.cycle_count:>4d} ({elapsed:.1f}s) | "
            f"Customers: +{stats['new_customers']} | "
            f"Orders: +{stats['new_orders']} | "
            f"Items: +{stats['new_items']} | "
            f"Payments: +{stats['new_payments']} | "
            f"Status updates: {stats['status_updates']} | "
            f"Refunds: +{stats['new_refunds']}"
        )

        # Sleep in small increments for responsive shutdown
        sleep_end = time.time() + interval
        while _running and time.time() < sleep_end:
            time.sleep(0.5)

    print("\n[DONE] Continuous generator stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Continuously generate ecommerce activity"
    )
    parser.add_argument(
        "--db-path",
        default="data/fashionflow.db",
        help="Path to SQLite database (default: data/fashionflow.db)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Seconds between cycles (default: 15)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="New orders per cycle (default: 3)",
    )
    args = parser.parse_args()
    run_continuous(
        db_path=args.db_path,
        interval=args.interval,
        batch_size=args.batch_size,
    )
