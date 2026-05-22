from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True, index=True)
    forecast_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    predicted_value: Mapped[float]
    horizon: Mapped[int] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    entity = relationship("Entity", back_populates="forecasts")
    source = relationship("Source", back_populates="forecasts")
