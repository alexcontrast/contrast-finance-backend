from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Contractor(Base):
    __tablename__ = "contractors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    iin_bin: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # our_vat / our_no_vat / simplified / self_employed / not_found / manual
    tax_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Whether the contractor is VAT payer according to KGD/current manual data.
    vat_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Current calculated/default values, refreshed daily in background.
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    deduction_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    # kgd / manual
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    checks = relationship("TaxpayerCheck", back_populates="contractor")
    payment_requests = relationship("PaymentRequest", back_populates="contractor")
