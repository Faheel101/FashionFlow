"""Refund endpoints for the FashionFlow Commerce API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from source_system.api.dependencies import (
    PaginationParams,
    build_paginated_response,
    get_db,
    get_pagination,
)
from source_system.api.schemas import PaginatedResponse, RefundResponse
from source_system.database.models import Refund

router = APIRouter(prefix="/refunds", tags=["Refunds"])


@router.get("", response_model=PaginatedResponse)
def list_refunds(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> dict:
    """List all refunds with pagination."""
    total = db.query(func.count(Refund.id)).scalar() or 0
    rows = (
        db.query(Refund)
        .order_by(Refund.id)
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    data = [RefundResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/{refund_id}", response_model=RefundResponse)
def get_refund(refund_id: int, db: Session = Depends(get_db)) -> RefundResponse:
    """Get a single refund by ID."""
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    return RefundResponse.model_validate(refund)
