from httpcore import NetworkError
from telegram.error import TimedOut
import asyncio
from smart_money_tracker.integrations.telegram_error_handler import global_error_handler
from telegram.request import HTTPXRequest
from telegram.ext import CallbackQueryHandler
from multiprocessing.sharedctypes import Value
import os, uuid, base64, io
from datetime import datetime
from telegram import Update, Message

from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from langchain_core.messages import HumanMessage

from smart_money_tracker.core.config import settings
from smart_money_tracker.agents.graph import build_tracker_graph
from smart_money_tracker.storage.repository import repository
from smart_money_tracker.service.excel import excel_service


graph = build_tracker_graph()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start."""
    welcome_text = (
        "👋 **Halo! Saya Smart Money Tracker Bot.**\n\n"
        "Kirimkan catatan pengeluaran Anda dengan bahasa natural sehari-hari. Contoh:\n"
        "• _Beli kopi di Starbucks 25rb pake QRIS tadi pagi_\n"
        "• _Belanja bulanan di Superindo 350k debit_\n"
        "• _Beli buku di Amazon $10 USD_\n\n"
        "**Perintah Tersedia:**\n"
        "/report - Lihat ringkasan pengeluaran bulan ini\n"
        "/export - Unduh laporan keuangan dalam format file Excel (.xlsx)\n"
        "/help - Bantuan penggunaan"
    )

    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handler untuk command /cancel."""
    context.user_data["thread_id"] = str(uuid.uuid4())
    await update.message.reply_text("🔄 Sesi percakapan telah di-reset. Anda bisa mencatat transaksi baru.")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /report."""
    user_id = f"tg_{update.effective_user.id}"
    current_month = datetime.now().month
    current_year = datetime.now().year

    monthly_total = repository.get_monthly_total(user_id, month=current_month, year=current_year)
    breakdown = repository.get_category_breakdown(user_id)

    if monthly_total == 0 and not breakdown:
        await update.message.reply_text("Belum ada catatan pengeluaran untuk bulan ini.")
        return

    lines = [
        f"📊 **LAPORAN PENGELUARAN BULAN {current_year}-{current_month:02d}**\n",
        f"💰 **Total Pengeluaran:** IDR {monthly_total:,.2f}\n",
        "📈 **Rincian Per Kategori:**"
    ]

    for cat, amount in breakdown.items():
        pct = (amount / monthly_total) * 100 if monthly_total > 0 else 0
        lines.append(f"• {cat.upper()}: IDR {amount:,.2f} ({pct:.1f}%)")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /export (Kirim file Excel ke user)."""
    user_id = f"tg_{update.effective_user.id}"
    file_name = f"laporan_pengeluaran_{user_id}.xlsx"
    await update.message.reply_text("⏳ Sedang membuat file Excel laporan Anda...")
    
    excel_path = excel_service.export(user_id=user_id, file_path=file_name)
    if not excel_path or not os.path.exists(excel_path):
        await update.message.reply_text("Belum ada data pengeluaran untuk diekspor.")
        return
    # Kirim file dokumen ke chat Telegram
    with open(excel_path, "rb") as doc:
        await update.message.reply_document(
            document=doc,
            filename="Laporan_Keuangan.xlsx",
            caption="📁 Berikut laporan catatan pengeluaran Anda."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk memproses pesan teks pengeluaran via LangGraph."""
    user_text = update.message.text
    chat_id = update.effective_chat.id
    user_id = f"tg_{update.effective_user.id}"
    today_str = datetime.now().strftime("%Y-%m-%d")

    status_msg = await update.message.reply_text("⏳ Sedang memproses catatan pengeluaran Anda...", parse_mode="Markdown")

    thread_id = context.user_data.get("thread_id")
    if not thread_id:
        thread_id = str(uuid.uuid4())
        context.user_data["thread_id"] = thread_id
    
    config = {"configurable": {"thread_id": thread_id}}
    input_data = {
        "messages": [HumanMessage(content=user_text)],
        "user_id": user_id,
        "ref_date": today_str,
        "channel": "telegram"
    }


    try:
        # 2. Berikan action typing & batasi waktu maksimal proses (misal 25 detik)
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        # Jalankan LangGraph dengan asyncio timeout guard
        # (karena graph.invoke bersifat synchronous, kita bungkus dalam asyncio.to_thread)
        output = await asyncio.wait_for(
            asyncio.to_thread(graph.invoke, input_data, config),
            timeout=25.0
        )
        final_message = output.get("final_message", "Maaf, terjadi kesalahan saat memproses catatan Anda.")
        status = output.get("status")
        # 3. Buat tombol inline jika sukses
        reply_markup = None
        keyboard = []
        if status == "success":
            trxs = output.get("enriched_transactions", [])
            for tx in trxs:
                keyboard.append([
                    InlineKeyboardButton(f"🗑️ Batalkan ({tx.item.merchant})", callback_data=f"del_{tx.id}")
                ])
            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
        # 4. Update pesan loading menjadi hasil akhir
        await status_msg.edit_text(final_message, parse_mode="Markdown", reply_markup=reply_markup)
        if status == "success":
            context.user_data["thread_id"] = str(uuid.uuid4())
    except asyncio.TimeoutError:
        # Jika LLM / internet terlalu lambat melebihi 25 detik
        await status_msg.edit_text(
            "⚠️ **Waktu Habis (Timeout)!**\n"
            "Koneksi sedang lambat saat menghubungi AI Agent. Silakan coba kirim ulang pesan Anda.",
            parse_mode="Markdown"
        )
    except (TimedOut, NetworkError) as net_err:
        # Jika ada gangguan jaringan Telegram
        await status_msg.edit_text(
            "⚠️ **Gangguan Jaringan!**\n"
            "Gagal terhubung ke server Telegram. Mohon periksa koneksi internet Anda.",
            parse_mode="Markdown"
        )
    except Exception as e:
        # Error umum lainnya
        await status_msg.edit_text(
            f"❌ Terjadi kesalahan: `{str(e)}`",
            parse_mode="Markdown"
        )

async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handler untuk memproses pesan gambar pengeluaran via LangGraph."""
    user_text: Message = update.message
    photo_receipt = user_text.photo[-1]
    caption = user_text.caption or ""

    chat_id = update.effective_chat.id
    user_id = f"tg_{update.effective_user.id}"
    today_str = datetime.now().strftime("%Y-%m-%d")

    status_msg = await update.message.reply_text("⏳ Sedang memproses catatan pengeluaran Anda...", parse_mode="Markdown")


    try:
        file = await context.bot.get_file(photo_receipt.file_id)
        image_bytes = await file.download_as_bytearray()
        base64_string = base64.b64encode(image_bytes).decode("utf-8")

        thread_id = context.user_data.get("thread_id")
        if not thread_id:
            thread_id = str(uuid.uuid4())
            context.user_data["thread_id"] = thread_id
        
        config = {"configurable": {"thread_id": thread_id}}
        msgs = [
            {"type": "text", "text": "Extract all expense items from this receipt image."},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_string}"}
        ]

        if caption:
            msgs.append({"type": "text", "text": f"Caption: {caption}"})
        input_data = {
            "messages": [HumanMessage(content=msgs)],
            "user_id": user_id,
            "ref_date": today_str,
            "channel": "telegram"
        }

        # 2. Berikan action typing & batasi waktu maksimal proses (misal 25 detik)
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        # Jalankan LangGraph dengan asyncio timeout guard
        # (karena graph.invoke bersifat synchronous, kita bungkus dalam asyncio.to_thread)
        output = await asyncio.wait_for(
            asyncio.to_thread(graph.invoke, input_data, config),
            timeout=60.0
        )
        final_message = output.get("final_message", "Maaf, terjadi kesalahan saat memproses catatan Anda.")
        status = output.get("status")
        # 3. Buat tombol inline jika sukses
        reply_markup = None
        keyboard = []
        if status == "success":
            trxs = output.get("enriched_transactions", [])
            for tx in trxs:
                keyboard.append([
                    InlineKeyboardButton(f"🗑️ Batalkan ({tx.item.merchant})", callback_data=f"del_{tx.id}")
                ])
            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
        # 4. Update pesan loading menjadi hasil akhir
        await status_msg.edit_text(final_message, parse_mode="Markdown", reply_markup=reply_markup)
        if status == "success":
            context.user_data["thread_id"] = str(uuid.uuid4())
    except asyncio.TimeoutError:
        # Jika LLM / internet terlalu lambat melebihi 25 detik
        await status_msg.edit_text(
            "⚠️ **Waktu Habis (Timeout)!**\n"
            "Koneksi sedang lambat saat menghubungi AI Agent. Silakan coba kirim ulang pesan Anda.",
            parse_mode="Markdown"
        )
    except (TimedOut, NetworkError) as net_err:
        # Jika ada gangguan jaringan Telegram
        await status_msg.edit_text(
            "⚠️ **Gangguan Jaringan!**\n"
            "Gagal terhubung ke server Telegram. Mohon periksa koneksi internet Anda.",
            parse_mode="Markdown"
        )
    except Exception as e:
        # Error umum lainnya
        await status_msg.edit_text(
            f"❌ Terjadi kesalahan: `{str(e)}`",
            parse_mode="Markdown"
        )

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if query.data and query.data.startswith("del_"):
        data_split = query.data.split("_", 1)
        if len(data_split) != 2:
            return
        user_id = f"tg_{query.from_user.id}"
        tx_id = data_split[1]
        
        deleted = repository.delete_transaction(tx_id, user_id)
        if not deleted:
            await query.edit_message_text(
                "❌ Gagal menghapus transaksi. Transaksi mungkin sudah dihapus atau tidak ditemukan."
            )
            return
        
        # Balas pesan untuk konfirmasi
        await query.edit_message_text(
            f"✅ Transaksi {tx_id} berhasil dihapus.",
            reply_markup=None  # Hapus tombol inline
        )


def run_telegram_bot():
    """Menjalankan bot Telegram menggunakan Polling."""
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    request_config = HTTPXRequest(
        connect_timeout=15.0,  # 15 detik batas koneksi awal
        read_timeout=30.0,     # 30 detik batas membaca respon Telegram
        write_timeout=20.0,
        pool_timeout=10.0,
    )

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .request(request_config)
        .get_updates_request(request_config)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))

    app.add_error_handler(global_error_handler)

    print("🤖 Telegram Bot sedang berjalan... (Tekan Ctrl+C untuk berhenti)")
    app.run_polling()
    

    