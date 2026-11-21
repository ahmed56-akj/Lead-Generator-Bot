from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import (
    BUSINESS_NAME,
    BUSINESS_TAGLINE,
    SUPPORT_CONTACT,
    SERVICES,
    FAQ_ITEMS,
    is_admin
)
from database import record_user

def get_main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generate the main interactive menu keyboard."""
    buttons = [
        [InlineKeyboardButton("🚀 Get a Quote / Start Consultation", callback_data="funnel_start")],
        [
            InlineKeyboardButton("💼 Our Services", callback_data="menu_services"),
            InlineKeyboardButton("❓ FAQs", callback_data="menu_faq")
        ],
        [
            InlineKeyboardButton("📞 Contact Us", callback_data="menu_contact")
        ]
    ]
    if is_admin(user_id):
        buttons.append([InlineKeyboardButton("⚙️ Admin Dashboard", callback_data="admin_dashboard")])
    return InlineKeyboardMarkup(buttons)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - Welcomes the user and shows the main menu."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Record user in database
    await record_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        is_admin=is_admin(user.id)
    )

    welcome_text = (
        f"👋 *Welcome to {BUSINESS_NAME}!*, {user.first_name}!\n\n"
        f"_{BUSINESS_TAGLINE}_\n\n"
        "We are here to help you turn your ideas into high-performing solutions.\n"
        "Whether you need custom bots, web platforms, lead automation, or consulting, we've got you covered.\n\n"
        "👇 *Please select an option below to begin:*"
    )

    keyboard = get_main_menu_keyboard(user.id)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    user_id = update.effective_user.id
    help_text = (
        "🤖 *Bot Command Guide:*\n\n"
        "• /start - Open main menu and services\n"
        "• /quote - Start consultation form directly\n"
        "• /help - View this help guide\n"
        "• /cancel - Stop and reset current question session\n"
    )
    if is_admin(user_id):
        help_text += (
            "\n👑 *Admin Commands:*\n"
            "• /admin - Access management panel & lead stats\n"
            "• /export - Download all leads as a CSV file\n"
            "• /broadcast - Send message to all users\n"
        )

    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def services_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed list of business services."""
    query = update.callback_query
    await query.answer()

    services_text = f"💼 *Our Services & Solutions at {BUSINESS_NAME}:*\n\n"
    for s in SERVICES:
        services_text += f"• {s}\n"

    services_text += (
        "\n✅ Custom-built according to your business needs\n"
        "✅ Clean, scalable, production-grade implementation\n"
        "✅ Dedicated post-launch support and integration\n\n"
        "Ready to work with us? Click below to request a tailored quote!"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Get a Quote Now", callback_data="funnel_start")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ])

    await query.edit_message_text(services_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

async def faq_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show FAQ category buttons."""
    query = update.callback_query
    await query.answer()

    text = "❓ *Frequently Asked Questions*\n\nSelect a topic below to see answers:"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💼 Pricing & Packages", callback_data="faq_item:pricing"),
            InlineKeyboardButton("⏱ Delivery Time", callback_data="faq_item:delivery")
        ],
        [
            InlineKeyboardButton("🛠 Support & Warranty", callback_data="faq_item:support"),
            InlineKeyboardButton("✨ Bot Capabilities", callback_data="faq_item:features")
        ],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

async def faq_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display specific FAQ answer."""
    query = update.callback_query
    await query.answer()

    data = query.data.split(":")[-1]
    answer = FAQ_ITEMS.get(data, "Information is currently unavailable.")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to FAQs", callback_data="menu_faq")],
        [InlineKeyboardButton("🚀 Request a Quote", callback_data="funnel_start")]
    ])

    await query.edit_message_text(answer, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

async def contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display direct business contact information."""
    query = update.callback_query
    await query.answer()

    text = (
        f"📞 *Contact & Support Team:*\n\n"
        f"• Telegram: {SUPPORT_CONTACT}\n"
        f"• Business: {BUSINESS_NAME}\n\n"
        "Need a live consultation or have a special inquiry? Send us a direct message or submit your requirements through our form."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Fill Form / Get Quote", callback_data="funnel_start")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
