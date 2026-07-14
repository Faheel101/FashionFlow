"""Customer endpoints for the FashionFlow Commerce API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from source_system.api.dependencies import (
    PaginationParams,
    build_paginated_response,
    get_db,
    get_pagination,
)
from source_system.api.schemas import CustomerResponse, PaginatedResponse
from source_system.database.models import Customer

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=PaginatedResponse)
def list_customers(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> dict:
    """List all customers with pagination."""
    total = db.query(func.count(Customer.id)).scalar() or 0
    rows = (
        db.query(Customer)
        .order_by(Customer.id)
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    data = [CustomerResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> CustomerResponse:
    """Get a single customer by ID."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse.model_validate(customer)
