from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TreatmentCycleCreate(BaseModel):
    source_volume_liters: float | None = None


class TreatmentCycleResponse(BaseModel):
    id: int
    device_id: int
    cycle_uid: str
    source_volume_liters: float | None
    purified_volume_liters: float | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    failure_reason: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )