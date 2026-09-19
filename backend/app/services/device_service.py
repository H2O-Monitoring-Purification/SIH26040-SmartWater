from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate


def create_device(
    db: Session,
    data: DeviceCreate,
) -> Device:
    existing_device = db.scalar(
        select(Device).where(
            Device.device_uid == data.device_uid
        )
    )

    if existing_device:
        raise ValueError("Device UID is already registered")

    device = Device(
        device_uid=data.device_uid,
        device_name=data.device_name,
        location_name=data.location_name,
        latitude=data.latitude,
        longitude=data.longitude,
        firmware_version=data.firmware_version,
        is_online=False,
        is_active=True,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


def get_device(
    db: Session,
    device_id: int,
) -> Device | None:
    return db.scalar(
        select(Device).where(Device.id == device_id)
    )


def get_devices(
    db: Session,
) -> list[Device]:
    return list(
        db.scalars(
            select(Device).order_by(Device.id)
        ).all()
    )


def update_device(
    db: Session,
    device: Device,
    data: DeviceUpdate,
) -> Device:
    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)

    return device


def mark_device_online(
    db: Session,
    device: Device,
) -> Device:
    device.is_online = True
    device.last_seen_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(device)

    return device