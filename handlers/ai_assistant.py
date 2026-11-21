import logging
import httpx
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import (
    AI_PROVIDER,
    AI_API_KEY,
    AI_MODEL,
    BUSINESS_NAME,
    BUSINESS_TAGLINE,
    SERVICES
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    f"You are the AI assistant for {BUSINESS_NAME}. {BUSINESS_TAGLINE}. "
    f"We offer: {', '.join(SERVICES)}. "
    "Keep answers friendly, concise (under 3 paragraphs), and always encourage the user "
    "to submit their requirements by typing /quote or clicking the 'Get a Quote' button."
)

async def ask_gemini(user_prompt: str) -> str:
    """Send prompt to Google Gemini API."""
    model = AI_MODEL or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={AI_API_KEY}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"System context: {SYSTEM_PROMPT}\n\nClient inquiry: {user_prompt}"}]
            }
        ]
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

async def ask_openai(user_prompt: str) -> str:
    """Send prompt to OpenAI API."""
    model = AI_MODEL or "gpt-4o-mini"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 300
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]

async def handle_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles any plain text message outside the conversation funnel."""
    user_msg = update.message.text.strip()
    msg_lower = user_msg.lower()

    # Default fallback reply markup
    cta_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Get a Custom Quote", callback_data="funnel_start")],
        [InlineKeyboardButton("💼 View Services", callback_data="menu_services")],
        [InlineKeyboardButton("📞 Contact Us Directly", callback_data="menu_contact")]
    ])

    # 1. Check if AI response is configured
    if AI_API_KEY and AI_PROVIDER in ["gemini", "openai"]:
        try:
            await update.message.chat.send_action("typing")
            if AI_PROVIDER == "gemini":
                reply = await ask_gemini(user_msg)
            else:
                reply = await ask_openai(user_msg)

            await update.message.reply_text(
                reply,
                reply_markup=cta_keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        except Exception as e:
            logger.error(f"AI Assistant error: {e}")

    # 2. Smart Keyword Match Fallback
    if any(k in msg_lower for k in ["price", "cost", "how much", "rate", "fee"]):
        reply = (
            f"💼 *Pricing at {BUSINESS_NAME}:*\n\n"
            "Our pricing depends on your exact project features and integrations.\n"
            "To receive a custom, transparent estimate for your business, click the button below!"
        )
    elif any(k in msg_lower for k in ["service", "what do you do", "features", "offer"]):
        services_list = "\n".join([f"• {s}" for s in SERVICES])
        reply = (
            f"🛠 *What We Offer:*\n\n{services_list}\n\n"
            "Tell us what you are looking to build and we'll make it happen!"
        )
    elif any(k in msg_lower for k in ["hello", "hi", "hey", "hola"]):
        reply = (
            f"Hello! 👋 Welcome to *{BUSINESS_NAME}*.\n\n"
            "How can we assist you with your project today?"
        )
    else:
        reply = (
            f"Thanks for your message! 😊\n\n"
            f"At *{BUSINESS_NAME}*, we build automated solutions tailored for your workflow.\n"
            "Would you like to get a quote or speak with a specialist?"
        )

    await update.message.reply_text(
        reply,
        reply_markup=cta_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
