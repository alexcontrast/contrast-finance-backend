from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class PendingActSignature(Base):
    __tablename__ = "pending_act_signatures"
    __table_args__ = (UniqueConstraint("accounting_id", "signature_sha256", name="uq_pending_act_signature"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    accounting_id: Mapped[int] = mapped_column(ForeignKey("self_employed_accounting.id", ondelete="CASCADE"), nullable=False, index=True)
    document_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signature_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False, deferred=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
