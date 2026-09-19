from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device
from app.models.water_quality import WaterQualityResult
from app.schemas.water_quality import (
    WaterQualityEvaluate,
    WaterQualityResponse,
)
from app.services.water_quality_service import (
    evaluate_water_quality,
)


router = APIRouter(
    prefix="/water-quality",
    tags=["Water Quality"],
)


@router.post(
    "/evaluate/{device_id}",
    response_model=WaterQualityResponse,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_device_water_quality(
    device_id: int,
    data: WaterQualityEvaluate | None = None,
    db: Session = Depends(get_db),
):
    device = db.scalar(
        select(Device).where(
            Device.id == device_id,
            Device.is_active.is_(True),
        )
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    try:
        return evaluate_water_quality(
            db,
            device_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/devices/{device_id}/latest",
    response_model=WaterQualityResponse,
)
def latest_water_quality(
    device_id: int,
    db: Session = Depends(get_db),
):
    device = db.scalar(
        select(Device).where(
            Device.id == device_id,
            Device.is_active.is_(True),
        )
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    result = db.scalar(
        select(WaterQualityResult)
        .where(
            WaterQualityResult.device_id == device_id
        )
        .order_by(
            desc(WaterQualityResult.evaluated_at)
        )
        .limit(1)
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No water quality evaluation found",
        )

    return result


@router.get(
    "/devices/{device_id}/history",
    response_model=list[WaterQualityResponse],
)
def water_quality_history(
    device_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    device = db.scalar(
        select(Device).where(
            Device.id == device_id,
            Device.is_active.is_(True),
        )
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    limit = min(max(limit, 1), 500)

    results = db.scalars(
        select(WaterQualityResult)
        .where(
            WaterQualityResult.device_id == device_id
        )
        .order_by(
            desc(WaterQualityResult.evaluated_at)
        )
        .limit(limit)
    ).all()

    return list(results)