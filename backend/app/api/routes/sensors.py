from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sensor import (
    SensorCreate,
    SensorResponse,
    SensorUpdate,
)
from app.services.sensor_service import (
    create_sensor,
    get_sensor,
    get_sensors,
    update_sensor,
)

router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"],
)


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_sensor(
    data: SensorCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_sensor(db, data)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[SensorResponse],
)
def list_sensors(
    device_id: int | None = None,
    db: Session = Depends(get_db),
):
    return get_sensors(
        db,
        device_id,
    )


@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def sensor_details(
    sensor_id: int,
    db: Session = Depends(get_db),
):
    sensor = get_sensor(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    return sensor


@router.patch(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def update_sensor_details(
    sensor_id: int,
    data: SensorUpdate,
    db: Session = Depends(get_db),
):
    sensor = get_sensor(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    return update_sensor(
        db,
        sensor,
        data,
    )