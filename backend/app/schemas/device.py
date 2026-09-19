from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreate(BaseModel):
    device_uid: str = Field(min_length=3, max_length=100)
    device_name: str = Field(min_length=2, max_length=100)
    location_name: str = Field(min_length=2, max_length=150)

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    firmware_version: Optional[str] = Field(
        default=None,
        max_length=50,
    )


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    location_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    firmware_version: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    is_online: Optional[bool] = None
    is_active: Optional[bool] = None


class DeviceResponse(BaseModel):
    id: int
    device_uid: str
    device_name: str
    location_name: str

    latitude: Optional[float]
    longitude: Optional[float]

    firmware_version: Optional[str]

    is_online: bool
    is_active: bool

    last_seen_at: Optional[datetime]

    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True,
    )