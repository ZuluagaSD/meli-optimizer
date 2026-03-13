import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, Text, Uuid, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Optimization(Base):
    __tablename__ = "optimizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("listings.id"), index=True)
    type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    original_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    suggested_titles: Mapped[list | None] = mapped_column(JSON, nullable=True)
    original_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), default="claude-sonnet-4-20250514")
    prompt_version: Mapped[str] = mapped_column(String(20), default="v1")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    listing: Mapped["Listing"] = relationship(back_populates="optimizations")
