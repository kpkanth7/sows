from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (UniqueConstraint("canonical_name", "entity_type", name="uq_entities_name_type"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    entity_type: Mapped[str] = mapped_column(String(80), index=True)
    canonical_name: Mapped[str] = mapped_column(String(200), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    item_entities = relationship("ItemEntity", back_populates="entity", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="entity")
    summaries = relationship("Summary", back_populates="entity")
    forecasts = relationship("Forecast", back_populates="entity")


class ItemEntity(Base):
    __tablename__ = "item_entities"
    __table_args__ = (UniqueConstraint("item_id", "entity_id", name="uq_item_entities"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)

    item = relationship("Item", back_populates="item_entities")
    entity = relationship("Entity", back_populates="item_entities")
