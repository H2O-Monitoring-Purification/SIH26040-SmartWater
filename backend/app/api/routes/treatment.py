from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.treatment import (
    TreatmentCycleCreate,
    TreatmentCycleResponse,
)
from app.services.treatment_service import (
    start_treatment_cycle,
    get_treatment_cycle,
    get_device_treatment_cycles,
    complete_treatment_cycle,
    fail_treatment_cycle,
)


router = APIRouter(
    prefix="/treatment",
    tags=["Treatment"],
)


@router.post(
    "/devices/{device_id}/start",
    response_model=TreatmentCycleResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_cycle(
    device_id: int,
    data: TreatmentCycleCreate,
    db: Session = Depends(get_db),
):
    try:
        return start_treatment_cycle(
            db=db,
            device_id=device_id,
            source_volume_liters=data.source_volume_liters,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/devices/{device_id}",
    response_model=list[TreatmentCycleResponse],
)
def get_cycles(
    device_id: int,
    db: Session = Depends(get_db),
):
    return get_device_treatment_cycles(
        db,
        device_id,
    )


@router.get(
    "/cycles/{cycle_id}",
    response_model=TreatmentCycleResponse,
)
def get_cycle(
    cycle_id: int,
    db: Session = Depends(get_db),
):
    cycle = get_treatment_cycle(
        db,
        cycle_id,
    )

    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment cycle not found",
        )

    return cycle


@router.post(
    "/cycles/{cycle_id}/complete",
    response_model=TreatmentCycleResponse,
)
def complete_cycle(
    cycle_id: int,
    purified_volume_liters: float | None = None,
    db: Session = Depends(get_db),
):
    cycle = get_treatment_cycle(
        db,
        cycle_id,
    )

    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment cycle not found",
        )

    try:
        return complete_treatment_cycle(
            db=db,
            cycle=cycle,
            purified_volume_liters=purified_volume_liters,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/cycles/{cycle_id}/fail",
    response_model=TreatmentCycleResponse,
)
def fail_cycle(
    cycle_id: int,
    failure_reason: str,
    db: Session = Depends(get_db),
):
    cycle = get_treatment_cycle(
        db,
        cycle_id,
    )

    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment cycle not found",
        )

    try:
        return fail_treatment_cycle(
            db=db,
            cycle=cycle,
            failure_reason=failure_reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc