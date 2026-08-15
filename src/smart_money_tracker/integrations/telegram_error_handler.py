from telegram.error import TimedOut
from telegram.ext import ContextTypes
import logging

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log error secara terstruktur dan tangani graceful shutdown."""
    if isinstance(context.error, TimedOut):
        logger.warning("Telegram polling timed out (Normal jika koneksi sempat terputus).")
        return
    logger.error("Exception saat memproses update:", exc_info=context.error)