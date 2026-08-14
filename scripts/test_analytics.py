from smart_money_tracker.storage.repository import repository

user_id = "usr_telegram_123"

# 1. Ambil data dari database SQLite yang tersimpan dari test sebelumnya
month = 8
year = 2026

category_breakdown = repository.get_category_breakdown(user_id)
monthly_total = repository.get_monthly_total(user_id, month, year)

display = f"""
📊 LAPORAN KEUANGAN BULAN {year}-{month:02d} (User: {user_id})
----------------------------------------------------------
💰 Total Pengeluaran: IDR {monthly_total:,.2f}
📈 Rincian Per Kategori:

"""

breakdown_lines = ""
for cat, amount in category_breakdown.items():
    percentage = (amount / monthly_total) * 100 if monthly_total > 0 else 0
    breakdown_lines += (
        f"- {cat.upper()}: IDR {amount:,.2f} ({percentage:.1f}%)\n"
    )

display += breakdown_lines
print(display)
