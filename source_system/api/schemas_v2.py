"""Pydantic schemas for marketing and inventory API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


# ── Marketing ────────────────────────────────────────────────────────────────

class CampaignResponse(TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    platform: str
    objective: str
    status: str
    daily_budget: float
    total_budget: float
    start_date: str
    end_date: str | None = None


class AdSetResponse(TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    id: int
    campaign_id: int
    name: str
    targeting_gender: str | None = None
    targeting_age_min: int | None = None
    targeting_age_max: int | None = None
    targeting_interests: str | None = None
    daily_budget: float
    bid_strategy: str
    status: str


class AdResponse(TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ad_set_id: int
    name: str
    ad_type: str
    headline: str
    description: str | None = None
    call_to_action: str
    destination_url: str
    status: str


class DailyPerformanceResponse(TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ad_id: int
    date: str
    impressions: int
    clicks: int
    spend: float
    ctr: float
    cpc: float
    purchases: int
    revenue: float


# ── Inventory ────────────────────────────────────────────────────────────────

class InventorySnapshotResponse(TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    snapshot_date: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    unit_cost: float
    total_value: float
    warehouse_location: str


class InventoryMovementResponse(TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    movement_type: str
    quantity: int
    unit_cost: float
    total_cost: float
    reference_id: str | None = None
    warehouse_location: str
    notes: str | None = None
    movement_date: str
