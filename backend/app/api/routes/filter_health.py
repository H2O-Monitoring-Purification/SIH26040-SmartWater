from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.filter_health_service import (
    create_filter,
    get_filter,
    get_device_filters,
    update_filter_health,
    service_filter,
)


router = APIRouter(
    prefix="/filter-health",
    tags=["Filter Health"],
)


class FilterCreateRequest(BaseModel):
    filter_type: str
    filter_uid: Optional[str] = None
    expected_life_days: Optional[int] = None


class FilterHealthUpdateRequest(BaseModel):
    flow_rate_lpm: Optional[float] = None
    pressure_drop: Optional[float] = None
    estimated_remaining_days: Optional[int] = None


class FilterHealthResponse(BaseModel):
    id: int
    device_id: int
    filter_type: str
    filter_uid: Optional[str]

    installed_at: Optional[datetime]
    last_service_at: Optional[datetime]

    expected_life_days: Optional[int]
    estimated_remaining_days: Optional[int]

    flow_rate_lpm: Optional[float]
    pressure_drop: Optional[float]

    health_status: str
    replacement_required: bool
    replacement_reason: Optional[str]

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


@router.post(
    "/devices/{device_id}",
    response_model=FilterHealthResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_device_filter(
    device_id: int,
    data: FilterCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        return create_filter(
            db=db,
            device_id=device_id,
            filter_type=data.filter_type,
            filter_uid=data.filter_uid,
            expected_life_days=data.expected_life_days,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{filter_id}",
    response_model=FilterHealthResponse,
)
def get_filter_health(
    filter_id: int,
    db: Session = Depends(get_db),
):
    filter_health = get_filter(
        db,
        filter_id,
    )

    if filter_health is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found",
        )

    return filter_health


@router.get(
    "/devices/{device_id}",
    response_model=list[FilterHealthResponse],
)
def get_device_filter_health(
    device_id: int,
    db: Session = Depends(get_db),
):
    return get_device_filters(
        db,
        device_id,
    )


@router.patch(
    "/{filter_id}",
    response_model=FilterHealthResponse,
)
def update_filter(
    filter_id: int,
    data: FilterHealthUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        return update_filter_health(
            db=db,
            filter_id=filter_id,
            flow_rate_lpm=data.flow_rate_lpm,
            pressure_drop=data.pressure_drop,
            estimated_remaining_days=data.estimated_remaining_days,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{filter_id}/service",
    response_model=FilterHealthResponse,
)
def service_filter_endpoint(
    filter_id: int,
    db: Session = Depends(get_db),
):
    try:
        return service_filter(
            db,
            filter_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc