"""Tests for database integrity and data quality."""

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from source_system.database.connection import get_session
from source_system.database.models import (
    Category,
    Customer,
    Order,
    OrderItem,
    Payment,
    Product,
    Refund,
)


class TestRowCounts:
    """Verify expected record counts in the test database."""

    def test_categories_exist(self, seeded_engine):
        with get_session(seeded_engine) as session:
            count = session.query(func.count(Category.id)).scalar()
            assert count > 0

    def test_products_exist(self, seeded_engine):
        with get_session(seeded_engine) as session:
            count = session.query(func.count(Product.id)).scalar()
            assert count > 0

    def test_customers_exist(self, seeded_engine):
        with get_session(seeded_engine) as session:
            count = session.query(func.count(Customer.id)).scalar()
            assert count > 0

    def test_orders_exist(self, seeded_engine):
        with get_session(seeded_engine) as session:
            count = session.query(func.count(Order.id)).scalar()
            assert count > 0

    def test_order_items_exist(self, seeded_engine):
        with get_session(seeded_engine) as session:
            count = session.query(func.count(OrderItem.id)).scalar()
            assert count > 0

    def test_payments_exist(self, seeded_engine):
        with get_session(seeded_engine) as session:
            count = session.query(func.count(Payment.id)).scalar()
            assert count > 0


class TestForeignKeys:
    """Verify no orphaned foreign key references."""

    FK_CHECKS = [
        ("products", "categories", "category_id", "id"),
        ("orders", "customers", "customer_id", "id"),
        ("order_items", "orders", "order_id", "id"),
        ("order_items", "products", "product_id", "id"),
        ("payments", "orders", "order_id", "id"),
        ("refunds", "orders", "order_id", "id"),
        ("refunds", "payments", "payment_id", "id"),
    ]

    def test_no_orphaned_records(self, seeded_engine):
        """All FK references should point to existing parent records."""
        with get_session(seeded_engine) as session:
            for child, parent, fk_col, pk_col in self.FK_CHECKS:
                query = text(
                    f"SELECT COUNT(*) FROM {child} c "
                    f"WHERE NOT EXISTS ("
                    f"  SELECT 1 FROM {parent} p WHERE p.{pk_col} = c.{fk_col}"
                    f")"
                )
                orphans = session.execute(query).scalar()
                assert orphans == 0, (
                    f"Found {orphans} orphaned rows: "
                    f"{child}.{fk_col} → {parent}.{pk_col}"
                )


class TestUniqueConstraints:
    """Verify unique fields have no duplicates."""

    def test_unique_customer_emails(self, seeded_engine):
        with get_session(seeded_engine) as session:
            total = session.query(func.count(Customer.id)).scalar()
            unique = session.query(func.count(func.distinct(Customer.email))).scalar()
            assert total == unique

    def test_unique_product_skus(self, seeded_engine):
        with get_session(seeded_engine) as session:
            total = session.query(func.count(Product.id)).scalar()
            unique = session.query(func.count(func.distinct(Product.sku))).scalar()
            assert total == unique

    def test_unique_order_numbers(self, seeded_engine):
        with get_session(seeded_engine) as session:
            total = session.query(func.count(Order.id)).scalar()
            unique = session.query(
                func.count(func.distinct(Order.order_number))
            ).scalar()
            assert total == unique

    def test_unique_transaction_ids(self, seeded_engine):
        with get_session(seeded_engine) as session:
            total = session.query(func.count(Payment.id)).scalar()
            unique = session.query(
                func.count(func.distinct(Payment.transaction_id))
            ).scalar()
            assert total == unique


class TestDataQuality:
    """Verify data values make business sense."""

    def test_order_totals_positive(self, seeded_engine):
        """Order totals should be positive."""
        with get_session(seeded_engine) as session:
            negative = (
                session.query(func.count(Order.id))
                .filter(Order.total_amount < 0)
                .scalar()
            )
            assert negative == 0

    def test_product_prices_positive(self, seeded_engine):
        """Product prices should be positive."""
        with get_session(seeded_engine) as session:
            invalid = (
                session.query(func.count(Product.id))
                .filter(Product.price <= 0)
                .scalar()
            )
            assert invalid == 0

    def test_cost_price_less_than_retail(self, seeded_engine):
        """Cost price should be less than retail price."""
        with get_session(seeded_engine) as session:
            invalid = (
                session.query(func.count(Product.id))
                .filter(Product.cost_price >= Product.price)
                .scalar()
            )
            assert invalid == 0

    def test_order_statuses_valid(self, seeded_engine):
        """All order statuses should be recognized values."""
        valid_statuses = {
            "pending", "confirmed", "processing",
            "shipped", "delivered", "cancelled", "returned",
        }
        with get_session(seeded_engine) as session:
            statuses = session.query(func.distinct(Order.status)).all()
            for (s,) in statuses:
                assert s in valid_statuses, f"Unexpected status: {s}"

    def test_payment_statuses_valid(self, seeded_engine):
        """All payment statuses should be recognized values."""
        valid = {"pending", "completed", "failed", "refunded"}
        with get_session(seeded_engine) as session:
            statuses = session.query(func.distinct(Payment.payment_status)).all()
            for (s,) in statuses:
                assert s in valid, f"Unexpected payment status: {s}"

    def test_every_order_has_payment(self, seeded_engine):
        """Every order should have at least one payment."""
        with get_session(seeded_engine) as session:
            orders_without_payment = session.execute(
                text(
                    "SELECT COUNT(*) FROM orders o "
                    "WHERE NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.id)"
                )
            ).scalar()
            assert orders_without_payment == 0

    def test_every_order_has_items(self, seeded_engine):
        """Every order should have at least one line item."""
        with get_session(seeded_engine) as session:
            orders_without_items = session.execute(
                text(
                    "SELECT COUNT(*) FROM orders o "
                    "WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.id)"
                )
            ).scalar()
            assert orders_without_items == 0
