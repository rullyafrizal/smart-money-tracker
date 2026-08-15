from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from smart_money_tracker.core.config import settings
from smart_money_tracker.schemas.expense import ExpenseExtractionResult
from smart_money_tracker.agents.tools import get_exchange_rate, calculate_discount

SYSTEM_PROMPT = """You are an expert Indonesian financial assistant and receipt parser.
Your task is to accurately extract financial expense information from user messages, receipts, or transaction notifications.

Context:
- Today's date is: {current_date}

Guidelines:
1. Identify ALL distinct expenses in the input (a single message might contain multiple items across multiple lines).
2. Number and Currency Parsing Rules:
   - In Indonesian notation, dots (.) are THOUSAND separators: '123.500' = 123500, '1.500.000' = 1500000.
   - Shorthand notations: '50k'/'50rb' = 50000, '12rb' = 12000, '73rb' = 73000, '1.5jt'/'1.5m' = 1500000.
   - Default currency is IDR. ONLY call the exchange rate tool if an EXPLICIT foreign currency symbol/code (e.g. $, USD, SGD, EUR, JPY) is clearly mentioned.
3. Merchant Identification:
   - Infer the most accurate merchant name (e.g. 'Mcdonalds', 'Toko Bangunan Panongan', 'Pasar Panongan').
4. Category and Payment Mapping:
   - Map category to: food, transportation, utilities, shopping, entertainment, etc.
   - Map payment to: cash, qris, debit, credit, ewallet, bank_transfer.
5. Indonesian Date Resolution:
   - 'tadi pagi', 'tadi siang', 'hari ini' -> {current_date}
   - 'kemarin' -> {current_date} minus 1 day
   - 'kemarin lusa' -> {current_date} minus 2 days
   - '1 minggu yang lalu' -> {current_date} minus 7 days
   - Output format: 'YYYY-MM-DD'.
6. Notes:
   - Capture what was purchased (e.g. 'Beli makan', 'Beli obeng', 'Belanja di pasar') in the 'notes' field.
"""


def get_llm() -> ChatGoogleGenerativeAI:
    """Factory function to initialize Google Gemini LLM."""
    return ChatGoogleGenerativeAI(
        model=settings.model_name,
        google_api_key=settings.google_api_key,
        temperature=0.0,
    )

AVAILABLE_TOOLS = {
    "get_exchange_rate": get_exchange_rate,
}

def extract_expenses(input_content: str | list, ref_date: str | None = None) -> ExpenseExtractionResult:
    """
    Extract structured expense records from raw text using LangChain and Gemini structured output with automated Tool Calling loop.
    """
    today_str = ref_date or datetime.now().strftime("%Y-%m-%d")

    llm = get_llm()
    llm_with_tools = llm.bind_tools(list(AVAILABLE_TOOLS.values()))

    # Bedakan perlakuan antara Text biasa vs Multimodal Image
    if isinstance(input_content, list):
        user_message = HumanMessage(content=input_content)
        raw_text_record = "[Foto Struk / Receipt Image]"
    else:
        user_message = HumanMessage(content=f"Extract and calculate the expense details for:\n\n{input_content}")
        raw_text_record = input_content

    msgs = [
        SystemMessage(content=SYSTEM_PROMPT.format(
                current_date=today_str,
                default_currency=settings.default_currency
            )),
        user_message
    ]

    while True:
        response = llm_with_tools.invoke(msgs)
        msgs.append(response)

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            selected_tool = AVAILABLE_TOOLS.get(tool_name)
            if selected_tool:
                tool_output = selected_tool.invoke(tool_args)
                msgs.append(
                    ToolMessage(
                        content=str(tool_output),
                        tool_call_id=tool_call["id"],
                        name=tool_name
                    )
                )

    msgs.append(HumanMessage(content="Format the extracted expenses into the required schema."))    

    structured_llm = llm_with_tools.with_structured_output(ExpenseExtractionResult)
    result: ExpenseExtractionResult = structured_llm.invoke(msgs)

    result.raw_text = raw_text_record
    return result