import asyncio
import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
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

from config import is_admin
from database import (
    get_lead_stats,
    get_recent_leads,
    get_lead_by_id,
    update_lead_status,
    export_leads_to_csv,
    get_all_user_ids
)

logger = logging.getLogger(__name__)

# Broadcast States
BROADCAST_MESSAGE, BROADCAST_CONFIRM = range(2)

def get_admin_dashboard_markup() -> InlineKeyboardMarkup:
    """Inline markup for admin panel dashboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 View Recent Leads", callback_data="admin_leads:0"),
            InlineKeyboardButton("📊 Refresh Stats", callback_data="admin_refresh")
        ],
        [
            InlineKeyboardButton("📥 Download CSV Export", callback_data="admin_export_csv"),
            InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast_start")
        ],
        [
            InlineKeyboardButton("🏠 Main User Menu", callback_data="menu_main")
        ]
    ])

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entrypoint for /admin command."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ *Access Denied.* You do not have administrator permissions.", parse_mode=ParseMode.MARKDOWN)
        return

    stats = await get_lead_stats()
    text = (
        "⚙️ *Lead Generation Admin Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 *Total Bot Users:* `{stats['total_users']}`\n"
        f"📥 *Total Leads Captured:* `{stats['total_leads']}`\n"
        f"📅 *Leads Today:* `{stats['leads_today']}`\n"
        f"🆕 *Pending / New Leads:* `{stats['new_leads']}`\n"
        f"📞 *Contacted Leads:* `{stats['contacted_leads']}`\n"
        f"🎯 *Qualified / Won:* `{stats['qualified_leads']}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Select an action below:"
    )

    markup = get_admin_dashboard_markup()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

async def admin_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Refresh stats on dashboard."""
    query = update.callback_query
    await admin_command(update, context)

async def admin_leads_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display paginated list of leads."""
    query = update.callback_query
    await query.answer()

    offset = int(query.data.split(":")[-1])
    limit = 5
    leads = await get_recent_leads(limit=limit, offset=offset)

    if not leads and offset == 0:
        await query.edit_message_text(
            "📭 No leads have been captured yet.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_dashboard")]
            ])
        )
        return

    text = f"📋 *Recent Leads (Page {offset // limit + 1})*\n━━━━━━━━━━━━━━━━━━━━\n"
    buttons = []

    for l in leads:
        status_emoji = "🆕" if l["status"] == "NEW" else ("📞" if l["status"] == "CONTACTED" else "🎯")
        text += (
            f"• *#{l['id']}* - {l['full_name']} ({status_emoji} {l['status']})\n"
            f"  Service: {l['service']} | Budget: {l['budget']}\n"
        )
        buttons.append([
            InlineKeyboardButton(f"🔍 View Lead #{l['id']}", callback_data=f"lead_view:{l['id']}")
        ])

    nav_row = []
    if offset >= limit:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"admin_leads:{offset - limit}"))
    if len(leads) == limit:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"admin_leads:{offset + limit}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_dashboard")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def admin_lead_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View details for a single lead with status change options."""
    query = update.callback_query
    await query.answer()

    lead_id = int(query.data.split(":")[-1])
    lead = await get_lead_by_id(lead_id)

    if not lead:
        await query.edit_message_text(
            "⚠️ Lead not found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Leads", callback_data="admin_leads:0")]
            ])
        )
        return

    text = (
        f"🔍 *Lead Details: #{lead['id']}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Full Name:* {lead['full_name']}\n"
        f"📱 *Phone:* `{lead['phone']}`\n"
        f"📧 *Email:* `{lead['email']}`\n"
        f"💼 *Service:* {lead['service']}\n"
        f"💰 *Budget:* {lead['budget']}\n"
        f"📝 *Requirements:* {lead['notes']}\n"
        f"📌 *Status:* *{lead['status']}*\n"
        f"📅 *Captured At:* {lead['created_at']}\n"
        f"✈️ *Telegram Username:* @{lead['username'] or 'N/A'} (ID: `{lead['user_id']}`)\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Change status or contact client:"
    )

    buttons = []
    # Contact buttons
    if lead["username"]:
        buttons.append([InlineKeyboardButton("💬 Open Telegram Chat", url=f"https://t.me/{lead['username']}")])

    # Status update row
    buttons.append([
        InlineKeyboardButton("📞 Contacted", callback_data=f"set_stat:{lead_id}:CONTACTED"),
        InlineKeyboardButton("🎯 Qualified", callback_data=f"set_stat:{lead_id}:QUALIFIED"),
        InlineKeyboardButton("❌ Lost", callback_data=f"set_stat:{lead_id}:LOST")
    ])

    buttons.append([InlineKeyboardButton("🔙 Back to Leads List", callback_data="admin_leads:0")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def admin_set_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update lead status from buttons."""
    query = update.callback_query
    parts = query.data.split(":")
    lead_id = int(parts[1])
    new_status = parts[2]

    await update_lead_status(lead_id, new_status)
    await query.answer(f"Status changed to {new_status}!", show_alert=False)

    # Re-render detail view
    query.data = f"lead_view:{lead_id}"
    await admin_lead_detail_callback(update, context)

async def alert_quick_contacted_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the quick 'Mark Contacted' button directly from new lead notification."""
    query = update.callback_query
    lead_id = int(query.data.replace("status_contacted_", ""))

    await update_lead_status(lead_id, "CONTACTED")
    await query.answer("Lead marked as Contacted!", show_alert=True)

    # Update original alert text
    original_text = query.message.text
    updated_text = original_text + "\n\n*(Status updated: ✅ CONTACTED)*"

    try:
        await query.edit_message_text(updated_text)
    except Exception:
        pass

async def export_csv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send CSV export file."""
    user = update.effective_user
    if not is_admin(user.id):
        return

    status_msg = None
    if update.callback_query:
        await update.callback_query.answer()
        status_msg = await update.callback_query.message.reply_text("⏳ Generating CSV export...")
    else:
        status_msg = await update.message.reply_text("⏳ Generating CSV export...")

    csv_file = await export_leads_to_csv()

    chat_id = update.effective_chat.id
    await context.bot.send_document(
        chat_id=chat_id,
        document=csv_file,
        filename=csv_file.name,
        caption="📊 *Here is your complete Leads Export (CSV)*",
        parse_mode=ParseMode.MARKDOWN
    )

    if status_msg:
        try:
            await status_msg.delete()
        except Exception:
            pass

# ==================== Broadcast Conversation ====================

async def broadcast_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiates broadcast flow."""
    user = update.effective_user
    if not is_admin(user.id):
        return ConversationHandler.END

    text = (
        "📢 *Broadcast Announcement*\n\n"
        "Please send the message you would like to broadcast to *all registered users*.\n\n"
        "Type /cancel to abort."
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    return BROADCAST_MESSAGE

async def broadcast_receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores draft broadcast message and requests confirmation."""
    message_text = update.message.text
    context.user_data["broadcast_text"] = message_text

    user_ids = await get_all_user_ids()
    count = len(user_ids)

    confirm_text = (
        "⚠️ *Confirm Broadcast Message*\n\n"
        f"Your message will be sent to *{count}* users.\n\n"
        f"📝 *Preview:*\n━━━━━━━━━━━━━━━━━━━━\n{message_text}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "Are you ready to send?"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Send Broadcast Now", callback_data="broadcast_confirm_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="broadcast_confirm_no")]
    ])

    await update.message.reply_text(confirm_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    return BROADCAST_CONFIRM

async def broadcast_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the broadcast message to all users."""
    query = update.callback_query
    await query.answer()

    if query.data == "broadcast_confirm_no":
        await query.edit_message_text("❌ Broadcast cancelled.")
        context.user_data.clear()
        return ConversationHandler.END

    message_text = context.user_data.get("broadcast_text", "")
    if not message_text:
        await query.edit_message_text("⚠️ No message found to broadcast.")
        return ConversationHandler.END

    await query.edit_message_text("⏳ Sending broadcast messages... Please wait.")

    user_ids = await get_all_user_ids()
    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
            await asyncio.sleep(0.05)  # Telegram rate limit safety
        except Exception as e:
            logger.debug(f"Could not deliver broadcast to {uid}: {e}")
            failed += 1

    summary = (
        "✅ *Broadcast Finished!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"• Delivered successfully: `{sent}`\n"
        f"• Failed / Blocked: `{failed}`\n"
        f"• Total attempted: `{len(user_ids)}`"
    )

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=summary,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Back to Dashboard", callback_data="admin_dashboard")]
        ]),
        parse_mode=ParseMode.MARKDOWN
    )

    context.user_data.clear()
    return ConversationHandler.END

async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels broadcast session."""
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Broadcast cancelled.")
    else:
        await update.message.reply_text("❌ Broadcast cancelled.")
    return ConversationHandler.END

def get_broadcast_conversation_handler():
    """Build ConversationHandler for broadcast."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(broadcast_start_command, pattern="^admin_broadcast_start$"),
            CommandHandler("broadcast", broadcast_start_command)
        ],
        states={
            BROADCAST_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_receive_message)
            ],
            BROADCAST_CONFIRM: [
                CallbackQueryHandler(broadcast_execute, pattern="^broadcast_confirm_")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", broadcast_cancel),
            CallbackQueryHandler(broadcast_cancel, pattern="^broadcast_confirm_no$")
        ],
        allow_reentry=True
    )
