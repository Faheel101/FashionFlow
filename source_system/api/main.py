"""FashionFlow Commerce API — FastAPI application.

A simulated ecommerce REST API serving data from SQLite.
Designed to mimic a real commerce backend for data pipeline ingestion.

Usage::

    uv run uvicorn source_system.api.main:app --reload
    uv run uvicorn source_system.api.main:app --host 0.0.0.0 --port 8000
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from source_system.api.dependencies import get_api_key
from source_system.api.routes import ALL_ROUTERS
from source_system.database.connection import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize the database engine on startup."""
    get_engine()
    yield


app = FastAPI(
    title="FashionFlow Commerce API",
    description=(
        "Simulated fashion ecommerce REST API. "
        "Serves customers, products, orders, payments, and refunds "
        "from a SQLite database for data pipeline ingestion.\n\n"
        "**Authentication:** Include `X-API-Key` header with all requests.\n\n"
        "**Incremental Loading:** Use `updated_since` query parameter "
        "to fetch only records modified after a given timestamp."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Error Handlers ───────────────────────────────────────────────────────────


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle value errors as 422 responses."""
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors with a generic 500 response."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Health Check (no auth required) ─────────────────────────────────────────


@app.get("/health", tags=["System"])
def health_check() -> dict:
    """Health check endpoint. No authentication required."""
    return {"status": "healthy", "service": "fashionflow-commerce-api"}


# ── Register Routers (all require API key) ───────────────────────────────────

for router in ALL_ROUTERS:
    app.include_router(
        router,
        prefix="/api/v1",
        dependencies=[Depends(get_api_key)],
    )
