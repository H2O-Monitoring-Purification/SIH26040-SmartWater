from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.device import Device
from app.models.filter_health import FilterHealth
from app.models.maintenance import Maintenance
from app.models.telemetry import SensorReading
from app.models.treatment import TreatmentCycle
from app.models.water_quality import WaterQualityResult


def get_dashboard(
    db: Session,
    device_id: int,
) -> dict:
    """
    Return the complete SmartWater dashboard state
    for one device.
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

    # ---------------------------------------------------------
    # Latest water-quality evaluation
    # ---------------------------------------------------------

    quality = db.scalar(
        select(WaterQualityResult)
        .where(
            WaterQualityResult.device_id == device_id
        )
        .order_by(
            WaterQualityResult.evaluated_at.desc()
        )
        .limit(1)
    )

    # ---------------------------------------------------------
    # Active alerts
    # ---------------------------------------------------------

    active_alerts = list(
        db.scalars(
            select(Alert)
            .where(
                Alert.device_id == device_id,
                Alert.is_resolved.is_(False),
            )
            .order_by(
                Alert.created_at.desc()
            )
            .limit(20)
        ).all()
    )

    # ---------------------------------------------------------
    # Active treatment cycle
    # ---------------------------------------------------------

    treatment = db.scalar(
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

    # ---------------------------------------------------------
    # Latest filter health record
    # ---------------------------------------------------------

    filter_health = db.scalar(
        select(FilterHealth)
        .where(
            FilterHealth.device_id == device_id
        )
        .order_by(
            FilterHealth.updated_at.desc()
        )
        .limit(1)
    )

    # ---------------------------------------------------------
    # Latest maintenance
    # ---------------------------------------------------------

    maintenance = db.scalar(
        select(Maintenance)
        .where(
            Maintenance.device_id == device_id
        )
        .order_by(
            Maintenance.created_at.desc()
        )
        .limit(1)
    )

    # ---------------------------------------------------------
    # Telemetry count
    # ---------------------------------------------------------

    reading_count = db.scalar(
        select(
            func.count(SensorReading.id)
        ).where(
            SensorReading.device_id == device_id
        )
    )

    # ---------------------------------------------------------
    # Water Quality
    # ---------------------------------------------------------

    if quality is None:

        quality_data = {
            "status": "no_data",
            "is_safe": False,
            "reason": (
                "No water quality evaluation available"
            ),
            "pH": None,
            "turbidity": None,
            "tds": None,
            "temperature": None,
            "evaluated_at": None,
        }

    else:

        quality_data = {
            "status": quality.quality_status,
            "is_safe": quality.is_safe,
            "reason": quality.reason,
            "pH": quality.pH,
            "turbidity": quality.turbidity,
            "tds": quality.tds,
            "temperature": quality.temperature,
            "evaluated_at": quality.evaluated_at,
        }

    # ---------------------------------------------------------
    # Alerts
    # ---------------------------------------------------------

    alerts_data = [
        {
            "id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "parameter": alert.parameter,
            "measured_value": alert.measured_value,
            "threshold_value": alert.threshold_value,
            "created_at": alert.created_at,
        }
        for alert in active_alerts
    ]

    # ---------------------------------------------------------
    # Treatment
    # ---------------------------------------------------------

    if treatment is None:

        treatment_data = {
            "id": None,
            "status": "idle",
            "cycle_uid": None,
            "source_volume_liters": None,
            "started_at": None,
        }

    else:

        treatment_data = {
            "id": treatment.id,
            "status": treatment.status,
            "cycle_uid": treatment.cycle_uid,
            "source_volume_liters": (
                treatment.source_volume_liters
            ),
            "started_at": treatment.started_at,
        }

    # ---------------------------------------------------------
    # Filter Health
    # ---------------------------------------------------------

    if filter_health is None:

        filter_data = {
            "status": "unknown",
            "filter_type": None,
            "remaining_days": None,
            "flow_rate_lpm": None,
            "pressure_drop": None,
            "replacement_required": False,
            "replacement_reason": None,
        }

    else:

        filter_data = {
            "status": filter_health.health_status,
            "filter_type": filter_health.filter_type,
            "remaining_days": (
                filter_health.estimated_remaining_days
            ),
            "flow_rate_lpm": filter_health.flow_rate_lpm,
            "pressure_drop": filter_health.pressure_drop,
            "replacement_required": (
                filter_health.replacement_required
            ),
            "replacement_reason": (
                filter_health.replacement_reason
            ),
        }

    # ---------------------------------------------------------
    # Maintenance
    # ---------------------------------------------------------

    if maintenance is None:

        maintenance_data = None

    else:

        maintenance_data = {
            "id": maintenance.id,
            "type": maintenance.maintenance_type,
            "description": maintenance.description,
            "status": maintenance.status,
            "scheduled_at": maintenance.scheduled_at,
            "performed_at": maintenance.performed_at,
            "next_due_at": maintenance.next_due_at,
        }

    # ---------------------------------------------------------
    # Final Dashboard
    # ---------------------------------------------------------

    return {
        "device": {
            "id": device.id,
            "uid": device.device_uid,
            "name": device.device_name,
            "location": device.location_name,
            "latitude": device.latitude,
            "longitude": device.longitude,
            "firmware_version": device.firmware_version,
            "is_online": device.is_online,
            "last_seen_at": device.last_seen_at,
        },

        "water_quality": quality_data,

        "alerts": {
            "active_count": len(active_alerts),
            "items": alerts_data,
        },

        "treatment": treatment_data,

        "filter": filter_data,

        "maintenance": maintenance_data,

        "telemetry": {
            "total_readings": reading_count or 0,
        },
    }