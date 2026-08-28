from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SelfEmployedAccounting(Base):
    __tablename__ = "self_employed_accounting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    payment_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("payment_requests.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
        index=True,
    )

    receipt_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receipt_content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    receipt_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    receipt_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # MVP storage: keep the original receipt inside Postgres so Railway's ephemeral
    # filesystem cannot lose accounting documents. The column is deferred so list
    # endpoints never load the binary payload.
    receipt_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)
    receipt_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    receipt_uploaded_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    contractor_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    iin: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    receipt_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    receipt_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    service_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    qr_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    parse_status: Mapped[str] = mapped_column(String(32), nullable=False, default="empty", index=True)

    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Reserved for the next stage (R-1 + signing) without changing today's workflow.
    act_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_created", index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    payment_request = relationship("PaymentRequest")
    request_links = relationship(
        "SelfEmployedAccountingRequest",
        back_populates="accounting",
        cascade="all, delete-orphan",
    )
