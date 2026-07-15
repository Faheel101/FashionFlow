"""Reusable data quality validation framework for FashionFlow.

Provides configurable checks that run against BigQuery tables and
store results for monitoring.

Usage::

    from ingestion.quality import DataQualityValidator, QualityCheck
    validator = DataQualityValidator(project_id, dataset)
    results = validator.run_checks("orders", [
        QualityCheck.not_null("id"),
        QualityCheck.unique("id"),
        QualityCheck.row_count_min(1000),
    ])
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from google.cloud import bigquery


class CheckType(str, Enum):
    NOT_NULL = "not_null"
    UNIQUE = "unique"
    ACCEPTED_VALUES = "accepted_values"
    ROW_COUNT_MIN = "row_count_min"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    NULL_THRESHOLD = "null_threshold"
    DUPLICATE_DETECTION = "duplicate_detection"
    CUSTOM_SQL = "custom_sql"


@dataclass
class QualityCheck:
    """A single data quality check definition."""

    check_type: CheckType
    column: str | None = None
    params: dict = field(default_factory=dict)
    description: str = ""

    @classmethod
    def not_null(cls, column: str) -> "QualityCheck":
        return cls(CheckType.NOT_NULL, column, description=f"{column} must not be null")

    @classmethod
    def unique(cls, column: str) -> "QualityCheck":
        return cls(CheckType.UNIQUE, column, description=f"{column} must be unique")

    @classmethod
    def accepted_values(cls, column: str, values: list[str]) -> "QualityCheck":
        return cls(CheckType.ACCEPTED_VALUES, column, {"values": values},
                   description=f"{column} must be in {values}")

    @classmethod
    def row_count_min(cls, minimum: int) -> "QualityCheck":
        return cls(CheckType.ROW_COUNT_MIN, params={"minimum": minimum},
                   description=f"Table must have at least {minimum} rows")

    @classmethod
    def null_threshold(cls, column: str, max_pct: float) -> "QualityCheck":
        return cls(CheckType.NULL_THRESHOLD, column, {"max_pct": max_pct},
                   description=f"{column} null rate must be below {max_pct*100}%")

    @classmethod
    def referential_integrity(cls, column: str, ref_table: str, ref_column: str) -> "QualityCheck":
        return cls(CheckType.REFERENTIAL_INTEGRITY, column,
                   {"ref_table": ref_table, "ref_column": ref_column},
                   description=f"{column} must reference {ref_table}.{ref_column}")

    @classmethod
    def custom_sql(cls, sql: str, description: str = "Custom check") -> "QualityCheck":
        return cls(CheckType.CUSTOM_SQL, params={"sql": sql}, description=description)


@dataclass
class CheckResult:
    """Result of a single quality check."""

    table: str
    check_type: str
    column: str | None
    description: str
    passed: bool
    failed_count: int
    total_count: int
    checked_at: str


class DataQualityValidator:
    """Run quality checks against BigQuery tables."""

    def __init__(
        self,
        project_id: str | None = None,
        dataset: str = "fashionflow_raw",
    ) -> None:
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID", "de-project-502311")
        self.dataset = dataset
        self.client = bigquery.Client(project=self.project_id)

    def run_checks(self, table: str, checks: list[QualityCheck]) -> list[CheckResult]:
        """Run all checks against a table and return results."""
        full_table = f"{self.project_id}.{self.dataset}.{table}"
        results: list[CheckResult] = []
        now = datetime.utcnow().isoformat()

        # Get total row count once
        total = self._query_scalar(f"SELECT COUNT(*) FROM `{full_table}`")

        for check in checks:
            try:
                failed = self._execute_check(full_table, check, total)
                results.append(CheckResult(
                    table=table, check_type=check.check_type.value,
                    column=check.column, description=check.description,
                    passed=(failed == 0), failed_count=failed,
                    total_count=total, checked_at=now,
                ))
            except Exception as e:
                results.append(CheckResult(
                    table=table, check_type=check.check_type.value,
                    column=check.column, description=f"ERROR: {e}",
                    passed=False, failed_count=-1,
                    total_count=total, checked_at=now,
                ))

        return results

    def _execute_check(self, full_table: str, check: QualityCheck, total: int) -> int:
        """Execute a single check, returning the number of failures."""
        col = check.column

        if check.check_type == CheckType.NOT_NULL:
            return self._query_scalar(f"SELECT COUNTIF({col} IS NULL) FROM `{full_table}`")

        elif check.check_type == CheckType.UNIQUE:
            return self._query_scalar(
                f"SELECT COUNT(*) - COUNT(DISTINCT {col}) FROM `{full_table}`"
            )

        elif check.check_type == CheckType.ACCEPTED_VALUES:
            values = ", ".join(f"'{v}'" for v in check.params["values"])
            return self._query_scalar(
                f"SELECT COUNTIF({col} NOT IN ({values})) FROM `{full_table}`"
            )

        elif check.check_type == CheckType.ROW_COUNT_MIN:
            return 0 if total >= check.params["minimum"] else 1

        elif check.check_type == CheckType.NULL_THRESHOLD:
            null_count = self._query_scalar(f"SELECT COUNTIF({col} IS NULL) FROM `{full_table}`")
            null_pct = null_count / total if total > 0 else 0
            return 0 if null_pct <= check.params["max_pct"] else null_count

        elif check.check_type == CheckType.REFERENTIAL_INTEGRITY:
            ref = check.params
            ref_full = f"{self.project_id}.{self.dataset}.{ref['ref_table']}"
            return self._query_scalar(
                f"SELECT COUNT(*) FROM `{full_table}` c "
                f"WHERE NOT EXISTS (SELECT 1 FROM `{ref_full}` p WHERE p.{ref['ref_column']} = c.{col})"
            )

        elif check.check_type == CheckType.CUSTOM_SQL:
            return self._query_scalar(check.params["sql"])

        return 0

    def _query_scalar(self, sql: str) -> int:
        result = list(self.client.query(sql).result())
        return result[0][0] if result else 0

    def store_results(self, results: list[CheckResult], audit_dataset: str = "fashionflow_audit") -> None:
        """Write check results to the audit dataset."""
        table_id = f"{self.project_id}.{audit_dataset}.quality_check_results"
        rows = [
            {
                "table_name": r.table, "check_type": r.check_type,
                "column_name": r.column, "description": r.description,
                "passed": r.passed, "failed_count": r.failed_count,
                "total_count": r.total_count, "checked_at": r.checked_at,
            }
            for r in results
        ]
        errors = self.client.insert_rows_json(table_id, rows)
        if errors:
            raise RuntimeError(f"Failed to insert quality results: {errors}")

    def print_results(self, results: list[CheckResult]) -> None:
        """Pretty-print check results."""
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            col_str = f".{r.column}" if r.column else ""
            print(f"  [{status:4s}] {r.table}{col_str:20s} {r.description} (failed: {r.failed_count})")
