from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.maintenance import Maintenance
from app.models.system_event import SystemEvent
from app.services.maintenance_service import (
    create_maintenance,
    complete_maintenance,
    get_maintenance,
    get_device_maintenance,
)


router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"],
)


class MaintenanceCreateRequest(BaseModel):
    maintenance_type: str
    description: str
    filter_health_id: Optional[int] = None
    performed_by: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None


class MaintenanceCompleteRequest(BaseModel):
    performed_by: Optional[str] = None
    next_due_at: Optional[datetime] = None
    notes: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: int
    device_id: int
    filter_health_id: Optional[int]

    maintenance_type: str
    description: str
    performed_by: Optional[str]

    status: str

    scheduled_at: Optional[datetime]
    performed_at: Optional[datetime]
    next_due_at: Optional[datetime]

    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class SystemEventResponse(BaseModel):
    id: int
    device_id: Optional[int]

    event_type: str
    severity: str
    message: str
    source: str
    event_metadata: Optional[str]

    occurred_at: datetime
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


@router.post(
    "/devices/{device_id}",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_device_maintenance(
    device_id: int,
    data: MaintenanceCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        return create_maintenance(
            db=db,
            device_id=device_id,
            maintenance_type=data.maintenance_type,
            description=data.description,
            filter_health_id=data.filter_health_id,
            performed_by=data.performed_by,
            scheduled_at=data.scheduled_at,
            notes=data.notes,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{maintenance_id}",
    response_model=MaintenanceResponse,
)
def get_maintenance_record(
    maintenance_id: int,
    db: Session = Depends(get_db),
):
    maintenance = get_maintenance(
        db,
        maintenance_id,
    )

    if maintenance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )

    return maintenance


@router.get(
    "/devices/{device_id}",
    response_model=list[MaintenanceResponse],
)
def get_device_maintenance_records(
    device_id: int,
    db: Session = Depends(get_db),
):
    return get_device_maintenance(
        db,
        device_id,
    )


@router.patch(
    "/{maintenance_id}/complete",
    response_model=MaintenanceResponse,
)
def complete_maintenance_record(
    maintenance_id: int,
    data: MaintenanceCompleteRequest,
    db: Session = Depends(get_db),
):
    maintenance = get_maintenance(
        db,
        maintenance_id,
    )

    if maintenance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )

    try:
        return complete_maintenance(
            db=db,
            maintenance=maintenance,
            performed_by=data.performed_by,
            next_due_at=data.next_due_at,
            notes=data.notes,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/events/device/{device_id}",
    response_model=list[SystemEventResponse],
)
def get_device_system_events(
    device_id: int,
    db: Session = Depends(get_db),
):
    events = db.scalars(
        select(SystemEvent)
        .where(
            SystemEvent.device_id == device_id
        )
        .order_by(
            desc(SystemEvent.occurred_at)
        )
    ).all()

    return list(events)


@router.get(
    "/events",
    response_model=list[SystemEventResponse],
)
def get_system_events(
    db: Session = Depends(get_db),
):
    events = db.scalars(
        select(SystemEvent)
        .order_by(
            desc(SystemEvent.occurred_at)
        )
        .limit(100)
    ).all()

    return list(events)