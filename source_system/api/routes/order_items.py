"""Order item endpoints for the FashionFlow Commerce API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from source_system.api.dependencies import (
    PaginationParams,
    build_paginated_response,
    get_db,
    get_pagination,
)
from source_system.api.schemas import OrderItemResponse, PaginatedResponse
from source_system.database.models import OrderItem

router = APIRouter(prefix="/order-items", tags=["Order Items"])


@router.get("", response_model=PaginatedResponse)
def list_order_items(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> dict:
    """List all order items with pagination."""
    total = db.query(func.count(OrderItem.id)).scalar() or 0
    rows = (
        db.query(OrderItem)
        .order_by(OrderItem.id)
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    data = [OrderItemResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/{item_id}", response_model=OrderItemResponse)
def get_order_item(item_id: int, db: Session = Depends(get_db)) -> OrderItemResponse:
    """Get a single order item by ID."""
    item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return OrderItemResponse.model_validate(item)
