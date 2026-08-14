import os
import pandas as pd

from sqlalchemy import  create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session

from smart_money_tracker.core.config import settings, Settings
from smart_money_tracker.schemas.expense import EnrichedTransaction
from smart_money_tracker.storage.models import Base, ExpenseRecord

class ExpenseRepository:
    def __init__(self, config: Settings = settings):
        self.engine = create_engine(config.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    def save_transactions(self, transactions: list[EnrichedTransaction]):
        saved_ids = []
        with self.SessionLocal() as sess:
            for tx in transactions:
                record = ExpenseRecord(
                    id=tx.id,
                    user_id=tx.user_id,
                    merchant=tx.item.merchant,
                    amount=tx.item.amount,
                    currency=tx.item.currency,
                    category=tx.item.category.value,
                    payment_method=tx.item.payment_method.value,
                    date=tx.item.date or "",
                    notes=tx.item.notes,
                    channel=tx.channel,
                    raw_src_text=tx.raw_src_text,
                    created_at=tx.created_at
                )
                sess.add(record)
                saved_ids.append(record.id)
            sess.commit()
        return saved_ids

    def get_all_by_user(self, user_id: str) -> list[ExpenseRecord]:
        """Retrieve all expenses for a specific user."""
        with self.SessionLocal() as sess:
            stmt = select(ExpenseRecord).where(ExpenseRecord.user_id == user_id).order_by(ExpenseRecord.date.desc())
            return list(sess.scalars(stmt).all())

    def get_category_breakdown(self, user_id: str) -> dict[str, float]:
        with self.SessionLocal() as sess:
            stmt = (
                select(ExpenseRecord.category, func.sum(ExpenseRecord.amount))
                .where(ExpenseRecord.user_id == user_id)
                .group_by(ExpenseRecord.category)
            )
            result = sess.execute(stmt)
            breakdown = {row[0]: float(row[1]) for row in result}
            return breakdown

    def get_monthly_total(self, user_id: str, month: int, year: int) -> float:
        with self.SessionLocal() as sess:
            stmt = (
                select(func.sum(ExpenseRecord.amount))
                .where(ExpenseRecord.user_id == user_id)
                .where(func.extract("month", ExpenseRecord.date) == month)
                .where(func.extract("year", ExpenseRecord.date) == year)
            )
            result = sess.execute(stmt)
            return float(result.scalar_one() or 0)

repository = ExpenseRepository()
    
        
    