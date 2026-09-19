from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services.device_heartbeat_service import (
    record_device_heartbeat,
)

from app.core.database import get_db
from app.schemas.device import (
    DeviceCreate,
    DeviceResponse,
    DeviceUpdate,
)
from app.services.device_service import (
    create_device,
    get_device,
    get_devices,
    update_device,
)

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_device(db, data)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[DeviceResponse],
)
def list_devices(
    db: Session = Depends(get_db),
):
    return get_devices(db)


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
)
def device_details(
    device_id: int,
    db: Session = Depends(get_db),
):
    device = get_device(db, device_id)

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return device


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
)
def update_device_details(
    device_id: int,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
):
    device = get_device(db, device_id)

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return update_device(db, device, data)

@router.post(
    "/{device_id}/heartbeat",
)
def device_heartbeat(
    device_id: int,
    db: Session = Depends(get_db),
):
    try:
        device = record_device_heartbeat(
            db,
            device_id,
        )

        return {
            "device_id": device.id,
            "device_uid": device.device_uid,
            "is_online": device.is_online,
            "last_seen_at": device.last_seen_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc