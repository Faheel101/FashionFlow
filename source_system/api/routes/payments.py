"""Payment endpoints for the FashionFlow Commerce API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from source_system.api.dependencies import (
    PaginationParams,
    build_paginated_response,
    get_db,
    get_pagination,
)
from source_system.api.schemas import PaginatedResponse, PaymentResponse
from source_system.database.models import Payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("", response_model=PaginatedResponse)
def list_payments(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> dict:
    """List all payments with pagination."""
    total = db.query(func.count(Payment.id)).scalar() or 0
    rows = (
        db.query(Payment)
        .order_by(Payment.id)
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
