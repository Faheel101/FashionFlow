"""Dagster asset for dbt transformations — builds staging and mart models."""

import os
import subprocess
from pathlib import Path

import dagster as dg


PROJECT_DIR = Path(__file__).resolve().parent.parent.parent / "transformations"


@dg.asset(
    description="Run dbt transformations: staging views and fact tables in BigQuery.",
    group_name="transformations",
    deps=["raw_commerce_data"],
    tags={"layer": "transform"},
    kinds={"bigquery", "dbt"},
)
def dbt_models(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Execute dbt run and dbt test."""
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    env = {**os.environ}
    if credentials_path:
        env["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    # dbt run
    context.log.info("Running dbt models...")
    run_result = subprocess.run(
        [
            "dbt", "run",
            "--project-dir", str(PROJECT_DIR),
            "--profiles-dir", str(PROJECT_DIR),
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    context.log.info(run_result.stdout)
    if run_result.returncode != 0:
        context.log.error(run_result.stderr)
        raise dg.Failure(
            description="dbt run failed",
            metadata={"stderr": dg.MetadataValue.text(run_result.stderr)},
        )

    # dbt test
    context.log.info("Running dbt tests...")
    test_result = subprocess.run(
        [
            "dbt", "test",
            "--project-dir", str(PROJECT_DIR),
            "--profiles-dir", str(PROJECT_DIR),
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    context.log.info(test_result.stdout)
    if test_result.returncode != 0:
        context.log.error(test_result.stderr)
        raise dg.Failure(
            description="dbt test failed",
            metadata={"stderr": dg.MetadataValue.text(test_result.stderr)},
        )

    # Parse results from stdout
    models_count = run_result.stdout.count(" OK ")
    tests_passed = test_result.stdout.count(" PASS ")

    return dg.MaterializeResult(
        metadata={
            "models_built": dg.MetadataValue.int(models_count),
            "tests_passed": dg.MetadataValue.int(tests_passed),
            "dbt_run_output": dg.MetadataValue.text(run_result.stdout[-2000:]),
            "dbt_test_output": dg.MetadataValue.text(test_result.stdout[-2000:]),
        }
    )
