"""Tests for API endpoints — pagination, filtering, and responses."""

import pytest
from fastapi.testclient import TestClient


class TestPagination:
    """Verify pagination behavior across endpoints."""

    def test_default_pagination(self, test_client: TestClient, auth_headers: dict):
        """Default page=1, page_size=100."""
        response = test_client.get("/api/v1/customers", headers=auth_headers)
        data = response.json()

        assert response.status_code == 200
        assert data["page"] == 1
        assert data["page_size"] == 100
        assert data["total_count"] > 0
        assert data["total_pages"] >= 1
        assert isinstance(data["data"], list)
        assert isinstance(data["has_next"], bool)
        assert isinstance(data["has_previous"], bool)

    def test_custom_page_size(self, test_client: TestClient, auth_headers: dict):
        """Custom page_size should limit results."""
        response = test_client.get(
            "/api/v1/customers?page_size=5", headers=auth_headers
        )
        data = response.json()

        assert data["page_size"] == 5
        assert len(data["data"]) <= 5

    def test_page_two(self, test_client: TestClient, auth_headers: dict):
        """Page 2 should return different records than page 1."""
        r1 = test_client.get(
            "/api/v1/customers?page=1&page_size=5", headers=auth_headers
        )
        r2 = test_client.get(
            "/api/v1/customers?page=2&page_size=5", headers=auth_headers
        )

        ids_1 = [c["id"] for c in r1.json()["data"]]
        ids_2 = [c["id"] for c in r2.json()["data"]]

        assert r2.json()["page"] == 2
        assert r2.json()["has_previous"] is True
        assert set(ids_1).isdisjoint(set(ids_2))

    def test_invalid_page_zero(self, test_client: TestClient, auth_headers: dict):
        """Page 0 should return 422."""
        response = test_client.get(
            "/api/v1/customers?page=0", headers=auth_headers
        )
        assert response.status_code == 422

    def test_page_size_exceeds_max(self, test_client: TestClient, auth_headers: dict):
        """Page size > 1000 should return 422."""
        response = test_client.get(
            "/api/v1/customers?page_size=1001", headers=auth_headers
        )
        assert response.status_code == 422


class TestCustomerEndpoints:
    """Tests for customer API endpoints."""

    def test_list_customers(self, test_client: TestClient, auth_headers: dict):
        """Should return paginated customer list."""
        response = test_client.get("/api/v1/customers?page_size=3", headers=auth_headers)
        data = response.json()

        assert response.status_code == 200
        assert len(data["data"]) <= 3
        assert data["total_count"] > 0

        customer = data["data"][0]
        assert "id" in customer
        assert "email" in customer
        assert "first_name" in customer
        assert "created_at" in customer

    def test_get_customer_by_id(self, test_client: TestClient, auth_headers: dict):
        """Should return a single customer."""
        response = test_client.get("/api/v1/customers/1", headers=auth_headers)
        assert response.status_code == 200

        customer = response.json()
        assert customer["id"] == 1
        assert "email" in customer

    def test_get_customer_not_found(self, test_client: TestClient, auth_headers: dict):
        """Should return 404 for nonexistent customer."""
        response = test_client.get("/api/v1/customers/999999", headers=auth_headers)
        assert response.status_code == 404

    def test_filter_by_state(self, test_client: TestClient, auth_headers: dict):
        """Should filter customers by state."""
        # First get a valid state
        r = test_client.get("/api/v1/customers?page_size=1", headers=auth_headers)
        state = r.json()["data"][0].get("state")

        if state:
            response = test_client.get(
                f"/api/v1/customers?state={state}", headers=auth_headers
            )
            data = response.json()
            assert all(c["state"] == state for c in data["data"])


class TestProductEndpoints:
    """Tests for product API endpoints."""

    def test_list_products(self, test_client: TestClient, auth_headers: dict):
        """Should return paginated product list."""
        response = test_client.get("/api/v1/products?page_size=5", headers=auth_headers)
        data = response.json()

        assert response.status_code == 200
        product = data["data"][0]
        assert "sku" in product
        assert "price" in product
        assert "brand" in product

    def test_get_product_by_id(self, test_client: TestClient, auth_headers: dict):
        """Should return a single product."""
        response = test_client.get("/api/v1/products/1", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_filter_by_active(self, test_client: TestClient, auth_headers: dict):
        """Should filter products by active status."""
        response = test_client.get(
            "/api/v1/products?is_active=true", headers=auth_headers
        )
        data = response.json()
        assert all(p["is_active"] is True for p in data["data"])

    def test_filter_by_price_range(self, test_client: TestClient, auth_headers: dict):
        """Should filter products by price range."""
        response = test_client.get(
            "/api/v1/products?min_price=50&max_price=100", headers=auth_headers
        )
        data = response.json()
        for p in data["data"]:
            assert 50 <= p["price"] <= 100


class TestOrderEndpoints:
    """Tests for order API endpoints."""

    def test_list_orders(self, test_client: TestClient, auth_headers: dict):
        """Should return paginated order list."""
        response = test_client.get("/api/v1/orders?page_size=5", headers=auth_headers)
        data = response.json()

        assert response.status_code == 200
        order = data["data"][0]
        assert "order_number" in order
        assert "total_amount" in order
        assert "status" in order

    def test_filter_by_status(self, test_client: TestClient, auth_headers: dict):
        """Should filter orders by status."""
        response = test_client.get(
            "/api/v1/orders?status=delivered", headers=auth_headers
        )
        data = response.json()
        assert all(o["status"] == "delivered" for o in data["data"])

    def test_filter_by_customer_id(self, test_client: TestClient, auth_headers: dict):
        """Should filter orders by customer ID."""
        response = test_client.get(
            "/api/v1/orders?customer_id=1", headers=auth_headers
        )
        data = response.json()
        assert all(o["customer_id"] == 1 for o in data["data"])


class TestOrderItemEndpoints:
    """Tests for order item API endpoints."""

    def test_list_order_items(self, test_client: TestClient, auth_headers: dict):
        """Should return paginated order item list."""
        response = test_client.get(
            "/api/v1/order-items?page_size=5", headers=auth_headers
        )
        data = response.json()

        assert response.status_code == 200
        item = data["data"][0]
        assert "order_id" in item
        assert "product_id" in item
        assert "quantity" in item
        assert "total_price" in item

    def test_filter_by_order_id(self, test_client: TestClient, auth_headers: dict):
        """Should filter items by order ID."""
        response = test_client.get(
            "/api/v1/order-items?order_id=1", headers=auth_headers
        )
        data = response.json()
        assert all(i["order_id"] == 1 for i in data["data"])


class TestPaymentEndpoints:
    """Tests for payment API endpoints."""

    def test_list_payments(self, test_client: TestClient, auth_headers: dict):
        """Should return paginated payment list."""
        response = test_client.get("/api/v1/payments?page_size=5", headers=auth_headers)
        data = response.json()

        assert response.status_code == 200
        payment = data["data"][0]
        assert "payment_method" in payment
        assert "payment_status" in payment
        assert "transaction_id" in payment

    def test_filter_by_method(self, test_client: TestClient, auth_headers: dict):
        """Should filter payments by method."""
        response = test_client.get(
            "/api/v1/payments?payment_method=credit_card", headers=auth_headers
        )
        data = response.json()
        assert all(p["payment_method"] == "credit_card" for p in data["data"])


class TestRefundEndpoints:
    """Tests for refund API endpoints."""

    def test_list_refunds(self, test_client: TestClient, auth_headers: dict):
        """Should return paginated refund list."""
        response = test_client.get("/api/v1/refunds?page_size=5", headers=auth_headers)
        data = response.json()

        assert response.status_code == 200
        if data["data"]:
            refund = data["data"][0]
            assert "reason" in refund
            assert "status" in refund
            assert "amount" in refund


class TestUpdatedSince:
    """Tests for incremental loading via updated_since parameter."""

    def test_updated_since_returns_subset(
        self, test_client: TestClient, auth_headers: dict
    ):
        """updated_since should return fewer records than no filter."""
        all_response = test_client.get("/api/v1/orders", headers=auth_headers)
        filtered_response = test_client.get(
            "/api/v1/orders?updated_since=2026-06-01T00:00:00", headers=auth_headers
        )

        all_count = all_response.json()["total_count"]
        filtered_count = filtered_response.json()["total_count"]

        assert filtered_count <= all_count

    def test_updated_since_far_future_returns_empty(
        self, test_client: TestClient, auth_headers: dict
    ):
        """A future timestamp should return zero records."""
        response = test_client.get(
            "/api/v1/orders?updated_since=2030-01-01T00:00:00", headers=auth_headers
        )
        assert response.json()["total_count"] == 0
