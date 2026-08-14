from smart_money_tracker.service.excel import excel_service
from smart_money_tracker.storage.repository import repository

user_id = "usr_telegram_123"

# 1. Ambil data dari database SQLite yang tersimpan dari test sebelumnya
records = repository.get_all_by_user(user_id)
print(f"\n📊 Total transaksi tersimpan di Database untuk {user_id}: {len(records)}")

for idx, r in enumerate(records, 1):
    print(f"{idx}. [{r.date}] {r.merchant} - {r.currency} {r.amount:,.2f} ({r.category}) via {r.payment_method}")

# 2. Ekspor ke Excel
excel_path = excel_service.export(user_id, "laporan_pengeluaran.xlsx")
if excel_path:
    print(f"\n📁 File Excel berhasil dibuat di: {excel_path}")
