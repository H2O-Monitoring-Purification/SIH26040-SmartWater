from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.sensor import Sensor
from app.schemas.sensor import SensorCreate, SensorUpdate


def create_sensor(
    db: Session,
    data: SensorCreate,
) -> Sensor:

    device = db.scalar(
        select(Device).where(
            Device.id == data.device_id
        )
    )

    if device is None:
        raise ValueError("Device not found")

    existing_sensor = db.scalar(
        select(Sensor).where(
            Sensor.sensor_uid == data.sensor_uid
        )
    )

    if existing_sensor:
        raise ValueError(
            "Sensor UID is already registered"
        )

    sensor = Sensor(
        device_id=data.device_id,
        sensor_uid=data.sensor_uid,
        sensor_type=data.sensor_type,
        sensor_name=data.sensor_name,
        unit=data.unit,
        min_safe_value=data.min_safe_value,
        max_safe_value=data.max_safe_value,
        calibration_due_at=data.calibration_due_at,
        is_active=True,
    )

    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    return sensor


def get_sensor(
    db: Session,
    sensor_id: int,
) -> Sensor | None:

    return db.scalar(
        select(Sensor).where(
            Sensor.id == sensor_id
        )
    )


def get_sensors(
    db: Session,
    device_id: int | None = None,
) -> list[Sensor]:

    query = select(Sensor).order_by(Sensor.id)

    if device_id is not None:
        query = query.where(
            Sensor.device_id == device_id
        )

    return list(
        db.scalars(query).all()
    )


def update_sensor(
    db: Session,
    sensor: Sensor,
    data: SensorUpdate,
) -> Sensor:

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(sensor, field, value)

    db.commit()
    db.refresh(sensor)

    return sensor