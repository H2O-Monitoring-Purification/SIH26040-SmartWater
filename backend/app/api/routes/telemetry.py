from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device
from app.schemas.telemetry import (
    LatestReadingResponse,
    SensorReadingCreate,
    SensorReadingResponse,
    TelemetryHistoryResponse,
)
from app.services.telemetry_service import (
    create_sensor_reading,
    get_latest_readings,
    get_reading_history,
)


router = APIRouter(
    prefix="/telemetry",
    tags=["Telemetry"],
)


@router.post(
    "/readings",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_reading(
    data: SensorReadingCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_sensor_reading(
            db,
            data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/devices/{device_id}/latest",
    response_model=list[LatestReadingResponse],
)
def latest_readings(
    device_id: int,
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

    return get_latest_readings(
        db,
        device_id,
    )


@router.get(
    "/devices/{device_id}/history",
    response_model=TelemetryHistoryResponse,
)
def telemetry_history(
    device_id: int,
    limit: int = 100,
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

    readings = get_reading_history(
        db,
        device_id,
        limit,
    )

    return {
        "readings": readings,
        "total": len(readings),
    }