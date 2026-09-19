from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.system_event import SystemEvent


def record_device_heartbeat(
    db: Session,
    device_id: int,
) -> Device:
    """
    Mark a device as online and update its last-seen timestamp.
    """

    device = db.scalar(
        select(Device).where(
            Device.id == device_id,
            Device.is_active.is_(True),
        )
    )

    if device is None:
        raise ValueError(
            "Device not found or inactive"
        )

    was_offline = not device.is_online

    now = datetime.now(timezone.utc)

    device.is_online = True
    device.last_seen_at = now
    device.updated_at = now

    db.commit()
    db.refresh(device)

    if was_offline:
        event = SystemEvent(
            device_id=device.id,
            event_type="device_online",
            severity="info",
            message=(
                f"Device {device.device_uid} is online"
            ),
            source="heartbeat",
            occurred_at=now,
        )

        db.add(event)
        db.commit()

    return device


def mark_device_offline(
    db: Session,
    device_id: int,
) -> Device:
    """
    Manually mark a device as offline.
    """

    device = db.scalar(
        select(Device).where(
            Device.id == device_id,
            Device.is_active.is_(True),
        )
    )

    if device is None:
        raise ValueError(
            "Device not found or inactive"
        )

    now = datetime.now(timezone.utc)

    device.is_online = False
    device.updated_at = now

    db.commit()
    db.refresh(device)

    event = SystemEvent(
        device_id=device.id,
        event_type="device_offline",
        severity="warning",
        message=(
            f"Device {device.device_uid} is offline"
        ),
        source="heartbeat",
        occurred_at=now,
    )

    db.add(event)
    db.commit()

    return device