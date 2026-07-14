"""Product endpoints for the FashionFlow Commerce API."""

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
from source_system.api.schemas import PaginatedResponse, ProductResponse
from source_system.database.models import Product

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=PaginatedResponse)
def list_products(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    category_id: int | None = Query(default=None, description="Filter by category ID"),
    brand: str | None = Query(default=None, description="Filter by brand name"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price"),
    color: str | None = Query(default=None, description="Filter by color"),
    db: Session = Depends(get_db),
) -> dict:
    """List products with pagination, filtering, and incremental support."""
    query = db.query(Product)

    if updated_since:
        query = query.filter(Product.updated_at > updated_since)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if brand:
        query = query.filter(Product.brand == brand)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if color:
        query = query.filter(Product.color == color)

    total = query.count()
    rows = (
        query.order_by(Product.id)
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    data = [ProductResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductResponse:
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)
