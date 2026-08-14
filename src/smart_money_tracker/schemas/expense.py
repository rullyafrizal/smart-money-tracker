from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from typing import Literal

import uuid

# Kategori Pengeluaran
class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORTATION = "transportation"
    HOUSING = "housing"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    OTHER = "other"

# Kategopri Pembayaran
class PaymentMethod(str, Enum):
    CASH = "cash"
    DEBIT = "debit"
    CREDIT = "credit"
    EWALLET = "ewallet"
    BANK_TRANSFER = "bank_transfer"
    QRIS = "qris"
    OTHER = "other"

# Entity pengeluaran
class ExpenseItem(BaseModel):
    """Structured extraction model representing an individual parsed expense item."""
    merchant: str = Field(
        ...,
        description="The name of the store, vendor, restaurant, or entity where the transaction happened"
    )

    amount: float = Field(
        ...,
        description="The total monetary amount spent (positive number)"
    )
    currency: str = Field(
        default="IDR",
        description="Three-letter ISO currency code"
    )
    category: ExpenseCategory = Field(
        default=ExpenseCategory.OTHER,
        description="The most appropriate category for this expense"
    )
    payment_method: PaymentMethod = Field(
        default=PaymentMethod.OTHER,
        description="The payment method used if identifiable."
    )
    date: Optional[str] = Field(
        default=None,
        description="Any extra details, itemized list summary, or context."
    )
    notes: Optional[str] = Field(
        default=None,
        description="Any extra details, itemized list summary, or context"
    )

# List pengeluaran
class ExpenseExtractionResult(BaseModel):
    """Wrapper model in case a single message or receipt contains multiple expenses."""

    expenses: list[ExpenseItem] = Field(
        default_factory=list,
        description="List of all expense items identified in the input text."
    )

    raw_text: str = Field(
        ...,
        description="The original text input provided by the user."
    )

class EnrichedTransaction(BaseModel):
    """Full enterprise transaction record with metadata injected by the pipeline."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    channel: Literal["telegram", "gmail", "manual"]
    created_at: datetime = Field(default_factory=datetime.now)
    item: ExpenseItem
    raw_src_text: str