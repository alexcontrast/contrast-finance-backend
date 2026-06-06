from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventItem(Base):
    __tablename__ = "event_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)

    # regular / coordinator
    item_type: Mapped[str] = mapped_column(String(50), nullable=False, default="regular")

    # Внешняя смета для заказчика
    external_name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    external_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("1.00"))
    external_days: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("1.00"))
    external_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    external_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Внутренняя смета
    amount_fact: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    # invoice / card / cash / self_employed
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    iin_bin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    iin_bin_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tax_check_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Короткие столбики во внутренней смете:
    # НДС и Вычеты.
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    deduction_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    internal_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    event = relationship("Event", back_populates="items")
