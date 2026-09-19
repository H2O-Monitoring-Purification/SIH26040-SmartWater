from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.treatment import TreatmentCycle


def start_treatment_cycle(
    db: Session,
    device_id: int,
    source_volume_liters: float | None = None,
) -> TreatmentCycle:
    """
    Start a new treatment cycle for a device.
    Only one active cycle is allowed per device.
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

    active_cycle = db.scalar(
        select(TreatmentCycle)
        .where(
            TreatmentCycle.device_id == device_id,
            TreatmentCycle.status == "started",
        )
        .order_by(
            TreatmentCycle.started_at.desc()
        )
        .limit(1)
    )

    if active_cycle is not None:
        raise ValueError(
            "Device already has an active treatment cycle"
        )

    cycle = TreatmentCycle(
        device_id=device_id,
        cycle_uid=f"TC-{uuid4().hex[:12].upper()}",
        source_volume_liters=source_volume_liters,
        purified_volume_liters=None,
        status="started",
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        failure_reason=None,
    )

    db.add(cycle)
    db.commit()
    db.refresh(cycle)

    return cycle


def get_treatment_cycle(
    db: Session,
    cycle_id: int,
) -> TreatmentCycle | None:
    """
    Get one treatment cycle by ID.
    """

    return db.scalar(
        select(TreatmentCycle).where(
            TreatmentCycle.id == cycle_id
        )
    )


def get_device_treatment_cycles(
    db: Session,
    device_id: int,
) -> list[TreatmentCycle]:
    """
    Get all treatment cycles for a device.
    """

    query = (
        select(TreatmentCycle)
        .where(
            TreatmentCycle.device_id == device_id
        )
        .order_by(
            TreatmentCycle.started_at.desc()
        )
    )

    return list(
        db.scalars(query).all()
    )


def complete_treatment_cycle(
    db: Session,
    cycle: TreatmentCycle,
    purified_volume_liters: float | None = None,
) -> TreatmentCycle:
    """
    Complete an active treatment cycle.
    """

    if cycle.status != "started":
        raise ValueError(
            "Only an active treatment cycle can be completed"
        )

    cycle.status = "completed"

    cycle.purified_volume_liters = (
        purified_volume_liters
    )

    cycle.completed_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(cycle)

    return cycle


def fail_treatment_cycle(
    db: Session,
    cycle: TreatmentCycle,
    failure_reason: str,
) -> TreatmentCycle:
    """
    Mark an active treatment cycle as failed.
    """

    if cycle.status != "started":
        raise ValueError(
            "Only an active treatment cycle can be failed"
        )

    if not failure_reason.strip():
        raise ValueError(
            "Failure reason is required"
        )

    cycle.status = "failed"

    cycle.failure_reason = (
        failure_reason.strip()
    )

    cycle.completed_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(cycle)

    return cycle