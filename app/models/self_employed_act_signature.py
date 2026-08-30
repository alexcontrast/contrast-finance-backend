from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SelfEmployedActSignature(Base):
    """One protected signing invitation for one side of an R-1 act."""

    __tablename__ = "self_employed_act_signatures"
    __table_args__ = (
        UniqueConstraint("accounting_id", "signer_role", name="uq_act_signature_accounting_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    accounting_id: Mapped[int] = mapped_column(
        ForeignKey("self_employed_accounting.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signer_role: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    expected_iin: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    token: Mapped[str] = mapped_column(String(96), nullable=False, unique=True, index=True)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="sent", index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    session_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    session_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sigex_data_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sigex_sign_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    egov_mobile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    egov_business_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    qr_code: Mapped[str | None] = mapped_column(Text, nullable=True)

    signature_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)
    signature_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sigex_sign_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    signer_iin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    signer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    accounting = relationship("SelfEmployedAccounting", back_populates="act_signatures")
