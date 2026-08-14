from smart_money_tracker.agents.parser import get_llm
from smart_money_tracker.agents.tools import get_exchange_rate, calculate_discount

# 1. Inisialisasi model dan bind tools
llm = get_llm()
llm_with_tools = llm.bind_tools([get_exchange_rate, calculate_discount])

# 2. Kirim pesan ke LLM
query = "Berapa kurs 10 USD ke IDR jika menggunakan tool exchange rate?"
print(f"User: {query}")

response = llm_with_tools.invoke(query)

# 3. Lihat apa yang diminta oleh LLM
print("\n--- Respons dari LLM ---")
print("Apakah LLM meminta tool?", bool(response.tool_calls))
print("Tool yang diminta:", response.tool_calls)

# 4. Eksekusi tool secara manual di Python (mensimulasikan apa yang dilakukan Agent)
for tool_call in response.tool_calls:
    if tool_call["name"] == "get_exchange_rate":
        args = tool_call["args"]
        # Eksekusi fungsi Python asli:
        rate = get_exchange_rate.invoke(args)
        print(f"\nHasil eksekusi fungsi Python: 1 {args['from_currency']} = {rate} {args['to_currency']}")
        print(f"Total untuk 10 USD = {10 * rate:,.2f} IDR")
