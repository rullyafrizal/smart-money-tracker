from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class ExpenseRecord(Base):
    """SQLAlchemy ORM table mapping for persisted expense transactions."""
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    merchant: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="IDR")
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="other")
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_src_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)