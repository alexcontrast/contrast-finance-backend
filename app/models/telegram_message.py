from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TelegramMessage(Base):
    __tablename__ = "telegram_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    payment_request_id: Mapped[int | None] = mapped_column(ForeignKey("payment_requests.id"), nullable=True, index=True)

    chat_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    message_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # manager_payment_card / admin_payment_card / notification
    message_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    recipient_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    # active / edited / deleted / failed
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
