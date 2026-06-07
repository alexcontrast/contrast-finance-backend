from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="manager")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # New auth fields.
    # legacy_user_id + legacy_pin_hash allow managers to log in with the same PIN as Apps Script.
    legacy_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    legacy_pin_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    auth_source: Mapped[str] = mapped_column(String(32), nullable=False, default="legacy_apps_script")

    # Future native auth can use this without breaking legacy PINs.
    pin_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    department = relationship("Department", back_populates="users")
