import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, BigInteger, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class MeliAccount(Base):
    __tablename__ = "meli_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    meli_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    site_id: Mapped[str] = mapped_column(String(5))
    nickname: Mapped[str] = mapped_column(String(255), default="")
    access_token: Mapped[str] = mapped_column(String(512))
    refresh_token: Mapped[str] = mapped_column(String(512))
    token_expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant: Mapped["Tenant"] = relationship(back_populates="meli_accounts")
    listings: Mapped[list["Listing"]] = relationship(back_populates="meli_account", cascade="all, delete-orphan")
