from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MonthlyPlan(Base):
    __tablename__ = "monthly_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    month: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)

    company_plan_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Defaults: Санжар 66.67%, Рауфаль 33.33%.
    sanzhar_share_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("66.67"))
    raufal_share_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("33.33"))

    # Default 1/8 of company plan = 12.5%.
    manager_personal_plan_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("12.50"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
