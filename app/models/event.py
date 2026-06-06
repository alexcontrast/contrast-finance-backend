from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Заказчик важнее названия — в интерфейсе показываем первым.
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False, index=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # draft / review / accepted / revision / completed / cancelled
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)

    # ip_contrast_event / our_no_vat / simplified / cash
    client_calc_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # default 21, admin can change
    manager_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("21.00"))

    agency_commission_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    agency_commission_spread_enabled: Mapped[str] = mapped_column(String(10), nullable=False, default="false")

    # Only for simplified calculation type: one combined line/field.
    simplified_bank_tax_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    department = relationship("Department", back_populates="events")
    manager = relationship("User", back_populates="events")
    items = relationship("EventItem", back_populates="event", cascade="all, delete-orphan")
    payment_requests = relationship("PaymentRequest", back_populates="event")
    shares = relationship("EventShare", back_populates="event", cascade="all, delete-orphan")
