from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SelfEmployedContact(Base):
    """Reusable WhatsApp contact keyed by the self-employed person's IIN."""

    __tablename__ = "self_employed_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    iin: Mapped[str] = mapped_column(String(12), nullable=False, unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    whatsapp_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
