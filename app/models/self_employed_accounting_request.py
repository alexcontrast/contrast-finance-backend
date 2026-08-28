from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SelfEmployedAccountingRequest(Base):
    __tablename__ = "self_employed_accounting_requests"
    __table_args__ = (
        UniqueConstraint("payment_request_id", name="uq_self_employed_accounting_requests_payment_request_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    accounting_id: Mapped[int] = mapped_column(
        ForeignKey("self_employed_accounting.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_request_id: Mapped[int] = mapped_column(
        ForeignKey("payment_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    accounting = relationship("SelfEmployedAccounting", back_populates="request_links")
    payment_request = relationship("PaymentRequest")
