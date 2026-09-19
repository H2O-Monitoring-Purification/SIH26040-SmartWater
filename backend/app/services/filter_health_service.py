from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.filter_health import FilterHealth


def create_filter(
    db: Session,
    device_id: int,
    filter_type: str,
    filter_uid: str | None = None,
    expected_life_days: int | None = None,
) -> FilterHealth:

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

    if filter_uid:
        existing = db.scalar(
            select(FilterHealth).where(
                FilterHealth.filter_uid == filter_uid
            )
        )

        if existing is not None:
            raise ValueError(
                "Filter UID already exists"
            )

    now = datetime.now(timezone.utc)

    filter_health = FilterHealth(
        device_id=device_id,
        filter_type=filter_type,
        filter_uid=filter_uid,
        installed_at=now,
        expected_life_days=expected_life_days,
        estimated_remaining_days=expected_life_days,
        health_status="healthy",
        replacement_required=False,
    )

    db.add(filter_health)
    db.commit()
    db.refresh(filter_health)

    return filter_health


def get_filter(
    db: Session,
    filter_id: int,
) -> FilterHealth | None:

    return db.scalar(
        select(FilterHealth).where(
            FilterHealth.id == filter_id
        )
    )


def get_device_filters(
    db: Session,
    device_id: int,
) -> list[FilterHealth]:

    query = (
        select(FilterHealth)
        .where(
            FilterHealth.device_id == device_id
        )
        .order_by(
            FilterHealth.updated_at.desc()
        )
    )

    return list(
        db.scalars(query).all()
    )


def update_filter_health(
    db: Session,
    filter_id: int,
    flow_rate_lpm: float | None = None,
    pressure_drop: float | None = None,
    estimated_remaining_days: int | None = None,
) -> FilterHealth:

    filter_health = get_filter(
        db,
        filter_id,
    )

    if filter_health is None:
        raise ValueError(
            "Filter not found"
        )

    if flow_rate_lpm is not None:
        filter_health.flow_rate_lpm = flow_rate_lpm

    if pressure_drop is not None:
        filter_health.pressure_drop = pressure_drop

    if estimated_remaining_days is not None:
        filter_health.estimated_remaining_days = (
            estimated_remaining_days
        )

    # Determine filter condition.
    reasons = []

    if (
        filter_health.estimated_remaining_days
        is not None
        and filter_health.estimated_remaining_days <= 0
    ):
        reasons.append(
            "Expected filter life exhausted"
        )

    if (
        filter_health.pressure_drop is not None
        and filter_health.pressure_drop >= 2.0
    ):
        reasons.append(
            "High pressure drop detected"
        )

    if (
        filter_health.flow_rate_lpm is not None
        and filter_health.flow_rate_lpm <= 1.0
    ):
        reasons.append(
            "Low flow rate detected"
        )

    if reasons:

        filter_health.health_status = "replacement_required"
        filter_health.replacement_required = True
        filter_health.replacement_reason = "; ".join(
            reasons
        )

    else:

        filter_health.health_status = "healthy"
        filter_health.replacement_required = False
        filter_health.replacement_reason = None

    filter_health.updated_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(filter_health)

    return filter_health


def service_filter(
    db: Session,
    filter_id: int,
) -> FilterHealth:

    filter_health = get_filter(
        db,
        filter_id,
    )

    if filter_health is None:
        raise ValueError(
            "Filter not found"
        )

    now = datetime.now(timezone.utc)

    filter_health.last_service_at = now
    filter_health.health_status = "healthy"
    filter_health.replacement_required = False
    filter_health.replacement_reason = None
    filter_health.updated_at = now

    db.commit()
    db.refresh(filter_health)

    return filter_health