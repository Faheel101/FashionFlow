"""dlt source for the FashionFlow Commerce API.

Defines dlt resources for each API entity with automatic pagination.
Each resource yields pages of records from the source API.

Usage::

    import dlt
    from ingestion.sources.commerce_api import fashionflow_source

    pipeline = dlt.pipeline(
        pipeline_name="fashionflow_commerce",
        destination="bigquery",
        dataset_name="fashionflow_raw",
    )
    pipeline.run(fashionflow_source())
"""

from collections.abc import Iterator

import dlt
import httpx


PAGE_SIZE = 500


def _paginate(
    client: httpx.Client,
    endpoint: str,
) -> Iterator[list[dict]]:
    """Paginate through an API endpoint, yielding pages of records.

    Args:
        client: Configured httpx client with base_url and auth headers.
        endpoint: API path (e.g. "/api/v1/customers").

    Yields:
        Lists of record dictionaries, one per page.
    """
    page = 1

    while True:
        response = client.get(
            endpoint,
            params={"page": page, "page_size": PAGE_SIZE},
        )
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


@dlt.resource(name="customers", write_disposition="replace", primary_key="id")
def customers_resource(client: httpx.Client) -> Iterator[list[dict]]:
    """Load all customers from the source API."""
    yield from _paginate(client, "/api/v1/customers")


@dlt.resource(name="products", write_disposition="replace", primary_key="id")
def products_resource(client: httpx.Client) -> Iterator[list[dict]]:
    """Load all products from the source API."""
    yield from _paginate(client, "/api/v1/products")


@dlt.resource(name="orders", write_disposition="replace", primary_key="id")
def orders_resource(client: httpx.Client) -> Iterator[list[dict]]:
    """Load all orders from the source API."""
    yield from _paginate(client, "/api/v1/orders")


@dlt.resource(name="order_items", write_disposition="replace", primary_key="id")
def order_items_resource(client: httpx.Client) -> Iterator[list[dict]]:
    """Load all order items from the source API."""
    yield from _paginate(client, "/api/v1/order-items")


@dlt.resource(name="payments", write_disposition="replace", primary_key="id")
def payments_resource(client: httpx.Client) -> Iterator[list[dict]]:
    """Load all payments from the source API."""
    yield from _paginate(client, "/api/v1/payments")


@dlt.resource(name="refunds", write_disposition="replace", primary_key="id")
def refunds_resource(client: httpx.Client) -> Iterator[list[dict]]:
    """Load all refunds from the source API."""
    yield from _paginate(client, "/api/v1/refunds")
