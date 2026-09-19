from datetime import datetime

from pydantic import BaseModel, Field


class SensorReadingCreate(BaseModel):
    sensor_id: int
    device_id: int

    value: float
    unit: str = Field(min_length=1, max_length=30)

    recorded_at: datetime

    quality_status: str | None = Field(
        default=None,
        max_length=30,
    )


class SensorReadingResponse(BaseModel):
    id: int
    sensor_id: int
    device_id: int

    value: float
    unit: str

    recorded_at: datetime
    created_at: datetime

    quality_status: str | None


class LatestReadingResponse(BaseModel):
    sensor_id: int
    sensor_type: str
    sensor_name: str

    value: float
    unit: str

    recorded_at: datetime

    quality_status: str | None


class TelemetryHistoryResponse(BaseModel):
    readings: list[SensorReadingResponse]
    total: int