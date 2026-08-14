from ast import Dict
from langchain_core.tools import tool

RATES = {
    ("USD", "IDR"): 18200.0,
    ("SGD", "IDR"): 12100.0,
    ("JPY", "IDR"): 105.0,
    ("EUR", "IDR"): 17500.0,
}

# Docstring penting buat kasih tau ke LLM fungsi ini bisa ngapain
# Sama types parameter juga wajib ada, supaya LLM ngerti cara pakai parameternya
# Dan yang paling penting, nama function harus deskriptif 
@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """
    Get the latest currency exchange rate between two currencies.
    Args:
        from_currency: ISO currency code source (e.g., USD, SGD, JPY).
        to_currency: ISO currency code target (e.g., IDR).
    """
    if from_currency == "IDR":
        return f"""Currency is already IDR, no need to convert.
        Value is: **1 {from_currency}** for every 1 {to_currency}"""
    # Di real world app, ini bisa pakai API bank/kurs
    # untuk latihan, kita bikin bank simpel
    print(f"\n🔥🔥 [TOOL DIPANGGIL!] Mengambil kurs {from_currency} -> {to_currency}...")
    rate  = RATES.get((from_currency.upper(), to_currency.upper()), 1.0)
    return f"Nilai konversi saat ini adalah **{rate} {to_currency}** untuk setiap 1 {from_currency}"

@tool
def calculate_discount(original_price: float, discount_percentage: float) -> float:
    """
    Calculate the final price after applying a percentage discount.
    Args:
        original_price: The base price before discount.
        discount_percentage: Discount in percent (e.g., 20 for 20%).
    """
    return original_price * (1 - (discount_percentage / 100))