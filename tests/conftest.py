"""Shared pytest fixtures for the FashionFlow test suite."""

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _set_test_env() -> None:
    """Ensure test-specific environment variables are set."""
    os.environ.setdefault("SOURCE_DB_PATH", "data/test_fashionflow.db")
    os.environ.setdefault("SOURCE_API_KEY", "test-api-key")
    os.environ.setdefault("GCP_PROJECT_ID", "test-project")
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "test-credentials.json")


@pytest.fixture()
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture()
def data_dir(project_root: Path) -> Path:
    """Return the data directory, creating it if needed."""
    d = project_root / "data"
    d.mkdir(exist_ok=True)
    return d
