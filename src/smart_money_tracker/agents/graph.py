from typing import TypedDict, Optional, Literal, Annotated

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from smart_money_tracker.schemas.expense import (
    ExpenseExtractionResult,
    EnrichedTransaction
)
from smart_money_tracker.agents.parser import extract_expenses
from smart_money_tracker.schemas.expense import PaymentMethod
from smart_money_tracker.schemas.expense import ExpenseItem
from smart_money_tracker.storage.repository import repository

class TrackerState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    channel: Literal["telegram", "gmail", "manual"]
    ref_date: Optional[str]

    extraction_result: Optional[ExpenseExtractionResult]
    enriched_transactions: list[EnrichedTransaction]
    status: Literal["success", "need_confirmation", "failed"]
    final_message: str
    warning_message: Optional[str]

def parse_node(state: TrackerState) -> dict:
    conversation_history = "\n".join(
        f"{msg.type}: {msg.content}" for msg in state["messages"]
    )
    ref_date = state.get("ref_date")

    result = extract_expenses(raw_text=conversation_history, ref_date=ref_date)
    return {"extraction_result": result}

def confirmation_node(state: TrackerState) -> dict:
    msg = state.get("final_message", "Bisa tolong berikan detail nominal dan tokonya?")
    return {
        "messages": [AIMessage(content=msg)]
    }

def validate_enrich_node(state: TrackerState) -> dict:
    extraction = state.get("extraction_result")
    if not extraction or not extraction.expenses:
        return {
            "status": "need_confirmation",
            "final_message": "Maaf, saya tidak dapat menemukan informasi pengeluaran pada pesan Anda. Mohon sebutkan nama toko, nominal, dan metode pembayarannya."
        }

    enriched_list: list[EnrichedTransaction] = []
    for item in extraction.expenses:
        missing = check_missing_fields(item)
        if missing:
            clarification_msg = generate_clarification_prompt(item, missing)
            return {
                "status": "need_confirmation",
                "final_message": clarification_msg
            }

        record = EnrichedTransaction(
            user_id=state["user_id"], 
            channel=state["channel"],
            item=item,
            raw_src_text=extraction.raw_text
        )
        enriched_list.append(record)
    
    return {
        "enriched_transactions": enriched_list,
        "status": "success"
    }


def format_summary_node(state: TrackerState) -> dict:
    trxs = state.get("enriched_transactions", [])
    total_amount = sum(t.item.amount for t in trxs)

    lines = ["✅ **Catatan Pengeluaran Berhasil Disimpan:**\n"]
    for idx, tx in enumerate(trxs, 1):
        lines.append(
            f"{idx}. **{tx.item.merchant}** — {tx.item.currency} {tx.item.amount:,.2f}\n"
            f"   - Kategori: `{tx.item.category.value}`\n"
            f"   - Pembayaran: `{tx.item.payment_method.value}`\n"
            f"   - Tanggal: `{tx.item.date}`\n"
            f"   - Merchant: {tx.item.merchant}\n"
            f"   - Catatan: _{tx.item.notes}_\n"
            f"   - Channel Laporan: {tx.channel}\n"
        )
    lines.append(f"💰 **Total:** IDR {total_amount:,.2f}")
    warning_message = state.get("warning_message", "")
    if warning_message:
        lines.append("\n" + warning_message)
    return {"final_message": "\n".join(lines)}

def check_status_router(state: TrackerState) -> str:
    if state.get("status") == "success":
        return "high_value_check"
    return "clarify"

def high_value_check_node(state: TrackerState) -> dict:
    trxs = state.get("enriched_transactions", [])
    high_value_limit = 500000
    high_value_trxs = [t for t in trxs if t.item.amount > high_value_limit]
    if not high_value_trxs:
        return {"status": "success"}

    merchants: set[str] = set()
    for t in high_value_trxs:
        merchants.add(t.item.merchant)
    
    return {
        "status": "success",
        "warning_message": f"⚠️ [PERINGATAN] Transaksi di {', '.join(merchants)} melebihi IDR {high_value_limit}!"
    }
    
def storage_node(state: TrackerState) -> dict:
    trxs = state.get("enriched_transactions", [])
    if trxs:
        repository.save_transactions(trxs)
    return {"status": "success"}
        

def build_tracker_graph():
    flow = StateGraph(TrackerState)

    flow.add_node("parse", parse_node)
    flow.add_node("validate_enrich", validate_enrich_node)
    flow.add_node("clarify", confirmation_node)
    flow.add_node("format_summary", format_summary_node)
    flow.add_node("high_value_check", high_value_check_node)
    flow.add_node("storage", storage_node)

    flow.add_edge(START, "parse")
    flow.add_edge("parse", "validate_enrich")

    flow.add_conditional_edges(
        "validate_enrich",
        check_status_router,
        {
            "high_value_check": "high_value_check",
            "clarify": "clarify"
        }
    )

    flow.add_edge("high_value_check", "storage")
    flow.add_edge("storage", "format_summary")
    flow.add_edge("format_summary", END)
    flow.add_edge("clarify", END)
    
    memory = InMemorySaver()
    return flow.compile(checkpointer=memory)

def check_missing_fields(item: ExpenseItem) -> list[str]:
    """Cek field apa saja yang masih kosong atau bernilai generic."""
    missing = []
    
    if item.amount <= 0:
        missing.append("nominal (jumlah uang)")
        
    generic_merchants = ["", "unknown", "none", "-", "toko", "tempat", "merchant"]
    if not item.merchant or item.merchant.strip().lower() in generic_merchants:
        missing.append("nama merchant/toko")
        
    if item.payment_method == PaymentMethod.OTHER:
        missing.append("metode pembayaran (Cash/QRIS/Debit/Transfer)")
        
    return missing

def generate_clarification_prompt(item: ExpenseItem, missing_fields: list[str]) -> str:
    known_info = []
    if item.merchant and item.merchant.lower() not in ["", "unknown", "none"]:
        known_info.append(f"di **{item.merchant}**")
    if item.amount > 0:
        known_info.append(f"sebesar **{item.currency} {item.amount:,.2f}**")
        
    known_str = " ".join(known_info)
    missing_str = ", ".join(missing_fields)
    
    if known_str:
        return f"Saya mendeteksi pengeluaran {known_str}, tapi masih membutuhkan informasi **{missing_str}**. Bisa tolong dilengkapi?"
    else:
        return f"Saya belum menemukan detail pengeluaran pada pesan Anda. Mohon sebutkan **{missing_str}**."
