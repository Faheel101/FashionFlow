"""Pydantic response schemas for the FashionFlow Commerce API.

These models define the JSON response shapes for all API endpoints.
They are separate from the SQLAlchemy ORM models to maintain clean
boundaries between the database layer and the API layer.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ── Base ─────────────────────────────────────────────────────────────────────


class TimestampMixin(BaseModel):
    """Common timestamp fields."""

    created_at: datetime
    updated_at: datetime


# ── Categories ───────────────────────────────────────────────────────────────


class CategoryResponse(TimestampMixin):
    """Category response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    parent_category_id: int | None = None
    is_active: bool


# ── Products ─────────────────────────────────────────────────────────────────


class ProductResponse(TimestampMixin):
    """Product response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    description: str | None = None
    category_id: int
    brand: str
    price: float
    cost_price: float
    size: str | None = None
    color: str | None = None
    material: str | None = None
    stock_quantity: int
    is_active: bool


# ── Customers ────────────────────────────────────────────────────────────────


class CustomerResponse(TimestampMixin):
    """Customer response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str
    is_active: bool


# ── Orders ───────────────────────────────────────────────────────────────────


class OrderResponse(TimestampMixin):
    """Order response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    customer_id: int
    status: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total_amount: float
    shipping_address_line1: str | None = None
    shipping_address_line2: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_postal_code: str | None = None
    shipping_country: str | None = None
    notes: str | None = None


# ── Order Items ──────────────────────────────────────────────────────────────


class OrderItemResponse(TimestampMixin):
    """Order item response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    discount_amount: float
    total_price: float


# ── Payments ─────────────────────────────────────────────────────────────────


class PaymentResponse(TimestampMixin):
    """Payment response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    payment_method: str
    payment_status: str
    amount: float
    transaction_id: str


# ── Refunds ──────────────────────────────────────────────────────────────────


class RefundResponse(TimestampMixin):
    """Refund response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    payment_id: int
    order_item_id: int | None = None
    reason: str
    status: str
    amount: float
    notes: str | None = None


# ── Paginated Response ───────────────────────────────────────────────────────


class PaginatedResponse(BaseModel):
    """Wrapper for paginated list responses."""

    data: list
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool
