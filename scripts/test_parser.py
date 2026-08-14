from smart_money_tracker.agents.parser import extract_expenses

sample_inputs = [
    # "Beli kopi di Starbucks 55rb pake QRIS tadi pagi",
    # "Kemarin belanja bulanan di Superindo abis 350.000 pake Kartu Debit, terus bayar parkir 5000 cash",
    # "Makan siang ayam cabe ijo 25rb pake qris"
    "Beli buku di Amazon harga 10 USD"
]

for text in sample_inputs:
    print(f"\n--- Testing: '{text}' ---")
    result = extract_expenses(text)
    for idx, item in enumerate(result.expenses, 1):
        print(f"  Item {idx}:")
        print(f"  Merchant: {item.merchant}")
        print(f"  Amount:   {item.currency} {item.amount:,.2f}")
        print(f"  Category: {item.category.value}")
        print(f"  Payment:  {item.payment_method.value}")
        print(f"  Notes:    {item.notes}")
        print(f"  Tanggal:  {item.date}")
 