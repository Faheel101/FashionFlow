"""Fixtures for source system tests.

Provides a fresh seeded test database and a FastAPI test client
for each test session.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from source_system.database.connection import get_engine, get_session, init_db, reset_engine
from source_system.database.models import Base
from source_system.generators.historical import HistoricalDataGenerator

TEST_DB_PATH = "data/test_fashionflow.db"
TEST_API_KEY = "test-api-key-12345"


@pytest.fixture(scope="session", autouse=True)
def _setup_test_env():
    """Set test environment variables before anything imports settings."""
    os.environ["SOURCE_DB_PATH"] = TEST_DB_PATH
    os.environ["SOURCE_API_KEY"] = TEST_API_KEY
    os.environ["GCP_PROJECT_ID"] = "test-project"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "test-creds.json"


@pytest.fixture(scope="session")
def seeded_engine(_setup_test_env):
    """Create a test database with a small dataset.

    Uses a smaller seed for fast tests (~500 orders instead of 50k).
    """
    db_file = Path(TEST_DB_PATH)
    if db_file.exists():
        db_file.unlink()

    reset_engine()
    engine = init_db(TEST_DB_PATH)

    # Generate a small dataset for testing
    generator = HistoricalDataGenerator(
        seed=99,
        num_customers=100,
        num_products=50,
        num_orders=500,
        history_days=90,
    )
    data = generator.generate()

    from source_system.database.models import (
        Category,
        Customer,
        Order,
        OrderItem,
        Payment,
        Product,
        Refund,
    )

    table_map = [
        ("categories", Category),
        ("products", Product),
        ("customers", Customer),
        ("orders", Order),
        ("order_items", OrderItem),
        ("payments", Payment),
        ("refunds", Refund),
    ]

    with get_session(engine) as session:
        for table_name, model_class in table_map:
            records = data[table_name]
            if records:
                session.execute(model_class.__table__.insert(), records)
                session.flush()

    yield engine

    # Cleanup — dispose engine before deleting on Windows
    engine.dispose()
    reset_engine()
    try:
        if db_file.exists():
            db_file.unlink()
    except PermissionError:
        pass  # Windows file lock — harmless, cleaned up next run


@pytest.fixture(scope="session")
def test_client(seeded_engine):
    """Provide a FastAPI test client with the seeded database."""
    from source_system.api.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture()
def auth_headers():
    """Return headers with a valid API key."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture()
def bad_auth_headers():
    """Return headers with an invalid API key."""
    return {"X-API-Key": "wrong-key"}
