# 📚 Smart Money Tracker: Comprehensive Learning Notes & Architectural Journey

Dokumen ini merangkum seluruh konsep, implementasi, best practices, dan pelajaran penting (*lessons learned*) yang telah kita pelajari dan bangun dari **Phase 1** hingga **Phase 5**.

---

## 🗺️ 1. High-Level Architecture Overview

```text
                                [ User Input ]
                         (Telegram / Gmail / CLI)
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │          LangGraph            │
                    │      (State Machine)          │
                    └───────────────┬───────────────┘
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
      [ Parsing & Tools ]                      [ Human-in-the-Loop ]
- Gemini 2.5/Flash-Lite                     - Field-Level Validation
- Tool Calling (`get_exchange_rate`)        - Dynamic Clarification
- Pydantic v2 Structured Output             - Session Checkpointer (`thread_id`)
               │                                         │
               └────────────────────┬────────────────────┘
                                    │ (Status: Success)
                                    ▼
                    ┌───────────────────────────────┐
                    │   Business Rules & Warning    │
                    │    (High-Value Alert Node)    │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Data Persistence Layer      │
                    │  (SQLAlchemy 2.0 Repository)  │
                    └───────┬───────────────┬───────┘
                            │               │
                            ▼               ▼
                     [ SQLite / PG ]   [ Excel Service ]
                     (`tracker.db`)    (`expenses.xlsx`)
```

---

## 🧱 2. Summary Pembelajaran Per Fase

---

### 📦 Phase 1: Environment & Dependency Management
- **`uv` Package Manager**: Menggunakan `uv venv` dan `uv pip install -r requirements.txt` untuk instalasi dependensi Python 3.12 yang sangat cepat dan deterministik.
- **Security & Secret Management**: Memisahkan kredensial sensitif (`GOOGLE_API_KEY`, `DATABASE_URL`) ke dalam `.env` dan melindunginya dengan `.gitignore`.
- **Python `src/` Layout**: Memahami resolusi modul Python (`sys.path` vs `PYTHONPATH=src` vs `uv pip install -e .`).

---

### 📐 Phase 2: Domain Modeling dengan Pydantic v2
- **Dual-Purpose Schemas**:
  1. Validasi tipe data internal backend Python.
  2. Prompt Schema untuk LLM (Gemini membaca `Field(description="...")` sebagai panduan ekstraksi data dari teks bebas).
- **Enums**: Mengelompokkan `ExpenseCategory` dan `PaymentMethod` agar output LLM selalu terbatas pada pilihan yang valid.
- **Type-Safe Configuration (`pydantic-settings`)**: Validasi konfigurasi lingkungan sejak aplikasi pertama kali *booting*.

---

### 🧠 Phase 3: Core LLM Parsing, Structured Output & Tool Calling

#### A. Structured Output vs Text Prompting
- Menggunakan `model.with_structured_output(ExpenseExtractionResult)` untuk menjamin respon LLM selalu sesuai format Pydantic tanpa risiko formatting rusak.

#### B. Dynamic Context Injection
- LLM tidak memiliki jam internal. Kita meng-inject `{current_date}` ke System Prompt saat runtime sehingga LLM dapat menghitung tanggal relatif (*kemarin*, *tadi pagi*, *2 hari lalu*).

#### C. Tool Calling Protocol (Function Calling)
- **Docstrings & Type Hints**: Berfungsi sebagai instruksi langsung yang dibaca oleh Gemini.
- **Single-Turn vs Multi-Turn Agent Loop**:
  - `with_structured_output` adalah single-turn format.
  - Untuk memanggil tool eksternal (seperti kurs mata uang `get_exchange_rate`), diperlukan **Loop Eksekusi**:
    1. LLM meminta tool call (`AIMessage.tool_calls`).
    2. Python mengeksekusi fungsi lokal.
    3. Python membalas dengan `ToolMessage(content=..., tool_call_id=...)`.
    4. LLM membaca hasil dan melanjutkan pemrosesan.
- **Aturan No-Model-Prefill pada Gemini API**:
  - Gemini API versi terbaru melarang percakapan berakhir dengan pesan `role: model`. Setiap siklus pesan sebelum request final wajib diakhiri oleh `HumanMessage` atau `ToolMessage`.

---

### 🌐 Phase 4: Workflow Orchestration & Human-in-the-Loop (LangGraph)

#### A. Komponen LangGraph
- **`TrackerState`**: Single source of truth data yang mengalir antar-node.
- **`add_messages` Reducer**: Mengakumulasi riwayat pesan percakapan untuk multi-turn chat.
- **`InMemorySaver` Checkpointer**: Menyimpan state per `thread_id` (session user).

#### B. Field-Level Validation & Dynamic Clarification
- Jika informasi tidak lengkap (misal: user hanya menyebut toko tanpa nominal atau sebaliknya), node validasi menghasilkan pesan klarifikasi kontekstual yang ramah:
  > *"Saya mendeteksi pengeluaran di **Starbucks** sebesar **IDR 455,000.00**, tapi masih membutuhkan informasi **metode pembayaran**."*

#### C. Transaction Scoping & Context Isolation
- **Pelajaran Kritis**: Riwayat pesan multi-turn hanya relevan selama transaksi berstatus `need_confirmation`. Begitu transaksi `success`, `thread_id` harus di-reset agar summary transaksi lama tidak mencemari konteks transaksi baru (*Context Pollution*).

#### D. Phase 4 Challenge: High-Value Alert Node
- Menambahkan node `high_value_check_node` untuk mendeteksi transaksi di atas ambang batas (misal `>= IDR 500,000`) dan menyematkan pesan peringatan khusus `warning_message`.

---

### 💾 Phase 5: Data Persistence & Analytics Layer

#### A. Repository Pattern & Decoupling
- Memisahkan logika database dari workflow agent. `ExpenseRepository` mengelola koneksi database via **SQLAlchemy 2.0** (`Mapped`, `mapped_column`, `SessionLocal`).
- Siap digunakan untuk SQLite (`tracker.db`) maupun PostgreSQL tanpa mengubah kode Agent.

#### B. Service Layer: Single Responsibility Principle (SRP)
- Memisahkan fungsi ekspor Excel ke dalam service tersendiri: `src/smart_money_tracker/service/excel.py` (`ExcelService`), sehingga `ExpenseRepository` tetap fokus pada urusan SQL.

#### C. Phase 5 Challenge: Financial Aggregations & Analytics
- **Category Breakdown Query**:
  ```python
  select(ExpenseRecord.category, func.sum(ExpenseRecord.amount))
      .where(ExpenseRecord.user_id == user_id)
      .group_by(ExpenseRecord.category)
  ```
- **Monthly Total Query**: Menggunakan `func.extract("month", ...)` dan `func.extract("year", ...)` dengan proteksi `scalar_one() or 0`.
- Menghasilkan laporan keuangan bulanan lengkap dengan perhitungan persentase belanja per kategori.

---

## 🚀 3. Status Roadmap Saat Ini

| Fase | Topik | Status |
| :--- | :--- | :---: |
| **Phase 1** | Project Init & Environment (`uv`, `requirements.txt`) | ✅ Selesai |
| **Phase 2** | Domain Modeling & Validation (Pydantic v2) | ✅ Selesai |
| **Phase 3** | Core LLM Parsing & Tool Calling Loop (Gemini) | ✅ Selesai |
| **Phase 4** | Workflow Orchestration & Clarification (LangGraph) | ✅ Selesai |
| **Phase 5** | Data Persistence & Analytics (SQLAlchemy & Excel) | ✅ Selesai |
| **Phase 6** | Channel Integrations (Telegram Bot / Ingestion Engine) | ⏳ **Berikutnya** |

---

*Catatan ini dibuat secara otomatis sebagai referensi komprehensif bagi developer untuk implementasi skala enterprise.*
