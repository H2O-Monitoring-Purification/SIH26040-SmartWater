from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.filter_health import FilterHealth
from app.models.maintenance import Maintenance
from app.models.system_event import SystemEvent


def create_system_event(
    db: Session,
    device_id: int | None,
    event_type: str,
    severity: str,
    message: str,
    source: str,
    event_metadata: str | None = None,
) -> SystemEvent:

    event = SystemEvent(
        device_id=device_id,
        event_type=event_type,
        severity=severity,
        message=message,
        source=source,
        event_metadata=event_metadata,
        occurred_at=datetime.now(timezone.utc),
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def create_maintenance(
    db: Session,
    device_id: int,
    maintenance_type: str,
    description: str,
    filter_health_id: int | None = None,
    performed_by: str | None = None,
    scheduled_at: datetime | None = None,
    notes: str | None = None,
) -> Maintenance:

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

    if filter_health_id is not None:
        filter_health = db.scalar(
            select(FilterHealth).where(
                FilterHealth.id == filter_health_id,
                FilterHealth.device_id == device_id,
            )
        )

        if filter_health is None:
            raise ValueError(
                "Filter not found for this device"
            )

    maintenance = Maintenance(
        device_id=device_id,
        filter_health_id=filter_health_id,
        maintenance_type=maintenance_type,
        description=description,
        performed_by=performed_by,
        status="scheduled"
        if scheduled_at is not None
        else "completed",
        scheduled_at=scheduled_at,
        performed_at=(
            datetime.now(timezone.utc)
            if scheduled_at is None
            else None
        ),
        notes=notes,
    )

    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)

    create_system_event(
        db=db,
        device_id=device_id,
        event_type="maintenance",
        severity="info",
        message=description,
        source="maintenance_service",
    )

    return maintenance


def get_maintenance(
    db: Session,
    maintenance_id: int,
) -> Maintenance | None:

    return db.scalar(
        select(Maintenance).where(
            Maintenance.id == maintenance_id
        )
    )


def get_device_maintenance(
    db: Session,
    device_id: int,
) -> list[Maintenance]:

    query = (
        select(Maintenance)
        .where(
            Maintenance.device_id == device_id
        )
        .order_by(
            Maintenance.created_at.desc()
        )
    )

    return list(
        db.scalars(query).all()
    )


def complete_maintenance(
    db: Session,
    maintenance: Maintenance,
    performed_by: str | None = None,
    next_due_at: datetime | None = None,
    notes: str | None = None,
) -> Maintenance:

    maintenance.status = "completed"
    maintenance.performed_at = datetime.now(
        timezone.utc
    )

    if performed_by is not None:
        maintenance.performed_by = performed_by

    if next_due_at is not None:
        maintenance.next_due_at = next_due_at

    if notes is not None:
        maintenance.notes = notes

    db.commit()
    db.refresh(maintenance)

    # If this maintenance belongs to a filter,
    # reset its health after service.
    if maintenance.filter_health_id is not None:

        filter_health = db.scalar(
            select(FilterHealth).where(
                FilterHealth.id
                == maintenance.filter_health_id
            )
        )

        if filter_health is not None:

            filter_health.last_service_at = (
                datetime.now(timezone.utc)
            )

            filter_health.health_status = "healthy"
            filter_health.replacement_required = False
            filter_health.replacement_reason = None

            db.commit()

    create_system_event(
        db=db,
        device_id=maintenance.device_id,
        event_type="maintenance_completed",
        severity="info",
        message=(
            f"Maintenance {maintenance.id} "
            "completed successfully"
        ),
        source="maintenance_service",
    )

    return maintenance