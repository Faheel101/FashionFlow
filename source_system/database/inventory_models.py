"""SQLAlchemy ORM models for the FashionFlow inventory domain.

Tables:
    - inventory_snapshots: Point-in-time inventory levels per product
    - inventory_movements: Individual stock changes (purchase, sale, return, etc.)
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from source_system.database.models import Base


class InventorySnapshot(Base):
    """Point-in-time inventory snapshot per product."""

    __tablename__ = "inventory_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    snapshot_date: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    warehouse_location: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<InventorySnapshot(id={self.id}, product_id={self.product_id}, date='{self.snapshot_date}')>"


class InventoryMovement(Base):
    """Individual inventory stock movement."""

    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    movement_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # purchase, sale, return, damage, adjustment
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    reference_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # order_id, PO number, etc.
    warehouse_location: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    movement_date: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<InventoryMovement(id={self.id}, product_id={self.product_id}, type='{self.movement_type}')>"
