"""Payment endpoints for the FashionFlow Commerce API."""

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
from source_system.api.schemas import PaginatedResponse, PaymentResponse
from source_system.database.models import Payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("", response_model=PaginatedResponse)
def list_payments(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    order_id: int | None = Query(default=None, description="Filter by order ID"),
    payment_method: str | None = Query(
        default=None,
        description="Filter by payment method (credit_card, debit_card, paypal, apple_pay, google_pay)",
    ),
    payment_status: str | None = Query(
        default=None,
        description="Filter by payment status (pending, completed, failed, refunded)",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """List payments with pagination, filtering, and incremental support."""
    query = db.query(Payment)

    if updated_since:
        query = query.filter(Payment.updated_at > updated_since)
    if order_id is not None:
        query = query.filter(Payment.order_id == order_id)
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
    if payment_status:
        query = query.filter(Payment.payment_status == payment_status)

    total = query.count()
    rows = (
        query.order_by(Payment.id)
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    data = [PaymentResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)) -> PaymentResponse:
    """Get a single payment by ID."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse.model_validate(payment)
