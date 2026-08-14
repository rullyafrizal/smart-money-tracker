import os
import pandas as pd

from smart_money_tracker.storage.repository import repository, ExpenseRepository

class ExcelService:
    def __init__(self, expense_repo: ExpenseRepository = repository):
        self.expense_repo = expense_repo

    def export(self, user_id:str, file_path: str) -> str:
        """Export user's expense records directly to an Excel spreadsheet."""
        records = self.expense_repo.get_all_by_user(user_id)
        if not records:
            return ""
        data = [
            {
                "Tanggal": r.date,
                "Merchant": r.merchant,
                "Nominal": r.amount,
                "Mata Uang": r.currency,
                "Kategori": r.category,
                "Metode Pembayaran": r.payment_method,
                "Catatan": r.notes or "",
                "Channel": r.channel,
                "Waktu Catat": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in records
        ]
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, engine="openpyxl")
        return os.path.abspath(file_path)

excel_service = ExcelService()