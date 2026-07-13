"""Sample asset to verify Dagster setup.

Remove this file after confirming the Dagster UI loads and the asset executes.
"""

import dagster as dg


@dg.asset(
    description="Sample asset to verify Dagster is configured correctly.",
    tags={"layer": "test"},
)
def sample_asset() -> str:
    """Return a verification message."""
    return "FashionFlow Dagster setup verified!"