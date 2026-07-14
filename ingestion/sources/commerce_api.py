"""dlt source for the FashionFlow Commerce API.

Supports both full-refresh and incremental loading modes.
Incremental mode uses the `updated_since` API parameter and dlt's
merge write disposition with `updated_at` as the incremental cursor.

Usage::

    import dlt
    from ingestion.sources.commerce_api import fashionflow_source

    # Full refresh
    pipeline.run(fashionflow_source())

    # Incremental (after initial load)
    pipeline.run(fashionflow_source())  # dlt tracks state automatically
"""

from collections.abc import Iterator
from datetime import datetime

import dlt
from dlt.extract.incremental import Incremental
import httpx


PAGE_SIZE = 500
# Lookback window to catch late-arriving updates (seconds)
LOOKBACK_SECONDS = 3600  # 1 hour


def _paginate(
    client: httpx.Client,
    endpoint: str,
    updated_since: datetime | None = None,
) -> Iterator[list[dict]]:
    """Paginate through an API endpoint, yielding pages of records.

    Args:
        client: Configured httpx client with base_url and auth headers.
        endpoint: API path (e.g. "/api/v1/customers").
        updated_since: If set, only fetch records updated after this time.

    Yields:
        Lists of record dictionaries, one per page.
    """
    page = 1
    params: dict[str, str | int] = {"page_size": PAGE_SIZE}

    if updated_since:
        params["updated_since"] = updated_since.isoformat()

    while True:
        params["page"] = page
        response = client.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        records = data["data"]
        if not records:
            break

        yield records

        if not data["has_next"]:
            break

        page += 1


@dlt.source(name="fashionflow")
def fashionflow_source(
    api_url: str = dlt.config.value,
    api_key: str = dlt.secrets.value,
) -> Iterator[dlt.resource]:
    """dlt source for the FashionFlow Commerce API.

    Args:
        api_url: Base URL of the source API (e.g. http://127.0.0.1:8000).
        api_key: API key for authentication.

    Yields:
        dlt resources for each entity.
    """
    client = httpx.Client(
        base_url=api_url,
        headers={"X-API-Key": api_key},
        timeout=60.0,
    )

    yield customers_resource(client)
    yield products_resource(client)
    yield orders_resource(client)
    yield order_items_resource(client)
    yield payments_resource(client)
    yield refunds_resource(client)


@dlt.resource(name="customers", write_disposition="merge", primary_key="id")
def customers_resource(
    client: httpx.Client,
    updated_at: Incremental[str] = dlt.sources.incremental(
        "updated_at", initial_value="1970-01-01T00:00:00"
    ),
) -> Iterator[list[dict]]:
    """Load customers with incremental merge on updated_at."""
    updated_since = _parse_cursor(updated_at.last_value)
    yield from _paginate(client, "/api/v1/customers", updated_since)


@dlt.resource(name="products", write_disposition="merge", primary_key="id")
def products_resource(
    client: httpx.Client,
    updated_at: Incremental[str] = dlt.sources.incremental(
        "updated_at", initial_value="1970-01-01T00:00:00"
    ),
) -> Iterator[list[dict]]:
    """Load products with incremental merge on updated_at."""
    updated_since = _parse_cursor(updated_at.last_value)
    yield from _paginate(client, "/api/v1/products", updated_since)


@dlt.resource(name="orders", write_disposition="merge", primary_key="id")
def orders_resource(
    client: httpx.Client,
    updated_at: Incremental[str] = dlt.sources.incremental(
        "updated_at", initial_value="1970-01-01T00:00:00"
    ),
) -> Iterator[list[dict]]:
    """Load orders with incremental merge on updated_at."""
    updated_since = _parse_cursor(updated_at.last_value)
    yield from _paginate(client, "/api/v1/orders", updated_since)


@dlt.resource(name="order_items", write_disposition="merge", primary_key="id")
def order_items_resource(
    client: httpx.Client,
    updated_at: Incremental[str] = dlt.sources.incremental(
        "updated_at", initial_value="1970-01-01T00:00:00"
    ),
) -> Iterator[list[dict]]:
    """Load order items with incremental merge on updated_at."""
    updated_since = _parse_cursor(updated_at.last_value)
    yield from _paginate(client, "/api/v1/order-items", updated_since)


@dlt.resource(name="payments", write_disposition="merge", primary_key="id")
def payments_resource(
    client: httpx.Client,
    updated_at: Incremental[str] = dlt.sources.incremental(
        "updated_at", initial_value="1970-01-01T00:00:00"
    ),
) -> Iterator[list[dict]]:
    """Load payments with incremental merge on updated_at."""
    updated_since = _parse_cursor(updated_at.last_value)
    yield from _paginate(client, "/api/v1/payments", updated_since)


@dlt.resource(name="refunds", write_disposition="merge", primary_key="id")
def refunds_resource(
    client: httpx.Client,
    updated_at: Incremental[str] = dlt.sources.incremental(
        "updated_at", initial_value="1970-01-01T00:00:00"
    ),
) -> Iterator[list[dict]]:
    """Load refunds with incremental merge on updated_at."""
    updated_since = _parse_cursor(updated_at.last_value)
    yield from _paginate(client, "/api/v1/refunds", updated_since)


def _parse_cursor(value: str | None) -> datetime | None:
    """Parse the incremental cursor value into a datetime.

    Applies a lookback window to catch late-arriving updates.

    Args:
        value: ISO format datetime string from dlt state, or None.

    Returns:
        datetime with lookback applied, or None for initial load.
    """
    if not value or value == "1970-01-01T00:00:00":
        return None  # Initial load — fetch everything

    from datetime import timedelta

    try:
        cursor_dt = datetime.fromisoformat(value)
        # Apply lookback window for safety
        return cursor_dt - timedelta(seconds=LOOKBACK_SECONDS)
    except (ValueError, TypeError):
        return None
