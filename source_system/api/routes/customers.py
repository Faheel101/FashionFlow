"""Customer endpoints for the FashionFlow Commerce API."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from source_system.api.dependencies import (
    PaginationParams,
    build_paginated_response,
    get_db,
    get_pagination,
    get_updated_since,
)
from source_system.api.schemas import CustomerResponse, PaginatedResponse
from source_system.database.models import Customer

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=PaginatedResponse)
def list_customers(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    city: str | None = Query(default=None, description="Filter by city"),
    state: str | None = Query(default=None, description="Filter by state abbreviation"),
    country: str | None = Query(default=None, description="Filter by country"),
    db: Session = Depends(get_db),
) -> dict:
    """List customers with pagination, filtering, and incremental support."""
    query = db.query(Customer)

    if updated_since:
        query = query.filter(Customer.updated_at > updated_since)
    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)
    if city:
        query = query.filter(Customer.city == city)
    if state:
        query = query.filter(Customer.state == state)
    if country:
        query = query.filter(Customer.country == country)

    total = query.count()
    rows = (
        query.order_by(Customer.id)
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
