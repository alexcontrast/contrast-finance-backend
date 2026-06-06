from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventShare(Base):
    __tablename__ = "event_shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    share_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    event = relationship("Event", back_populates="shares")
