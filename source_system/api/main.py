"""FashionFlow Commerce API — FastAPI application.

A simulated ecommerce REST API serving data from SQLite.
Designed to mimic a real commerce backend for data pipeline ingestion.

Usage::

    uv run uvicorn source_system.api.main:app --reload
    uv run uvicorn source_system.api.main:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

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
        "from a SQLite database for data pipeline ingestion."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Health Check ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["System"])
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "fashionflow-commerce-api"}


# ── Register Routers ─────────────────────────────────────────────────────────

for router in ALL_ROUTERS:
    app.include_router(router, prefix="/api/v1")
