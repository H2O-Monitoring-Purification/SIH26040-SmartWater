from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.devices import router as devices_router
from app.api.routes.sensors import router as sensors_router
from app.api.routes.telemetry import router as telemetry_router
from app.core.config import settings
from app.api.routes.alerts import router as alerts_router
from app.api.routes.treatment import router as treatment_router

from app.api.routes.water_quality import (
    router as water_quality_router,
)

from app.api.routes.filter_health import (
    router as filter_health_router,
)

from app.api.routes.maintenance import (
    router as maintenance_router,
)

from app.api.routes.dashboard import (
    router as dashboard_router,
)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Smart Water Purification and Quality Monitoring "
        "System for SIH26040"
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    devices_router,
    prefix="/api/v1",
)

app.include_router(
    sensors_router,
    prefix="/api/v1",
)

app.include_router(
    telemetry_router,
    prefix="/api/v1",
)

app.include_router(
    water_quality_router,
    prefix="/api/v1",
)

app.include_router(
    alerts_router,
    prefix="/api/v1",
)

app.include_router(
    treatment_router,
    prefix="/api/v1",
)

app.include_router(
    filter_health_router,
    prefix="/api/v1",
)

app.include_router(
    maintenance_router,
    prefix="/api/v1",
)

app.include_router(
    dashboard_router,
    prefix="/api/v1",
)

@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SIH26040 Backend",
    }