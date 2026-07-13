"""SQLAlchemy ORM models for the FashionFlow ecommerce source system.

Tables:
    - categories: Product categories with hierarchical support
    - products: Fashion products with pricing and inventory
    - customers: Customer profiles with addresses
    - orders: Purchase orders with status tracking
    - order_items: Individual line items within orders
    - payments: Payment transactions linked to orders
    - refunds: Refund records linked to orders and payments
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Category(Base):
    """Product category with optional parent for hierarchical taxonomy.

    Examples: Women > Dresses > Maxi Dresses
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent"
    )
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class Product(Base):
    """Fashion product with pricing, inventory, and attributes."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False)
    size: Mapped[str | None] = mapped_column(String(20), nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    material: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"


class Customer(Base):
    """Customer profile with contact and address information."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(String(10), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="US", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer")

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, email='{self.email}')>"


class Order(Base):
    """Purchase order with status tracking and financial summary."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, confirmed, processing, shipped, delivered, cancelled, returned
    subtotal: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    shipping_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    shipping_address_line1: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    shipping_address_line2: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    shipping_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shipping_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order"
    )
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="order")
    refunds: Mapped[list["Refund"]] = relationship("Refund", back_populates="order")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"


class OrderItem(Base):
    """Individual line item within an order."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"


class Payment(Base):
    """Payment transaction linked to an order."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False
    )
    payment_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # credit_card, debit_card, paypal, apple_pay, google_pay
    payment_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, completed, failed, refunded
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="payments")
    refunds: Mapped[list["Refund"]] = relationship("Refund", back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, order_id={self.order_id}, status='{self.payment_status}')>"


class Refund(Base):
    """Refund record linked to an order, payment, and optionally a specific item."""

    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False
    )
    payment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payments.id"), nullable=False
    )
    order_item_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("order_items.id"), nullable=True
    )
    reason: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # damaged, wrong_item, not_as_described, changed_mind, size_issue, quality_issue
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, approved, processed, rejected
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="refunds")
    payment: Mapped["Payment"] = relationship("Payment", back_populates="refunds")

    def __repr__(self) -> str:
        return f"<Refund(id={self.id}, order_id={self.order_id}, status='{self.status}')>"
