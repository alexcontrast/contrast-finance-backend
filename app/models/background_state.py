from datetime import datetime
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class BackgroundState(Base):
    __tablename__ = "background_states"
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    owner: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    watermark: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
