"""Order endpoints for the FashionFlow Commerce API."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from source_system.api.dependencies import (
    PaginationParams,
    build_paginated_response,
    get_db,
    get_pagination,
    get_updated_since,
)
from source_system.api.schemas import OrderResponse, PaginatedResponse
from source_system.database.models import Order

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=PaginatedResponse)
def list_orders(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    status: str | None = Query(
        default=None,
        description="Filter by order status (pending, confirmed, processing, shipped, delivered, cancelled, returned)",
    ),
    customer_id: int | None = Query(default=None, description="Filter by customer ID"),
    created_after: datetime | None = Query(
        default=None, description="Orders created after this timestamp"
    ),
    created_before: datetime | None = Query(
        default=None, description="Orders created before this timestamp"
    ),
    min_total: float | None = Query(default=None, ge=0, description="Minimum order total"),
    max_total: float | None = Query(default=None, ge=0, description="Maximum order total"),
    db: Session = Depends(get_db),
) -> dict:
    """List orders with pagination, filtering, and incremental support."""
    query = db.query(Order)

    if updated_since:
        query = query.filter(Order.updated_at > updated_since)
    if status:
        query = query.filter(Order.status == status)
    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)
    if created_after:
        query = query.filter(Order.created_at >= created_after)
    if created_before:
        query = query.filter(Order.created_at <= created_before)
    if min_total is not None:
        query = query.filter(Order.total_amount >= min_total)
    if max_total is not None:
        query = query.filter(Order.total_amount <= max_total)

    total = query.count()
    rows = (
        query.order_by(Order.id)
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    data = [OrderResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderResponse:
    """Get a single order by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse.model_validate(order)
