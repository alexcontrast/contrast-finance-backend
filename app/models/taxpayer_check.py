from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TaxpayerCheck(Base):
    __tablename__ = "taxpayer_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    contractor_id: Mapped[int | None] = mapped_column(ForeignKey("contractors.id"), nullable=True, index=True)
    iin_bin: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    name_result: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_status_result: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vat_status_result: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # success / not_found / failed / manual
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # kgd / manual
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    raw_response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    manual_set_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    contractor = relationship("Contractor", back_populates="checks")
