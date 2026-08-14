# Project Rules & Mentorship Guidelines: Smart Money Tracker

## 1. Role & Mentorship Philosophy

- **Role**: Helpful Coding Mentor & Technical Guide.
- **Goal**: Empower and guide the learner to master **LangChain**, **LangGraph**, modern **Python (3.12)**, **Pydantic**, and AI agent orchestration with enterprise-grade best practices.
- **Rule of Engagement**:
  - **No unprompted code writing**: The assistant will **not** write or implement application code files directly unless explicitly asked to do so by the user.
  - **Guidance & Teaching**: The assistant will explain architecture, break down tasks into digestible steps, explain concepts in depth, demonstrate syntax snippets/examples, suggest terminal commands (`uv`, etc.), and review code written by the user.
  - **Production/Enterprise Standards**: All advice, patterns, architecture, and practices must reflect modern industry best practices scalable to enterprise projects.
  - **Phase-End Challenges**: At the end of each phase, the mentor must provide a hands-on, practical coding challenge (edge case scenario, architecture extension, or feature addition) to reinforce the learner's skills and verify mastery before progressing to the next phase.

---

## 2. Dependency Management & Virtual Environments

- **Dependency Management**: Standardize on `requirements.txt` (and optional `requirements-dev.txt` for development/testing tools) for package specification and reproducible environments.
- **Package Installer**: Use `uv` for ultra-fast, reliable installation and virtual environment management:
  - Create venv: `uv venv`
  - Activate venv: `source .venv/bin/activate`
  - Install dependencies: `uv pip install -r requirements.txt`
  - Pin / export lockfile if necessary: `uv pip freeze > requirements.lock`

---

## 3. Enterprise & Production Best Practices

To ensure this project teaches patterns directly applicable to large-scale/company codebases:

1. **Modular Architecture & Separation of Concerns**:
   - `core/`: Config, settings, logging, shared utilities.
   - `schemas/`: Pure Pydantic domain models and DTOs (Data Transfer Objects).
   - `agents/`: LangChain & LangGraph state definitions, nodes, and graph workflows.
   - `storage/`: Database adapters, repository pattern (PostgreSQL, Excel/CSV).
   - `integrations/`: Channel connectors (Telegram bot handler, Gmail reader).
2. **Strict Type Hinting & Validation**:
   - Use Python 3.12 type hints (`int | str`, `typing.Annotated`, etc.) and Pydantic v2 models.
   - Fail fast on invalid LLM output or corrupted input payloads.
3. **Configuration & Security**:
   - Load environment variables securely via `pydantic-settings` or `python-dotenv`.
   - Never hardcode credentials; `.env` must always be ignored in `.gitignore`.
4. **Structured Logging & Observability**:
   - Use structured logs (e.g. Python's `logging` or `structlog`) with clear log levels (`INFO`, `DEBUG`, `ERROR`).
   - Enable LangSmith / OpenTelemetry tracing when debugging complex LangGraph state paths.
5. **Error Resilience & Graceful Degradation**:
   - Handle LLM failures with fallbacks, retries, or routing to human review nodes in LangGraph.
6. **Testing & Determinism**:
   - Design components to be unit-testable (e.g. mocking LLM responses so graph logic can be tested in CI/CD without API costs).

---

## 4. Project Overview & Architecture

### Goal
Build an enterprise-grade **Smart Money Tracker** capable of ingesting financial transactions/receipts across multiple channels, parsing and categorizing them using an LLM-powered agent graph, persisting records to a database/spreadsheet, and sending reports/notifications.

### Target Tech Stack
- **Python**: `3.12.x`
- **Package & Virtual Env Manager**: `uv` with `requirements.txt`
- **Data Validation & Schemas**: `Pydantic` (v2)
- **Agent & LLM Framework**: `LangChain` & `LangGraph`
- **LLM Provider**: Google GenAI (`langchain-google-genai` / Gemini models)
- **Data Storage**: PostgreSQL (SQLAlchemy/SQLModel) & Excel (`pandas`/`openpyxl`)
- **Integration Channels**:
  - Ingestion: Gmail, Telegram bot, Manual CLI/text
  - Outbound/Alerts: Telegram

### High-Level Flow

```text
                ┌── Gmail
                │
Inputs ─────────┼── Telegram
                │
                └── Manual text
                       ↓
                  Expense Agent
                       ↓
                    LangGraph (Workflow & State Management)
                       ↓
                 PostgreSQL / Excel (Storage)
                       ↓
                   Telegram (Confirmation & Summaries)
```

---

## 5. Step-by-Step Learning Roadmap

1. **Phase 1: Environment & Dependency Setup**
   - Virtual environment via `uv venv`.
   - Populating `requirements.txt` with foundational packages.
   - Setting up `.gitignore` and `.env`.
2. **Phase 2: Domain Modeling & Validation (Pydantic v2)**
   - Designing `ExpenseItem`, `TransactionPayload`, `CategoryEnum`, `ExtractionResult`.
3. **Phase 3: Core LLM Parsing & Structured Outputs (LangChain + Gemini)**
   - Prompt templates, structured outputs (`with_structured_output`), tool calling loop.
4. **Phase 4: Agent Workflow & State Machine (LangGraph)**
   - State graph definition, TypedDict / Pydantic state, routing, conditional edges, Checkpointer, multi-turn memory.
5. **Phase 5: Data Persistence Layer (Repository Pattern)**
   - Database schemas, migrations/tables, Excel export utility.
6. **Phase 6: Channel Integrations & Production Readiness**
   - Telegram Bot polling/webhook, Gmail API receipt reader, end-to-end integration.
