"""Marketing endpoints for the FashionFlow Commerce API."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from source_system.api.dependencies import (
    PaginationParams,
    build_paginated_response,
    get_db,
    get_pagination,
    get_updated_since,
)
from source_system.api.schemas_v2 import (
    AdResponse,
    AdSetResponse,
    CampaignResponse,
    DailyPerformanceResponse,
)
from source_system.database.marketing_models import Ad, AdSet, Campaign, DailyPerformance

router = APIRouter(prefix="/marketing", tags=["Marketing"])


# ── Campaigns ────────────────────────────────────────────────────────────────

@router.get("/campaigns", response_model=dict)
def list_campaigns(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    platform: str | None = Query(default=None, description="Filter by platform"),
    status: str | None = Query(default=None, description="Filter by status"),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Campaign)
    if updated_since:
        query = query.filter(Campaign.updated_at > updated_since)
    if platform:
        query = query.filter(Campaign.platform == platform)
    if status:
        query = query.filter(Campaign.status == status)
    total = query.count()
    rows = query.order_by(Campaign.id).offset(pagination.offset).limit(pagination.page_size).all()
    data = [CampaignResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    row = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return CampaignResponse.model_validate(row)


# ── Ad Sets ──────────────────────────────────────────────────────────────────

@router.get("/ad-sets", response_model=dict)
def list_ad_sets(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    campaign_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(AdSet)
    if updated_since:
        query = query.filter(AdSet.updated_at > updated_since)
    if campaign_id is not None:
        query = query.filter(AdSet.campaign_id == campaign_id)
    if status:
        query = query.filter(AdSet.status == status)
    total = query.count()
    rows = query.order_by(AdSet.id).offset(pagination.offset).limit(pagination.page_size).all()
    data = [AdSetResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/ad-sets/{ad_set_id}", response_model=AdSetResponse)
def get_ad_set(ad_set_id: int, db: Session = Depends(get_db)):
    row = db.query(AdSet).filter(AdSet.id == ad_set_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Ad set not found")
    return AdSetResponse.model_validate(row)


# ── Ads ──────────────────────────────────────────────────────────────────────

@router.get("/ads", response_model=dict)
def list_ads(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    ad_set_id: int | None = Query(default=None),
    ad_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Ad)
    if updated_since:
        query = query.filter(Ad.updated_at > updated_since)
    if ad_set_id is not None:
        query = query.filter(Ad.ad_set_id == ad_set_id)
    if ad_type:
        query = query.filter(Ad.ad_type == ad_type)
    if status:
        query = query.filter(Ad.status == status)
    total = query.count()
    rows = query.order_by(Ad.id).offset(pagination.offset).limit(pagination.page_size).all()
    data = [AdResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/ads/{ad_id}", response_model=AdResponse)
def get_ad(ad_id: int, db: Session = Depends(get_db)):
    row = db.query(Ad).filter(Ad.id == ad_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Ad not found")
    return AdResponse.model_validate(row)


# ── Daily Performance ────────────────────────────────────────────────────────

@router.get("/daily-performance", response_model=dict)
def list_daily_performance(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    ad_id: int | None = Query(default=None),
    date_from: str | None = Query(default=None, description="YYYY-MM-DD"),
    date_to: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(DailyPerformance)
    if updated_since:
        query = query.filter(DailyPerformance.updated_at > updated_since)
    if ad_id is not None:
        query = query.filter(DailyPerformance.ad_id == ad_id)
    if date_from:
        query = query.filter(DailyPerformance.date >= date_from)
    if date_to:
        query = query.filter(DailyPerformance.date <= date_to)
    total = query.count()
    rows = query.order_by(DailyPerformance.id).offset(pagination.offset).limit(pagination.page_size).all()
    data = [DailyPerformanceResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)
