"""Order endpoints for the FashionFlow Commerce API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from source_system.api.dependencies import (
    PaginationParams,
    build_paginated_response,
    get_db,
    get_pagination,
)
from source_system.api.schemas import OrderResponse, PaginatedResponse
from source_system.database.models import Order

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=PaginatedResponse)
def list_orders(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> dict:
    """List all orders with pagination."""
    total = db.query(func.count(Order.id)).scalar() or 0
    rows = (
        db.query(Order)
        .order_by(Order.id)
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
