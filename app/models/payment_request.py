from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    event_item_id: Mapped[int] = mapped_column(ForeignKey("event_items.id"), nullable=False, index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    amount_requested: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # invoice / card / cash / self_employed
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)

    # Статус оплаты подрядчику: new / to_pay / paid / rejected / tax_check_needed
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new", index=True)

    # Статус денег клиента по мероприятию: waiting_money / cash_received. Независим от оплаты подрядчику.
    money_status: Mapped[str] = mapped_column(String(50), nullable=False, default="waiting_money", index=True)

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Snapshot from event item at the moment of request.
    item_name_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_amount_plan_snapshot: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    item_amount_fact_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    item_paid_amount_snapshot: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    item_remaining_snapshot: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    contractor_id: Mapped[int | None] = mapped_column(ForeignKey("contractors.id"), nullable=True, index=True)

    # Tax snapshot. Card shows only compact tax_status_snapshot, not amounts.
    contractor_name_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    iin_bin_snapshot: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tax_status_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vat_status_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vat_amount_snapshot: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    deduction_amount_snapshot: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    tax_source_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)

    card_number: Mapped[str | None] = mapped_column(String(30), nullable=True)

    manual_tax_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manual_tax_set_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    manual_tax_set_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    warning_over_remaining: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cash_received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    event = relationship("Event", back_populates="payment_requests")
    event_item = relationship("EventItem", back_populates="payment_requests")
    created_by_user = relationship("User", back_populates="payment_requests_created", foreign_keys=[created_by_user_id])
    contractor = relationship("Contractor", back_populates="payment_requests")
