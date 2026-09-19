from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SensorCreate(BaseModel):
    device_id: int
    sensor_uid: str = Field(min_length=3, max_length=100)
    sensor_type: str = Field(min_length=2, max_length=50)
    sensor_name: str = Field(min_length=2, max_length=100)
    unit: str = Field(min_length=1, max_length=30)

    min_safe_value: Optional[float] = None
    max_safe_value: Optional[float] = None

    calibration_due_at: Optional[datetime] = None


class SensorUpdate(BaseModel):
    sensor_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    unit: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    min_safe_value: Optional[float] = None
    max_safe_value: Optional[float] = None
    calibration_due_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class SensorResponse(BaseModel):
    id: int
    device_id: int
    sensor_uid: str
    sensor_type: str
    sensor_name: str
    unit: str

    min_safe_value: Optional[float]
    max_safe_value: Optional[float]

    calibration_due_at: Optional[datetime]

    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )