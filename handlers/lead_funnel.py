import re
import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from telegram.constants import ParseMode

from config import (
    SERVICES,
    BUDGET_RANGES,
    ADMIN_IDS,
    BUSINESS_NAME
)
from database import save_lead, update_lead_status
from integrations.webhook import trigger_crm_webhook
from integrations.sheets import append_lead_to_google_sheet

logger = logging.getLogger(__name__)

# Conversation States
(
    STATE_NAME,
    STATE_EMAIL,
    STATE_PHONE,
    STATE_SERVICE,
    STATE_BUDGET,
    STATE_NOTES,
    STATE_CONFIRM
) = range(7)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

async def funnel_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for starting the lead generation funnel."""
    user = update.effective_user
    context.user_data.clear()
    context.user_data["user_id"] = user.id
    context.user_data["username"] = user.username or ""

    text = (
        "📋 *Project Consultation & Quote Request*\n\n"
        "Let's capture your requirements so our team can provide you with the best solution.\n\n"
        "Step 1/6: What is your *Full Name*? (or Business Name)"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN
        )

    return STATE_NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save name and ask for email."""
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("⚠️ Please enter a valid name (at least 2 characters).")
        return STATE_NAME

    context.user_data["full_name"] = name

    await update.message.reply_text(
        f"Nice to meet you, *{name}*!\n\n"
        "Step 2/6: What is your *Email Address*?\n"
        "_(We'll use this to send project proposals and updates)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_EMAIL

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validate and save email, then ask for phone number."""
    email = update.message.text.strip()

    if not EMAIL_REGEX.match(email):
        await update.message.reply_text(
            "⚠️ That doesn't look like a valid email address.\n"
            "Please provide a valid email (e.g. `john@example.com`):",
            parse_mode=ParseMode.MARKDOWN
        )
        return STATE_EMAIL

    context.user_data["email"] = email

    # Offer reply keyboard button for quick phone sharing or manual input
    contact_keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 Share Phone Number", request_contact=True)],
            [KeyboardButton("⏭ Skip Phone")]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Step 3/6: What is your *Phone / WhatsApp Number*?\n\n"
        "You can tap the button below to share automatically, or type it manually:",
        reply_markup=contact_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save phone number (from contact sharing or manual text)."""
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        text = update.message.text.strip()
        if text == "⏭ Skip Phone":
            phone = "Not Provided"
        else:
            phone = text

    context.user_data["phone"] = phone

    # Present services as inline buttons
    buttons = []
    for idx, service in enumerate(SERVICES):
        buttons.append([InlineKeyboardButton(service, callback_data=f"srv_{idx}")])

    keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "Step 4/6: Which *Service* are you interested in?",
        reply_markup=ReplyKeyboardRemove()
    )

    await update.message.reply_text(
        "Please select from the options below:",
        reply_markup=keyboard
    )
    return STATE_SERVICE

async def handle_service_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save selected service and present budget options."""
    query = update.callback_query
    await query.answer()

    data = query.data
    idx = int(data.replace("srv_", ""))
    selected_service = SERVICES[idx]
    context.user_data["service"] = selected_service

    # Present budget range buttons
    buttons = []
    for b_idx, budget in enumerate(BUDGET_RANGES):
        buttons.append([InlineKeyboardButton(budget, callback_data=f"bdg_{b_idx}")])

    keyboard = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(
        f"Selected Service: *{selected_service}*\n\n"
        "Step 5/6: What is your estimated *Budget Range*?",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_BUDGET

async def handle_budget_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save selected budget and ask for project notes/details."""
    query = update.callback_query
    await query.answer()

    data = query.data
    idx = int(data.replace("bdg_", ""))
    selected_budget = BUDGET_RANGES[idx]
    context.user_data["budget"] = selected_budget

    skip_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Skip this step", callback_data="skip_notes")]
    ])

    await query.edit_message_text(
        f"Budget: *{selected_budget}*\n\n"
        "Step 6/6: Please briefly describe your *project or requirements*:\n"
        "_(e.g., target features, deadline, specific integrations)_",
        reply_markup=skip_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_NOTES

async def handle_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save notes and present confirmation summary."""
    notes = update.message.text.strip()
    context.user_data["notes"] = notes
    return await show_summary(update, context)

async def handle_skip_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skipping notes."""
    query = update.callback_query
    await query.answer()
    context.user_data["notes"] = "None provided"
    return await show_summary(update, context, is_callback=True)

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback: bool = False):
    """Displays user review card before final submission."""
    data = context.user_data

    summary_text = (
        "🔍 *Please Review Your Information:*\n\n"
        f"• *Name:* {data.get('full_name')}\n"
        f"• *Email:* {data.get('email')}\n"
        f"• *Phone:* {data.get('phone')}\n"
        f"• *Service:* {data.get('service')}\n"
        f"• *Budget:* {data.get('budget')}\n"
        f"• *Requirements:* {data.get('notes')}\n\n"
        "Ready to submit your inquiry?"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm & Submit", callback_data="confirm_lead")],
        [InlineKeyboardButton("🔄 Restart Form", callback_data="restart_funnel")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_funnel")]
    ])

    if is_callback:
        await update.callback_query.edit_message_text(
            summary_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            summary_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    return STATE_CONFIRM

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes lead confirmation, saves to DB, alerts admins, triggers webhooks."""
    query = update.callback_query
    await query.answer()

    data = context.user_data
    user = update.effective_user

    # 1. Save Lead into database
    lead_id = await save_lead(
        user_id=data.get("user_id", user.id),
        username=data.get("username", user.username or ""),
        full_name=data.get("full_name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        service=data.get("service", ""),
        budget=data.get("budget", ""),
        notes=data.get("notes", "")
    )
    data["id"] = lead_id

    # 2. Trigger Integrations (CRM Webhook & Google Sheets)
    try:
        await trigger_crm_webhook(data)
    except Exception as e:
        logger.error(f"Error in webhook integration: {e}")

    try:
        await append_lead_to_google_sheet(data)
    except Exception as e:
        logger.error(f"Error in sheets integration: {e}")

    # 3. Notify Admins
    admin_alert = (
        f"🚨 *NEW LEAD CAPTURED!* (#{lead_id})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Client:* {data.get('full_name')}\n"
        f"📱 *Phone:* `{data.get('phone')}`\n"
        f"📧 *Email:* `{data.get('email')}`\n"
        f"💼 *Service:* {data.get('service')}\n"
        f"💰 *Budget:* {data.get('budget')}\n"
        f"📝 *Details:* {data.get('notes')}\n"
        f"✈️ *Telegram:* @{user.username if user.username else 'N/A'} (ID: `{user.id}`)\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    admin_keyboard_buttons = []
    if user.username:
        admin_keyboard_buttons.append(
            InlineKeyboardButton("💬 Open Telegram Chat", url=f"https://t.me/{user.username}")
        )
    admin_keyboard_buttons.append(
        InlineKeyboardButton("✅ Mark Contacted", callback_data=f"status_contacted_{lead_id}")
    )
    admin_markup = InlineKeyboardMarkup([admin_keyboard_buttons])

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_alert,
                reply_markup=admin_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to deliver admin notification to {admin_id}: {e}")

    # 4. Thank You confirmation to the user
    user_confirmation_text = (
        f"🎉 *Thank you, {data.get('full_name')}!*\n\n"
        f"Your inquiry has been successfully submitted under Reference ID: *#{lead_id}*.\n\n"
        "Our team has received your details and will get in touch with you shortly (usually within a few hours).\n\n"
        f"If you need immediate assistance, feel free to contact us via the main menu."
    )

    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
    ])

    await query.edit_message_text(
        user_confirmation_text,
        reply_markup=back_button,
        parse_mode=ParseMode.MARKDOWN
    )

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_funnel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels active consultation session."""
    context.user_data.clear()
    cancel_text = "❌ Consultation request has been cancelled. You can start again anytime using /start."

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            cancel_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
            ])
        )
    else:
        await update.message.reply_text(
            cancel_text,
            reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END

def get_lead_conversation_handler():
    """Build and return the complete Lead Generation ConversationHandler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(funnel_entry, pattern="^funnel_start$"),
            CommandHandler("quote", funnel_entry)
        ],
        states={
            STATE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)
            ],
            STATE_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)
            ],
            STATE_PHONE: [
                MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), handle_phone)
            ],
            STATE_SERVICE: [
                CallbackQueryHandler(handle_service_choice, pattern="^srv_")
            ],
            STATE_BUDGET: [
                CallbackQueryHandler(handle_budget_choice, pattern="^bdg_")
            ],
            STATE_NOTES: [
                CallbackQueryHandler(handle_skip_notes, pattern="^skip_notes$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_notes)
            ],
            STATE_CONFIRM: [
                CallbackQueryHandler(handle_confirmation, pattern="^confirm_lead$"),
                CallbackQueryHandler(funnel_entry, pattern="^restart_funnel$"),
                CallbackQueryHandler(cancel_funnel, pattern="^cancel_funnel$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_funnel),
            CallbackQueryHandler(cancel_funnel, pattern="^cancel_funnel$")
        ],
        allow_reentry=True
    )
