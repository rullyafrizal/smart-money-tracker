from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from smart_money_tracker.core.config import settings
from smart_money_tracker.schemas.expense import ExpenseExtractionResult
from smart_money_tracker.agents.tools import get_exchange_rate, calculate_discount

SYSTEM_PROMPT = """
You are an expert financial assistant and receipt parser.
Your task is to accurately extract financial expense information from user messages, receipts, or transaction notifications.

Context:
- Today's date is: {current_date}

Guidelines:
1. Identify all distinct expenses in the input (a single message might contain multiple items).
2. Handle currency amounts and shorthand notations accurately:
   - E.g., '50k', '50rb', '50.000' in Indonesian context means 50000.
   - E.g., '1.5jt' or '1.5m' means 1500000.
3. Currency used is IDR for the tracker, so if currency is other than IDR, make sure to convert it to IDR.
4. Infer the most accurate merchant/vendor name. If the user says 'makan siang di warteg', merchant is 'Warteg'.
5. Map to the most suitable category (food, transportation, utilities, shopping, etc.) and payment method (cash, qris, debit, credit, ewallet, etc.).
6. Date Handling:
   - Resolve relative dates against today's date ({current_date}). 
     Example: If today is 2026-08-14 and user says 'kemarin', date is '2026-08-13'.
     If user says 'tadi pagi' or doesn't specify any past date, use '{current_date}'.
   - Always output date in 'YYYY-MM-DD' format.
7. Capture extra context or item breakdowns in the 'notes' field.
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

def extract_expenses(raw_text: str, ref_date: str | None = None) -> ExpenseExtractionResult:
    """
    Extract structured expense records from raw text using LangChain and Gemini structured output with automated Tool Calling loop.
    """
    today_str = ref_date or datetime.now().strftime("%Y-%m-%d")

    llm = get_llm()
    llm_with_tools = llm.bind_tools(list(AVAILABLE_TOOLS.values()))

    msgs = [
        SystemMessage(content=SYSTEM_PROMPT.format(
                current_date=today_str,
                default_currency=settings.default_currency
            )),
        HumanMessage(content=f"Extract and calculate the expense details for:\n\n{raw_text}")
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

    result.raw_text = raw_text
    return result