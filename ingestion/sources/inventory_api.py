"""dlt source for FashionFlow inventory data."""

from collections.abc import Iterator
from datetime import datetime, timedelta

import dlt
from dlt.extract.incremental import Incremental
import httpx

PAGE_SIZE = 500
LOOKBACK_SECONDS = 3600


def _paginate(client: httpx.Client, endpoint: str, updated_since: datetime | None = None) -> Iterator[list[dict]]:
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


def _parse_cursor(value: str | None) -> datetime | None:
    if not value or value == "1970-01-01T00:00:00":
        return None
    try:
        return datetime.fromisoformat(value) - timedelta(seconds=LOOKBACK_SECONDS)
    except (ValueError, TypeError):
        return None


@dlt.source(name="fashionflow_inventory")
def inventory_source(
    api_url: str = dlt.config.value,
    api_key: str = dlt.secrets.value,
) -> Iterator[dlt.resource]:
    client = httpx.Client(base_url=api_url, headers={"X-API-Key": api_key}, timeout=60.0)
    yield inventory_snapshots_resource(client)
    yield inventory_movements_resource(client)


@dlt.resource(name="inventory_snapshots", write_disposition="merge", primary_key="id")
def inventory_snapshots_resource(
    client: httpx.Client,
    updated_at: Incremental[str] = dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00"),
) -> Iterator[list[dict]]:
    yield from _paginate(client, "/api/v1/inventory/snapshots", _parse_cursor(updated_at.last_value))


@dlt.resource(name="inventory_movements", write_disposition="merge", primary_key="id")
def inventory_movements_resource(
    client: httpx.Client,
    updated_at: Incremental[str] = dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00"),
) -> Iterator[list[dict]]:
    yield from _paginate(client, "/api/v1/inventory/movements", _parse_cursor(updated_at.last_value))
