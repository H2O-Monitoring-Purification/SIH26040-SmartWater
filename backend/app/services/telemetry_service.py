from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.sensor import Sensor
from app.models.telemetry import SensorReading
from app.schemas.telemetry import SensorReadingCreate
from app.services.alert_service import create_alert
from app.services.water_quality_service import evaluate_water_quality


def create_sensor_reading(
    db: Session,
    data: SensorReadingCreate,
) -> SensorReading:

    device = db.scalar(
        select(Device).where(
            Device.id == data.device_id,
            Device.is_active.is_(True),
        )
    )

    if device is None:
        raise ValueError(
            "Device not found or inactive"
        )

    sensor = db.scalar(
        select(Sensor).where(
            Sensor.id == data.sensor_id,
            Sensor.device_id == data.device_id,
            Sensor.is_active.is_(True),
        )
    )

    if sensor is None:
        raise ValueError(
            "Sensor not found, inactive, or does not belong to this device"
        )

    reading = SensorReading(
        sensor_id=data.sensor_id,
        device_id=data.device_id,
        value=data.value,
        unit=data.unit,
        recorded_at=(
            data.recorded_at
            if data.recorded_at is not None
            else datetime.now(timezone.utc)
        ),
        quality_status="received",
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    # ---------------------------------------------------------------
    # Automatically evaluate water quality
    # ---------------------------------------------------------------

    try:

        result = evaluate_water_quality(
            db,
            data.device_id,
        )

        reading.quality_status = "evaluated"

        db.commit()
        db.refresh(reading)

        # -----------------------------------------------------------
        # Unsafe water
        # -----------------------------------------------------------

        if result.quality_status == "unsafe":

            # Determine the primary failing parameter
            parameter = None
            measured_value = None
            threshold_value = None
            title = "Unsafe Water Quality"

            if (
                result.turbidity is not None
                and result.turbidity > 5
            ):
                parameter = "turbidity"
                measured_value = result.turbidity
                threshold_value = 5
                title = "High Turbidity"

            elif (
                result.tds is not None
                and result.tds > 500
            ):
                parameter = "tds"
                measured_value = result.tds
                threshold_value = 500
                title = "High TDS"

            elif (
                result.pH is not None
                and (
                    result.pH < 6.5
                    or result.pH > 8.5
                )
            ):
                parameter = "pH"
                measured_value = result.pH

                if result.pH < 6.5:
                    threshold_value = 6.5
                    title = "Low pH"
                else:
                    threshold_value = 8.5
                    title = "High pH"

            create_alert(
                db=db,
                device_id=data.device_id,
                alert_type="water_quality",
                severity="critical",
                title=title,
                message=(
                    result.reason
                    or "Water quality is outside safe limits."
                ),
                parameter=parameter,
                measured_value=measured_value,
                threshold_value=threshold_value,
            )

        # -----------------------------------------------------------
        # Insufficient data
        # -----------------------------------------------------------

        elif result.quality_status == "insufficient_data":

            create_alert(
                db=db,
                device_id=data.device_id,
                alert_type="sensor_data",
                severity="warning",
                title="Insufficient Sensor Data",
                message=(
                    result.reason
                    or "Required sensor data is unavailable."
                ),
            )

    except Exception:

        # Telemetry must not be lost if evaluation fails.
        reading.quality_status = "evaluation_failed"

        db.commit()
        db.refresh(reading)

    return reading


def get_latest_readings(
    db: Session,
    device_id: int,
) -> list[SensorReading]:

    sensors = db.scalars(
        select(Sensor)
        .where(
            Sensor.device_id == device_id,
            Sensor.is_active.is_(True),
        )
        .order_by(
            Sensor.id
        )
    ).all()

    results: list[SensorReading] = []

    for sensor in sensors:

        reading = db.scalar(
            select(SensorReading)
            .where(
                SensorReading.sensor_id == sensor.id,
                SensorReading.device_id == device_id,
            )
            .order_by(
                SensorReading.recorded_at.desc()
            )
            .limit(1)
        )

        if reading is not None:
            results.append(reading)

    return results


def get_reading_history(
    db: Session,
    device_id: int,
    limit: int = 100,
) -> list[SensorReading]:

    limit = max(
        1,
        min(limit, 1000),
    )

    readings = db.scalars(
        select(SensorReading)
        .where(
            SensorReading.device_id == device_id
        )
        .order_by(
            SensorReading.recorded_at.desc()
        )
        .limit(limit)
    ).all()

    return list(readings)