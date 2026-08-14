# 💰 Smart Money Tracker

An enterprise-grade, agentic financial tracking assistant built with **Python 3.12**, **LangChain**, **LangGraph**, **Google Gemini**, and **SQLAlchemy 2.0**. 

Smart Money Tracker ingests natural language transaction logs, receipts, and messages across multiple channels (Telegram, Gmail, Manual CLI), accurately parses multi-item expenses, performs automated tool-assisted currency conversion, clarifies incomplete details via Human-in-the-Loop workflows, and persists structured data to SQL databases and Excel reports.

---

## 🌟 Key Features

- **🧠 Intelligent Financial Parser**: Extracts merchant, amount, category, payment method, date, and itemized notes from messy, multi-item text using Google Gemini with structured Pydantic v2 schemas.
- **🛠️ Automated Tool Calling**: Seamlessly executes runtime tools (e.g. real-time foreign currency conversion `USD/SGD/EUR -> IDR`) before finalizing structured records.
- **📅 Dynamic Date Resolution**: Resolves relative time expressions (*"kemarin"*, *"tadi pagi"*, *"2 hari lalu"*) against dynamic runtime reference timestamps.
- **🔄 Multi-Turn Human-in-the-Loop (LangGraph)**: Identifies missing or ambiguous fields (e.g., missing price, vendor, or payment method) and prompts the user for clarification while preserving conversation context across sessions.
- **⚠️ High-Value Expense Alerts**: Custom configurable safety thresholds (e.g., transactions `>= IDR 500,000`) flag high-ticket expenses with visual warnings.
- **💾 Decoupled Storage Layer (Repository Pattern)**: Persists records using modern SQLAlchemy 2.0 (supporting SQLite and PostgreSQL) with aggregated financial analytics.
- **📊 Excel Export Service**: Dedicated service for exporting user expense histories to formatted `.xlsx` spreadsheets via `pandas` and `openpyxl`.

---

## 🏗️ Architecture & Workflow

```text
                ┌── Gmail
                │
Inputs ─────────┼── Telegram
                │
                └── Manual text
                       ↓
             ┌───────────────────┐
             │   Expense Agent   │ ──▶ Tool Calling (`get_exchange_rate`)
             │  (Google Gemini)  │
             └─────────┬─────────┘
                       ↓
             ┌───────────────────┐
             │     LangGraph     │ ──▶ Human-in-the-Loop Clarification
             │  (State Machine)  │ ──▶ High-Value Safety Check
             └─────────┬─────────┘
                       ↓
             ┌───────────────────┐
             │ Persistence Layer │ ──▶ SQLite / PostgreSQL
             │  (SQLAlchemy 2.0) │ ──▶ Excel Export (`.xlsx`)
             └─────────┬─────────┘
                       ↓
             ┌───────────────────┐
             │ Outbound Response │ ──▶ Confirmation & Alerts
             └───────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python `3.12.x` |
| **Package Manager** | [`uv`](https://github.com/astral-sh/uv) with `requirements.txt` |
| **LLM Provider** | Google GenAI (`gemini-2.5-flash` / `gemini-1.5-flash`) |
| **Agent Framework** | [LangChain](https://www.langchain.com/) & [LangGraph](https://langchain-ai.github.io/langgraph/) |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/latest/) & `pydantic-settings` |
| **Persistence** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (SQLite / PostgreSQL) |
| **Spreadsheet Export**| `pandas` & `openpyxl` |

---

## 📁 Project Structure

```text
smart-money-tracker/
├── .env.example              # Environment variables template
├── pyproject.toml            # Project metadata
├── requirements.txt          # Production dependencies
├── RULES.md                  # Development rules & guidelines
├── LEARNING_NOTES.md         # Comprehensive architectural learning notes
├── scripts/                  # Interactive testing & CLI scripts
│   ├── test_parser.py        # Core LLM parsing & currency tests
│   ├── test_pure_tool_calling.py # Low-level tool invocation tests
│   ├── test_graph.py         # Multi-turn LangGraph interactive REPL
│   ├── test_persistence.py   # Database and Excel export verification
│   └── test_analytics.py     # Category breakdown & monthly metrics
└── src/
    └── smart_money_tracker/
        ├── core/             # Configuration & environment settings
        │   └── config.py
        ├── schemas/          # Pydantic domain models & DTOs
        │   └── expense.py
        ├── agents/           # LangChain extractors, tools & LangGraph workflow
        │   ├── graph.py      # LangGraph state machine definition
        │   ├── parser.py     # Gemini extraction & tool loop
        │   └── tools.py      # Exchange rate & calculation tools
        ├── storage/          # ORM models and repository layer
        │   ├── models.py     # SQLAlchemy table definitions
        │   └── repository.py # Database CRUD & analytics queries
        └── service/          # Business service layer
            └── excel.py      # Excel export service
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12+
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`)
- Google Gemini API Key (from [Google AI Studio](https://aistudio.google.com/app/apikey))

### 2. Installation & Setup

Clone the repository and set up the environment:

```bash
# 1. Create Python 3.12 virtual environment
uv venv --python 3.12

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Install package in editable mode
uv pip install -e .
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-2.5-flash-lite
DEFAULT_CURRENCY=IDR
DATABASE_URL=sqlite:///./tracker.db
```

---

## 🧪 Running & Testing

### Interactive Agent REPL (LangGraph Multi-Turn)
Test the conversational agent with clarification and high-value warnings:

```bash
PYTHONPATH=src python scripts/test_graph.py
```
*Example prompt flow:*
```text
User: Beli kopi di starbucks harga 25 USD, kemarin
Bot [need_confirmation]: Saya mendeteksi pengeluaran di Starbucks sebesar IDR 455,000.00, tapi masih membutuhkan informasi metode pembayaran.
User: Cash
Bot [success]: ✅ Catatan Pengeluaran Berhasil Disimpan: Starbucks — IDR 455,000.00 (Tanggal: 2026-08-13)
```

### Database Persistence & Excel Export
Verify SQLite data storage and generate `laporan_pengeluaran.xlsx`:

```bash
PYTHONPATH=src python scripts/test_persistence.py
```

### Financial Analytics & Category Breakdown
View monthly totals and category-based spending distributions:

```bash
PYTHONPATH=src python scripts/test_analytics.py
```

---

## 📄 License
MIT License. Free for educational and commercial use.
