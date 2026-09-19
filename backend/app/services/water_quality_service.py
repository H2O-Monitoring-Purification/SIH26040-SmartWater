from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.sensor import Sensor
from app.models.telemetry import SensorReading
from app.models.water_quality import WaterQualityResult

from app.services.alert_service import (
    create_alert,
    resolve_alerts_for_parameter,
)


# -------------------------------------------------------------------
# Latest sensor value
# -------------------------------------------------------------------

def _latest_value(
    db: Session,
    device_id: int,
    sensor_types: list[str],
) -> float | None:

    reading = db.scalar(
        select(SensorReading)
        .join(
            Sensor,
            Sensor.id == SensorReading.sensor_id,
        )
        .where(
            SensorReading.device_id == device_id,
            Sensor.sensor_type.in_(sensor_types),
            Sensor.is_active.is_(True),
        )
        .order_by(
            SensorReading.recorded_at.desc()
        )
        .limit(1)
    )

    if reading is None:
        return None

    return reading.value


# -------------------------------------------------------------------
# Evaluate water quality
# -------------------------------------------------------------------

def evaluate_water_quality(
    db: Session,
    device_id: int,
) -> WaterQualityResult:

    # ---------------------------------------------------------------
    # Validate device
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Get latest sensor readings
    # ---------------------------------------------------------------

    ph = _latest_value(
        db,
        device_id,
        ["ph", "pH"],
    )

    turbidity = _latest_value(
        db,
        device_id,
        ["turbidity", "ntu"],
    )

    tds = _latest_value(
        db,
        device_id,
        ["tds", "TDS"],
    )

    temperature = _latest_value(
        db,
        device_id,
        ["temperature", "temp"],
    )

    # ---------------------------------------------------------------
    # Check required data
    # ---------------------------------------------------------------

    missing: list[str] = []

    if ph is None:
        missing.append("pH")

    if turbidity is None:
        missing.append("Turbidity")

    if tds is None:
        missing.append("TDS")

    if missing:

        result = WaterQualityResult(
            device_id=device_id,
            pH=ph,
            turbidity=turbidity,
            tds=tds,
            temperature=temperature,
            is_safe=False,
            quality_status="insufficient_data",
            reason=(
                "Required sensor data unavailable: "
                + ", ".join(missing)
            ),
            evaluated_at=datetime.now(timezone.utc),
        )

        db.add(result)
        db.commit()
        db.refresh(result)

        # -----------------------------------------------------------
        # Data-quality alert
        # -----------------------------------------------------------

        create_alert(
            db=db,
            device_id=device_id,
            alert_type="data_quality",
            severity="warning",
            title="Insufficient Water Quality Data",
            message=(
                "Required sensor data unavailable: "
                + ", ".join(missing)
            ),
            parameter=None,
            measured_value=None,
            threshold_value=None,
        )

        return result

    # ---------------------------------------------------------------
    # Safe limits
    # ---------------------------------------------------------------

    problems: list[str] = []

    # pH limits
    if ph < 6.5:

        problems.append(
            f"pH too low: {ph} (minimum 6.5)"
        )

    elif ph > 8.5:

        problems.append(
            f"pH too high: {ph} (maximum 8.5)"
        )

    # Turbidity limit
    if turbidity > 5:

        problems.append(
            f"Turbidity too high: {turbidity} NTU "
            "(maximum 5 NTU)"
        )

    # TDS limit
    if tds > 500:

        problems.append(
            f"TDS too high: {tds} ppm "
            "(maximum 500 ppm)"
        )

    # ---------------------------------------------------------------
    # Parameter-specific alerts
    # ---------------------------------------------------------------

    # ---------------- TURBIDITY ----------------

    if turbidity > 5:

        create_alert(
            db=db,
            device_id=device_id,
            alert_type="water_quality",
            severity="critical",
            title="High Turbidity",
            message=(
                f"Turbidity is {turbidity} NTU. "
                "Maximum safe value is 5 NTU."
            ),
            parameter="turbidity",
            measured_value=turbidity,
            threshold_value=5,
        )

    else:

        resolve_alerts_for_parameter(
            db,
            device_id,
            "turbidity",
        )

    # ---------------- TDS ----------------

    if tds > 500:

        create_alert(
            db=db,
            device_id=device_id,
            alert_type="water_quality",
            severity="critical",
            title="High TDS",
            message=(
                f"TDS is {tds} ppm. "
                "Maximum safe value is 500 ppm."
            ),
            parameter="tds",
            measured_value=tds,
            threshold_value=500,
        )

    else:

        resolve_alerts_for_parameter(
            db,
            device_id,
            "tds",
        )

    # ---------------- pH ----------------

    if ph < 6.5:

        create_alert(
            db=db,
            device_id=device_id,
            alert_type="water_quality",
            severity="critical",
            title="Low pH",
            message=(
                f"pH is {ph}. "
                "Minimum safe value is 6.5."
            ),
            parameter="pH",
            measured_value=ph,
            threshold_value=6.5,
        )

    elif ph > 8.5:

        create_alert(
            db=db,
            device_id=device_id,
            alert_type="water_quality",
            severity="critical",
            title="High pH",
            message=(
                f"pH is {ph}. "
                "Maximum safe value is 8.5."
            ),
            parameter="pH",
            measured_value=ph,
            threshold_value=8.5,
        )

    else:

        resolve_alerts_for_parameter(
            db,
            device_id,
            "pH",
        )

    # ---------------------------------------------------------------
    # Determine overall quality status
    # ---------------------------------------------------------------

    if problems:

        quality_status = "unsafe"
        is_safe = False

        reason = "; ".join(problems)

    else:

        quality_status = "safe"
        is_safe = True

        reason = (
            "All configured quality parameters "
            "are within safe limits"
        )

    # ---------------------------------------------------------------
    # Store water-quality result
    # ---------------------------------------------------------------

    result = WaterQualityResult(
        device_id=device_id,
        pH=ph,
        turbidity=turbidity,
        tds=tds,
        temperature=temperature,
        is_safe=is_safe,
        quality_status=quality_status,
        reason=reason,
        evaluated_at=datetime.now(timezone.utc),
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return result