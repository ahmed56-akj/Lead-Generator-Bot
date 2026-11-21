import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Telegram Bot Token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Admin Telegram IDs (can be multiple separated by commas)
ADMIN_IDS_RAW = os.getenv("ADMIN_CHAT_IDS", "")
ADMIN_IDS = set()
for item in ADMIN_IDS_RAW.split(","):
    item = item.strip()
    if item.isdigit():
        ADMIN_IDS.add(int(item))

# Business Branding
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Apex Digital Agency")
BUSINESS_TAGLINE = os.getenv("BUSINESS_TAGLINE", "Automate, Grow, and Scale your Business")
SUPPORT_CONTACT = os.getenv("SUPPORT_CONTACT", "@ApexSupport")

# Services offered (displayed as selection buttons)
SERVICES = [
    "🌐 Web & App Development",
    "📈 Lead Gen & Digital Marketing",
    "🤖 Telegram & AI Automation",
    "📊 CRM & Workflow Setup",
    "💡 Other / Custom Consulting"
]

# Budget ranges (displayed as selection buttons)
BUDGET_RANGES = [
    "💵 Under $500",
    "💵 $500 - $1,500",
    "💵 $1,500 - $5,000",
    "🚀 $5,000+"
]

# Database configuration
DB_PATH = BASE_DIR / "leads.db"

# Optional integrations
CRM_WEBHOOK_URL = os.getenv("CRM_WEBHOOK_URL", "").strip()
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Leads").strip()

# Optional AI Assistant configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "none").strip().lower()
AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "").strip()

# Built-in FAQ questions & answers
FAQ_ITEMS = {
    "pricing": (
        "💼 *Pricing & Packages:*\n"
        "Our pricing depends on the scope and complexity of your project.\n"
        "• Starter Package: Starting from $300\n"
        "• Growth Package: Starting from $800\n"
        "• Enterprise / Custom: Tailored quote\n\n"
        "Click *'Get a Free Quote'* to get an accurate estimate tailored to your needs!"
    ),
    "delivery": (
        "⏱ *Delivery Timeline:*\n"
        "Standard bot projects usually take 3 to 7 business days.\n"
        "Complex enterprise builds with CRM and custom integrations take 1 to 3 weeks."
    ),
    "support": (
        "🛠 *Support & Maintenance:*\n"
        "We provide 30 days of free post-launch support and bug fixes for all projects.\n"
        "Ongoing monthly maintenance plans are also available."
    ),
    "features": (
        "✨ *Key Bot Capabilities:*\n"
        "• 24/7 automated lead capture\n"
        "• Smart phone & email validation\n"
        "• Instant admin alert notifications\n"
        "• Direct export to CSV / Excel\n"
        "• CRM & Google Sheets integration\n"
        "• Broadcast messaging to all subscribers"
    )
}

def is_admin(user_id: int) -> bool:
    """Check if a given user ID has admin privileges."""
    return user_id in ADMIN_IDS
