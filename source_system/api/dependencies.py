"""FastAPI dependencies for the FashionFlow Commerce API.

Provides dependency injection for database sessions, pagination,
API key authentication, and incremental loading support.
"""

import math
import os
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime

from fastapi import Depends, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from source_system.database.connection import get_session_factory

# ── API Key Authentication ───────────────────────────────────────────────────

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(
    api_key: str | None = Security(API_KEY_HEADER),
) -> str:
    """Validate the API key from the request header.

    The expected key is read from the SOURCE_API_KEY environment variable.
    If no key is configured, authentication is disabled (dev mode).

    Raises:
        HTTPException: 401 if key is missing, 403 if key is invalid.
    """
    expected_key = os.environ.get("SOURCE_API_KEY")

    # If no key configured, skip auth (dev convenience)
    if not expected_key:
        return "dev-mode"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key


# ── Database Session ─────────────────────────────────────────────────────────


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, closing it after the request."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


# ── Pagination ───────────────────────────────────────────────────────────────


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


# ── Incremental Loading ─────────────────────────────────────────────────────


def get_updated_since(
    updated_since: datetime | None = Query(
        default=None,
        description="ISO 8601 timestamp. Returns only records updated after this time. "
        "Used for incremental data loading.",
        examples=["2026-01-01T00:00:00"],
    ),
) -> datetime | None:
    """Extract the optional updated_since filter for incremental loads."""
    return updated_since
