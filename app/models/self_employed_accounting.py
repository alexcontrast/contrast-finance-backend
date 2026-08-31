from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, LargeBinary, Numeric, String, Text
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
    contractor_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
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

    # R-1 document lifecycle.  The generated PDF is stored in Postgres for the
    # same reason as the original receipt: Railway's filesystem is ephemeral.
    act_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_created", index=True)
    act_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    act_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    act_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    act_content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    act_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    act_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    act_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)
    act_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    act_generated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    act_sigex_document_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    act_sigex_registered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # One public URL per AVR. Both parties receive this exact URL; the signer
    # role is inferred from the IIN in the certificate returned by eGov.
    act_signing_token: Mapped[str | None] = mapped_column(String(96), nullable=True, unique=True, index=True)
    act_signing_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    act_session_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    act_session_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    act_session_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    act_sigex_data_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    act_sigex_sign_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    act_egov_mobile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    act_egov_business_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    act_qr_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    act_signing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Persist the CMS as soon as eGov/NCALayer returns it. Final registration in
    # SIGEX may be retried without asking the person to sign the AVR again.
    act_pending_signature_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)
    act_pending_signature_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    act_pending_signature_received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # SIGEX DDC (карточка электронного документа) is the permanent,
    # human-readable signed PDF. It embeds the immutable original AVR, both
    # registered CMS signatures, their visualisation and verification QR.
    act_ddc_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    act_ddc_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    act_ddc_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    act_ddc_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    act_ddc_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)
    act_ddc_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    act_ddc_last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    act_ddc_error: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    act_signatures = relationship(
        "SelfEmployedActSignature",
        back_populates="accounting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
