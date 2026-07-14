"""Refund endpoints for the FashionFlow Commerce API."""

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
from source_system.api.schemas import PaginatedResponse, RefundResponse
from source_system.database.models import Refund

router = APIRouter(prefix="/refunds", tags=["Refunds"])


@router.get("", response_model=PaginatedResponse)
def list_refunds(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    order_id: int | None = Query(default=None, description="Filter by order ID"),
    reason: str | None = Query(
        default=None,
        description="Filter by reason (damaged, wrong_item, not_as_described, changed_mind, size_issue, quality_issue)",
    ),
    status: str | None = Query(
        default=None,
        description="Filter by refund status (pending, approved, processed, rejected)",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """List refunds with pagination, filtering, and incremental support."""
    query = db.query(Refund)

    if updated_since:
        query = query.filter(Refund.updated_at > updated_since)
    if order_id is not None:
        query = query.filter(Refund.order_id == order_id)
    if reason:
        query = query.filter(Refund.reason == reason)
    if status:
        query = query.filter(Refund.status == status)

    total = query.count()
    rows = (
        query.order_by(Refund.id)
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
