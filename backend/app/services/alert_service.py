from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.device import Device


def create_alert(
    db: Session,
    device_id: int,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    parameter: str | None = None,
    measured_value: float | None = None,
    threshold_value: float | None = None,
) -> Alert:

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

    existing_alert = db.scalar(
        select(Alert)
        .where(
            Alert.device_id == device_id,
            Alert.alert_type == alert_type,
            Alert.is_resolved.is_(False),
            Alert.parameter == parameter,
        )
        .order_by(
            Alert.created_at.desc()
        )
        .limit(1)
    )

    if existing_alert is not None:

        existing_alert.severity = severity
        existing_alert.message = message
        existing_alert.measured_value = measured_value
        existing_alert.threshold_value = threshold_value

        db.commit()
        db.refresh(existing_alert)

        return existing_alert

    alert = Alert(
        device_id=device_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=message,
        parameter=parameter,
        measured_value=measured_value,
        threshold_value=threshold_value,
        is_resolved=False,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


def resolve_alerts_for_parameter(
    db: Session,
    device_id: int,
    parameter: str,
) -> None:

    alerts = db.scalars(
        select(Alert).where(
            Alert.device_id == device_id,
            Alert.parameter == parameter,
            Alert.is_resolved.is_(False),
        )
    ).all()

    for alert in alerts:
        alert.is_resolved = True
        alert.resolved_at = datetime.now(
            timezone.utc
        )

    db.commit()


def get_alert(
    db: Session,
    alert_id: int,
) -> Alert | None:

    return db.scalar(
        select(Alert).where(
            Alert.id == alert_id
        )
    )


def get_device_alerts(
    db: Session,
    device_id: int,
    unresolved_only: bool = False,
) -> list[Alert]:

    query = (
        select(Alert)
        .where(
            Alert.device_id == device_id
        )
        .order_by(
            Alert.created_at.desc()
        )
    )

    if unresolved_only:
        query = query.where(
            Alert.is_resolved.is_(False)
        )

    return list(
        db.scalars(query).all()
    )


def resolve_alert(
    db: Session,
    alert: Alert,
) -> Alert:

    alert.is_resolved = True
    alert.resolved_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(alert)

    return alert