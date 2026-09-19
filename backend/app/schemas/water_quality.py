from datetime import datetime

from pydantic import BaseModel


class WaterQualityEvaluate(BaseModel):
    device_id: int
    evaluated_at: datetime | None = None


class WaterQualityResponse(BaseModel):
    id: int
    device_id: int

    ph: float | None
    turbidity: float | None
    tds: float | None
    temperature: float | None

    status: str
    reason: str

    evaluated_at: datetime

    class Config:
        from_attributes = True