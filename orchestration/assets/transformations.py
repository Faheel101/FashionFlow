"""Dagster asset for dbt transformations — builds staging and mart models."""

import os
import subprocess
from pathlib import Path

import dagster as dg


PROJECT_DIR = Path(__file__).resolve().parent.parent.parent / "transformations"


@dg.asset(
    description="Run dbt transformations: staging views and fact tables in BigQuery.",
    group_name="transformations",
    deps=["raw_commerce_data", "raw_marketing_data", "raw_inventory_data"],
    tags={"layer": "transform"},
    kinds={"bigquery", "dbt"},
)
def dbt_models(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Execute dbt run and dbt test."""
    env = {**os.environ}

    # dbt run
    context.log.info("Running dbt models...")
    run_result = subprocess.run(
        ["dbt", "run", "--project-dir", str(PROJECT_DIR), "--profiles-dir", str(PROJECT_DIR)],
        capture_output=True, text=True, env=env,
    )
    context.log.info(run_result.stdout)
    if run_result.returncode != 0:
        context.log.error(run_result.stderr)
        raise dg.Failure(description="dbt run failed", metadata={"stderr": dg.MetadataValue.text(run_result.stderr)})

    # dbt test
    context.log.info("Running dbt tests...")
    test_result = subprocess.run(
        ["dbt", "test", "--project-dir", str(PROJECT_DIR), "--profiles-dir", str(PROJECT_DIR)],
        capture_output=True, text=True, env=env,
    )
    context.log.info(test_result.stdout)
    if test_result.returncode != 0:
        context.log.error(test_result.stderr)
        raise dg.Failure(description="dbt test failed", metadata={"stderr": dg.MetadataValue.text(test_result.stderr)})

    models_count = run_result.stdout.count(" OK ")
    tests_passed = test_result.stdout.count(" PASS ")

    return dg.MaterializeResult(
        metadata={
            "models_built": dg.MetadataValue.int(models_count),
            "tests_passed": dg.MetadataValue.int(tests_passed),
        }
    )
