import sys
import logging

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config import BOT_TOKEN, BUSINESS_NAME
from database import init_db
from handlers.user import (
    start_command,
    help_command,
    services_callback,
    faq_menu_callback,
    faq_detail_callback,
    contact_callback
)
from handlers.lead_funnel import get_lead_conversation_handler
from handlers.admin import (
    admin_command,
    admin_refresh_callback,
    admin_leads_list_callback,
    admin_lead_detail_callback,
    admin_set_status_callback,
    alert_quick_contacted_callback,
    export_csv_command,
    get_broadcast_conversation_handler
)
from handlers.ai_assistant import handle_general_message

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    """Initializes the database schema when the application boots."""
    logger.info("Initializing database...")
    await init_db()
    logger.info(f"Database ready. {BUSINESS_NAME} Lead Bot is running!")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log uncaught errors."""
    logger.error("Exception while handling an update:", exc_info=context.error)

def main():
    if not BOT_TOKEN or "ABCdefGhIJKlmNoPQRsTUVwxyZ" in BOT_TOKEN:
        print("\n" + "=" * 60)
        print("⚠️  MISSING TELEGRAM_BOT_TOKEN")
        print("=" * 60)
        print("Please configure your bot token in the .env file:")
        print("1. Copy .env.example to .env")
        print("2. Open .env and set TELEGRAM_BOT_TOKEN=<your_token_from_BotFather>")
        print("3. Add your Telegram ID to ADMIN_CHAT_IDS (get it from @userinfobot)")
        print("=" * 60 + "\n")
        sys.exit(1)

    # Build Telegram Application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # 1. Conversation Handlers (High Priority)
    application.add_handler(get_lead_conversation_handler())
    application.add_handler(get_broadcast_conversation_handler())

    # 2. Main Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("export", export_csv_command))

    # 3. Interactive Callback Query Handlers
    application.add_handler(CallbackQueryHandler(start_command, pattern="^menu_main$"))
    application.add_handler(CallbackQueryHandler(services_callback, pattern="^menu_services$"))
    application.add_handler(CallbackQueryHandler(faq_menu_callback, pattern="^menu_faq$"))
    application.add_handler(CallbackQueryHandler(faq_detail_callback, pattern="^faq_item:"))
    application.add_handler(CallbackQueryHandler(contact_callback, pattern="^menu_contact$"))

    # Admin Callback Handlers
    application.add_handler(CallbackQueryHandler(admin_command, pattern="^admin_dashboard$"))
    application.add_handler(CallbackQueryHandler(admin_refresh_callback, pattern="^admin_refresh$"))
    application.add_handler(CallbackQueryHandler(admin_leads_list_callback, pattern="^admin_leads:"))
    application.add_handler(CallbackQueryHandler(admin_lead_detail_callback, pattern="^lead_view:"))
    application.add_handler(CallbackQueryHandler(admin_set_status_callback, pattern="^set_stat:"))
    application.add_handler(CallbackQueryHandler(alert_quick_contacted_callback, pattern="^status_contacted_"))
    application.add_handler(CallbackQueryHandler(export_csv_command, pattern="^admin_export_csv$"))

    # 4. Fallback Freeform Message Handler (AI or smart FAQ)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_general_message))

    # Error handling
    application.add_error_handler(error_handler)

    print(f"🚀 Starting {BUSINESS_NAME} Lead Generation Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
