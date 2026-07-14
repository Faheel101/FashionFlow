"""Tests for API key authentication."""

import pytest
from fastapi.testclient import TestClient


class TestAuthentication:
    """Verify API key enforcement across all endpoints."""

    PROTECTED_ENDPOINTS = [
        "/api/v1/customers",
        "/api/v1/products",
        "/api/v1/orders",
        "/api/v1/order-items",
        "/api/v1/payments",
        "/api/v1/refunds",
    ]

    def test_health_check_no_auth_required(self, test_client: TestClient):
        """Health endpoint should be accessible without auth."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.parametrize("endpoint", PROTECTED_ENDPOINTS)
    def test_missing_api_key_returns_401(
        self, test_client: TestClient, endpoint: str
    ):
        """Endpoints without API key should return 401."""
        response = test_client.get(endpoint)
        assert response.status_code == 401

    @pytest.mark.parametrize("endpoint", PROTECTED_ENDPOINTS)
    def test_invalid_api_key_returns_403(
        self, test_client: TestClient, endpoint: str, bad_auth_headers: dict
    ):
        """Endpoints with wrong API key should return 403."""
        response = test_client.get(endpoint, headers=bad_auth_headers)
        assert response.status_code == 403

    @pytest.mark.parametrize("endpoint", PROTECTED_ENDPOINTS)
    def test_valid_api_key_returns_200(
        self, test_client: TestClient, endpoint: str, auth_headers: dict
    ):
        """Endpoints with valid API key should return 200."""
        response = test_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200
