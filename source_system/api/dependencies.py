"""FastAPI dependencies for the FashionFlow Commerce API.

Provides dependency injection for database sessions, pagination
parameters, and shared query utilities.
"""

import math
from collections.abc import Generator
from dataclasses import dataclass

from fastapi import Query
from sqlalchemy.orm import Session

from source_system.database.connection import get_session_factory


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, closing it after the request."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


@dataclass
class PaginationParams:
    """Pagination parameters extracted from query string."""

    page: int
    page_size: int
    offset: int


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=100, ge=1, le=1000, description="Records per page (max 1000)"
    ),
) -> PaginationParams:
    """Extract and validate pagination parameters."""
    return PaginationParams(
        page=page,
        page_size=page_size,
        offset=(page - 1) * page_size,
    )


def build_paginated_response(
    data: list,
    total_count: int,
    pagination: PaginationParams,
) -> dict:
    """Build a standardized paginated response dictionary.

    Args:
        data: List of serialized records for the current page.
        total_count: Total number of matching records.
        pagination: Current pagination parameters.

    Returns:
        Dictionary matching the PaginatedResponse schema.
    """
    total_pages = max(1, math.ceil(total_count / pagination.page_size))

    return {
        "data": data,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": pagination.page < total_pages,
        "has_previous": pagination.page > 1,
    }
