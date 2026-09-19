from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FilterHealth(Base):
    __tablename__ = "filter_health"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filter_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    filter_uid: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )

    installed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_service_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expected_life_days: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    estimated_remaining_days: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    flow_rate_lpm: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    pressure_drop: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    health_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="healthy",
    )

    replacement_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    replacement_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )