"""FashionFlow — Dagster definitions.

This is the main entry point for the Dagster project.
All assets, jobs, resources, schedules, and sensors are registered here.
"""

import dagster as dg

from orchestration.assets.sample import sample_asset


defs = dg.Definitions(
    assets=[sample_asset],
    jobs=[],
    schedules=[],
    sensors=[],
    resources={},
)