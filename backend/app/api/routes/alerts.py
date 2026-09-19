from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.alert import Alert
from app.models.device import Device
from app.services.alert_service import resolve_alert


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


class AlertResponse(BaseModel):
    id: int
    device_id: int
    sensor_id: Optional[int]

    alert_type: str
    severity: str

    title: str
    message: str

    parameter: Optional[str]
    measured_value: Optional[float]
    threshold_value: Optional[float]

    is_resolved: bool
    resolved_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


@router.get(
    "",
    response_model=list[AlertResponse],
)
def list_alerts(
    unresolved_only: bool = Query(
        default=False
    ),
    device_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = select(Alert)

    if device_id is not None:
        query = query.where(
            Alert.device_id == device_id
        )

    if unresolved_only:
        query = query.where(
            Alert.is_resolved.is_(False)
        )

    query = query.order_by(
        desc(Alert.created_at)
    )

    return list(
        db.scalars(query).all()
    )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = db.scalar(
        select(Alert).where(
            Alert.id == alert_id
        )
    )

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return alert


@router.get(
    "/device/{device_id}",
    response_model=list[AlertResponse],
)
def get_device_alerts(
    device_id: int,
    unresolved_only: bool = Query(
        default=False
    ),
    db: Session = Depends(get_db),
):
    device = db.scalar(
        select(Device).where(
            Device.id == device_id,
            Device.is_active.is_(True),
        )
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    query = (
        select(Alert)
        .where(
            Alert.device_id == device_id
        )
        .order_by(
            desc(Alert.created_at)
        )
    )

    if unresolved_only:
        query = query.where(
            Alert.is_resolved.is_(False)
        )

    return list(
        db.scalars(query).all()
    )


@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
)
def resolve_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = db.scalar(
        select(Alert).where(
            Alert.id == alert_id
        )
    )

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    if alert.is_resolved:
        return alert

    return resolve_alert(
        db,
        alert,
    )