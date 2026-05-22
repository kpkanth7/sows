from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = (
        UniqueConstraint("entity_id", "source_id", "metric_date", name="uq_metrics_entity_source_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    metric_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    mention_count: Mapped[int] = mapped_column(default=0)
    score_sum: Mapped[float] = mapped_column(default=0.0)
    item_count: Mapped[int] = mapped_column(default=0)
    trend_score: Mapped[float] = mapped_column(default=0.0, index=True)

    entity = relationship("Entity", back_populates="metrics")
    source = relationship("Source", back_populates="metrics")
