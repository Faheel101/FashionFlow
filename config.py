"""Centralized configuration using Pydantic Settings.

All environment variables are loaded from .env and validated at startup.
Import ``get_settings`` anywhere in the project for typed access to config.

Usage::

    from config import get_settings
    settings = get_settings()
    print(settings.gcp_project_id)
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Google Cloud / BigQuery ──────────────────────────────────────────
    gcp_project_id: str = Field(description="GCP project ID")
    gcp_location: str = Field(default="US", description="BigQuery dataset location")
    google_application_credentials: str = Field(
        description="Path to GCP service account JSON key"
    )

    bq_dataset_raw: str = Field(default="fashionflow_raw")
    bq_dataset_staging: str = Field(default="fashionflow_staging")
    bq_dataset_mart: str = Field(default="fashionflow_mart")

    # ── Source System ────────────────────────────────────────────────────
    source_api_host: str = Field(default="127.0.0.1")
    source_api_port: int = Field(default=8000)
    source_api_key: str = Field(description="API key for source system authentication")
    source_db_path: str = Field(default="data/fashionflow.db")

    # ── dlt ──────────────────────────────────────────────────────────────
    dlt_pipeline_name: str = Field(default="fashionflow_commerce")
    dlt_destination: str = Field(default="bigquery")

    # ── dbt ──────────────────────────────────────────────────────────────
    dbt_project_dir: str = Field(default="transformations")
    dbt_profiles_dir: str = Field(default="transformations")
    dbt_target: str = Field(default="dev")

    # ── Dagster ──────────────────────────────────────────────────────────
    dagster_home: str = Field(default=".dagster")

    @property
    def source_api_url(self) -> str:
        """Full URL for the source system API."""
        return f"http://{self.source_api_host}:{self.source_api_port}"

    @property
    def source_db_full_path(self) -> Path:
        """Absolute path to the SQLite database file."""
        return PROJECT_ROOT / self.source_db_path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance. Call once at startup."""
    return Settings()  # type: ignore[call-arg]
