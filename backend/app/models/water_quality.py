from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WaterQualityResult(Base):
    __tablename__ = "water_quality_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    pH: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    turbidity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    tds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    temperature: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    is_safe: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    quality_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )