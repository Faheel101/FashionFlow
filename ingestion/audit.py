"""Audit logging for FashionFlow pipeline runs.

Records pipeline execution metadata (timing, row counts, status, errors)
to a BigQuery audit dataset for operational monitoring.

Usage::

    from ingestion.audit import AuditLogger
    audit = AuditLogger()
    run_id = audit.start_run("commerce", "ingestion")
    audit.log_resource(run_id, "customers", row_count=10000, status="success")
    audit.end_run(run_id, status="success")
"""

import os
import uuid
from datetime import datetime

from google.cloud import bigquery


AUDIT_DATASET = "fashionflow_audit"

AUDIT_SCHEMA = {
    "pipeline_runs": [
        bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("pipeline_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("pipeline_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("started_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("completed_at", "TIMESTAMP"),
        bigquery.SchemaField("duration_seconds", "FLOAT64"),
        bigquery.SchemaField("total_rows", "INT64"),
        bigquery.SchemaField("error_message", "STRING"),
        bigquery.SchemaField("metadata", "JSON"),
    ],
    "pipeline_resource_runs": [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("resource_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("row_count", "INT64"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("started_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("completed_at", "TIMESTAMP"),
        bigquery.SchemaField("duration_seconds", "FLOAT64"),
        bigquery.SchemaField("error_message", "STRING"),
    ],
    "quality_check_results": [
        bigquery.SchemaField("table_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("check_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("column_name", "STRING"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("passed", "BOOLEAN", mode="REQUIRED"),
        bigquery.SchemaField("failed_count", "INT64"),
        bigquery.SchemaField("total_count", "INT64"),
        bigquery.SchemaField("checked_at", "TIMESTAMP", mode="REQUIRED"),
    ],
}


class AuditLogger:
    """Log pipeline execution metadata to BigQuery audit tables."""

    def __init__(self, project_id: str | None = None) -> None:
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID", "de-project-502311")
        self.client = bigquery.Client(project=self.project_id)
        self._ensure_audit_dataset()

    def _ensure_audit_dataset(self) -> None:
        """Create audit dataset and tables if they don't exist."""
        dataset_id = f"{self.project_id}.{AUDIT_DATASET}"
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        self.client.create_dataset(dataset, exists_ok=True)

        for table_name, schema in AUDIT_SCHEMA.items():
            table_id = f"{dataset_id}.{table_name}"
            table = bigquery.Table(table_id, schema=schema)
            self.client.create_table(table, exists_ok=True)

    def start_run(self, pipeline_name: str, pipeline_type: str) -> str:
        """Record the start of a pipeline run. Returns the run_id."""
        run_id = str(uuid.uuid4())
        row = {
            "run_id": run_id,
            "pipeline_name": pipeline_name,
            "pipeline_type": pipeline_type,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "total_rows": 0,
        }
        table_id = f"{self.project_id}.{AUDIT_DATASET}.pipeline_runs"
        self.client.insert_rows_json(table_id, [row])
        return run_id

    def log_resource(
        self,
        run_id: str,
        resource_name: str,
        row_count: int = 0,
        status: str = "success",
        duration_seconds: float = 0.0,
        error_message: str | None = None,
    ) -> None:
        """Log a resource-level execution result."""
        row = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "resource_name": resource_name,
            "row_count": row_count,
            "status": status,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": duration_seconds,
            "error_message": error_message,
        }
        table_id = f"{self.project_id}.{AUDIT_DATASET}.pipeline_resource_runs"
        self.client.insert_rows_json(table_id, [row])

    def end_run(
        self,
        run_id: str,
        status: str = "success",
        total_rows: int = 0,
        duration_seconds: float = 0.0,
        error_message: str | None = None,
    ) -> None:
        """Update a pipeline run with completion status."""
        now = datetime.utcnow().isoformat()
        sql = f"""
            UPDATE `{self.project_id}.{AUDIT_DATASET}.pipeline_runs`
            SET status = '{status}',
                completed_at = TIMESTAMP('{now}'),
                duration_seconds = {duration_seconds},
                total_rows = {total_rows}
                {f", error_message = '{error_message}'" if error_message else ""}
            WHERE run_id = '{run_id}'
        """
        self.client.query(sql).result()
