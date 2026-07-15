"""Inventory endpoints for the FashionFlow Commerce API."""

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
    InventoryMovementResponse,
    InventorySnapshotResponse,
)
from source_system.database.inventory_models import InventoryMovement, InventorySnapshot

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ── Snapshots ────────────────────────────────────────────────────────────────

@router.get("/snapshots", response_model=dict)
def list_snapshots(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    product_id: int | None = Query(default=None),
    warehouse_location: str | None = Query(default=None),
    snapshot_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(InventorySnapshot)
    if updated_since:
        query = query.filter(InventorySnapshot.updated_at > updated_since)
    if product_id is not None:
        query = query.filter(InventorySnapshot.product_id == product_id)
    if warehouse_location:
        query = query.filter(InventorySnapshot.warehouse_location == warehouse_location)
    if snapshot_date:
        query = query.filter(InventorySnapshot.snapshot_date == snapshot_date)
    total = query.count()
    rows = query.order_by(InventorySnapshot.id).offset(pagination.offset).limit(pagination.page_size).all()
    data = [InventorySnapshotResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/snapshots/{snapshot_id}", response_model=InventorySnapshotResponse)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    row = db.query(InventorySnapshot).filter(InventorySnapshot.id == snapshot_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return InventorySnapshotResponse.model_validate(row)


# ── Movements ────────────────────────────────────────────────────────────────

@router.get("/movements", response_model=dict)
def list_movements(
    pagination: PaginationParams = Depends(get_pagination),
    updated_since: datetime | None = Depends(get_updated_since),
    product_id: int | None = Query(default=None),
    movement_type: str | None = Query(default=None),
    warehouse_location: str | None = Query(default=None),
    date_from: str | None = Query(default=None, description="YYYY-MM-DD"),
    date_to: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(InventoryMovement)
    if updated_since:
        query = query.filter(InventoryMovement.updated_at > updated_since)
    if product_id is not None:
        query = query.filter(InventoryMovement.product_id == product_id)
    if movement_type:
        query = query.filter(InventoryMovement.movement_type == movement_type)
    if warehouse_location:
        query = query.filter(InventoryMovement.warehouse_location == warehouse_location)
    if date_from:
        query = query.filter(InventoryMovement.movement_date >= date_from)
    if date_to:
        query = query.filter(InventoryMovement.movement_date <= date_to)
    total = query.count()
    rows = query.order_by(InventoryMovement.id).offset(pagination.offset).limit(pagination.page_size).all()
    data = [InventoryMovementResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated_response(data, total, pagination)


@router.get("/movements/{movement_id}", response_model=InventoryMovementResponse)
def get_movement(movement_id: int, db: Session = Depends(get_db)):
    row = db.query(InventoryMovement).filter(InventoryMovement.id == movement_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Movement not found")
    return InventoryMovementResponse.model_validate(row)
