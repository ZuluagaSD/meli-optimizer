import uuid
import json
from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, Float, Integer, Uuid, func, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    meli_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("meli_accounts.id"), index=True)
    meli_item_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    site_id: Mapped[str] = mapped_column(String(5), index=True)
    title: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[str] = mapped_column(String(30), default="")
    category_name: Mapped[str] = mapped_column(String(255), default="")
    price: Mapped[float] = mapped_column(Float, default=0)
    currency_id: Mapped[str] = mapped_column(String(5), default="ARS")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # stored as JSON list
    pictures: Mapped[list | None] = mapped_column(JSON, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)  # stored as JSON array
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    health_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    attribute_completeness_pct: Mapped[float] = mapped_column(Float, default=0)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    meli_account: Mapped["MeliAccount"] = relationship(back_populates="listings")
    optimizations: Mapped[list["Optimization"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )
