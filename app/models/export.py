from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # monthly_report / payments_report / backup / events_archive / client_offer
    export_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    period_month: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # pending / processing / completed / failed
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)

    google_sheet_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
