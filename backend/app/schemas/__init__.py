from app.schemas.auth import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

from app.schemas.device import (
    DeviceCreate,
    DeviceResponse,
    DeviceUpdate,
)

from app.schemas.sensor import (
    SensorCreate,
    SensorResponse,
    SensorUpdate,
)

from app.schemas.telemetry import (
    LatestReadingResponse,
    SensorReadingCreate,
    SensorReadingResponse,
    TelemetryHistoryResponse,
)

__all__ = [
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "TokenResponse",

    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",

    "SensorCreate",
    "SensorUpdate",
    "SensorResponse",

    "SensorReadingCreate",
    "SensorReadingResponse",
    "LatestReadingResponse",
    "TelemetryHistoryResponse",
]