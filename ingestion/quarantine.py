"""Quarantine handler for invalid records during ingestion.

Instead of failing entire pipeline runs, invalid records are routed
to quarantine tables with failure reasons attached.

Usage::

    from ingestion.quarantine import QuarantineHandler
    qh = QuarantineHandler()
    valid, quarantined = qh.validate_and_split(records, rules)
    qh.write_quarantine("customers", quarantined)
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime

from google.cloud import bigquery


QUARANTINE_DATASET = "fashionflow_quarantine"


@dataclass
class ValidationRule:
    """A single record-level validation rule."""

    field: str
    rule_type: str  # not_null, positive, in_list, regex, custom
    params: dict | None = None
    message: str = ""

    @classmethod
    def not_null(cls, field: str) -> "ValidationRule":
        return cls(field, "not_null", message=f"{field} must not be null")

    @classmethod
    def positive(cls, field: str) -> "ValidationRule":
        return cls(field, "positive", message=f"{field} must be positive")

    @classmethod
    def in_list(cls, field: str, values: list) -> "ValidationRule":
        return cls(field, "in_list", {"values": values}, f"{field} must be in {values}")

    @classmethod
    def min_value(cls, field: str, minimum: float) -> "ValidationRule":
        return cls(field, "min_value", {"min": minimum}, f"{field} must be >= {minimum}")


class QuarantineHandler:
    """Validate records and route invalid ones to quarantine."""

    def __init__(self, project_id: str | None = None) -> None:
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID", "de-project-502311")
        self.client = bigquery.Client(project=self.project_id)
        self._ensure_dataset()

    def _ensure_dataset(self) -> None:
        dataset_id = f"{self.project_id}.{QUARANTINE_DATASET}"
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        self.client.create_dataset(dataset, exists_ok=True)

    def validate_and_split(
        self,
        records: list[dict],
        rules: list[ValidationRule],
    ) -> tuple[list[dict], list[dict]]:
        """Split records into valid and quarantined lists.

        Returns:
            Tuple of (valid_records, quarantined_records).
            Quarantined records get extra fields: _quarantine_reason, _quarantined_at.
        """
        valid: list[dict] = []
        quarantined: list[dict] = []

        for record in records:
            failures = self._check_record(record, rules)
            if failures:
                record["_quarantine_reasons"] = json.dumps(failures)
                record["_quarantined_at"] = datetime.utcnow().isoformat()
                quarantined.append(record)
            else:
                valid.append(record)

        return valid, quarantined

    def _check_record(self, record: dict, rules: list[ValidationRule]) -> list[str]:
        """Check a single record against all rules. Returns list of failure messages."""
        failures: list[str] = []

        for rule in rules:
            value = record.get(rule.field)

            if rule.rule_type == "not_null" and value is None:
                failures.append(rule.message)

            elif rule.rule_type == "positive" and value is not None and value <= 0:
                failures.append(rule.message)

            elif rule.rule_type == "in_list" and value not in rule.params["values"]:
                failures.append(rule.message)

            elif rule.rule_type == "min_value" and value is not None and value < rule.params["min"]:
                failures.append(rule.message)

        return failures

    def write_quarantine(self, source_table: str, records: list[dict]) -> int:
        """Write quarantined records to BigQuery quarantine table.

        Returns:
            Number of records written.
        """
        if not records:
            return 0

        table_id = f"{self.project_id}.{QUARANTINE_DATASET}.{source_table}_quarantine"

        # Create table if needed (schema auto-detected)
        job_config = bigquery.LoadJobConfig(
            autodetect=True,
            write_disposition="WRITE_APPEND",
        )

        job = self.client.load_table_from_json(records, table_id, job_config=job_config)
        job.result()

        return len(records)
