# 🤖 Custom Telegram Lead Generation & CRM Bot

A production-ready, modular **Telegram Lead Generation Bot** designed to capture customer requirements, qualify leads step-by-step, store entries in a database, send real-time alerts to admins, and sync with your favorite CRM and automation platforms 24/7.

---

## ✨ Features

- 🌟 **Automated Welcome & Onboarding:** Greets visitors with custom branding, company intro, and interactive buttons.
- 📋 **Step-by-Step Lead Qualification Funnel:**
  - Full Name / Business Name
  - Email address (with real-time regex validation)
  - Phone / WhatsApp number (with 1-tap Telegram contact sharing or manual input)
  - Service required (interactive buttons)
  - Budget range selection
  - Project specifications and timeline
  - Summary review & confirmation card
- 🚨 **Instant Admin Notifications:** Admins immediately receive full lead details with 1-click links to chat with the lead or mark them as contacted.
- ⚙️ **Comprehensive Admin Dashboard (`/admin`):**
  - Real-time lead metrics (Total Leads, Leads Today, Contacted, Qualified)
  - Interactive lead browser with pagination
  - Status pipeline management (`NEW` ➡️ `CONTACTED` ➡️ `QUALIFIED` ➡️ `LOST`)
  - **Instant CSV Export:** Download all leads directly inside Telegram as an Excel-ready CSV.
  - **Broadcast Announcements:** Mass-send updates or offers to all past users.
- 🔗 **CRM & Webhook Integration:** Sends lead JSON payloads to Zapier, Make.com, n8n, HubSpot, or any custom API webhook.
- 🤖 **Smart FAQ & AI Assistant:** Handles general user inquiries with smart keyword matching or OpenAI / Google Gemini AI.
- 🗄 **Zero-Config Database:** Built-in SQLite database that works right out of the box.

---

## 📁 Project Structure

```text
simple project/
├── bot.py                  # Main entrypoint and bot initializer
├── config.py               # Settings, environment variables, services & budgets
├── database.py             # SQLite database manager & CSV export logic
├── handlers/
│   ├── __init__.py
│   ├── user.py             # /start, /help, FAQ, and service catalog menus
│   ├── lead_funnel.py      # ConversationHandler for lead collection
│   ├── admin.py            # /admin dashboard, CSV export, and broadcasts
│   └── ai_assistant.py     # AI fallback and smart FAQ responder
├── integrations/
│   ├── __init__.py
│   ├── webhook.py          # CRM / Zapier / Make webhook dispatcher
│   └── sheets.py           # Optional Google Sheets sync
├── .env.example            # Environment configuration template
├── .gitignore
├── requirements.txt        # Python package dependencies
├── run.bat                 # 1-Click launcher script for Windows
└── README.md               # Complete setup documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed ([Download Python](https://www.python.org/downloads/))

### 2. Get Your Telegram Credentials

1. **Bot Token:**
   - Open Telegram and search for [`@BotFather`](https://t.me/BotFather).
   - Send `/newbot`, choose a name and username for your bot.
   - Copy the API Token provided.

2. **Admin Chat ID:**
   - Search for [`@userinfobot`](https://t.me/userinfobot) on Telegram.
   - Send `/start` to see your numeric **Id** (e.g. `123456789`).

### 3. Configure `.env`

Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```

Open `.env` and fill in your values:
```env
TELEGRAM_BOT_TOKEN=your_token_from_botfather
ADMIN_CHAT_IDS=your_numeric_telegram_id

BUSINESS_NAME=Apex Digital Agency
BUSINESS_TAGLINE=We help businesses scale with custom digital solutions
SUPPORT_CONTACT=@ApexSupport
```

### 4. Run the Bot

#### Option A: Windows 1-Click (Recommended)
Double-click `run.bat`. It will automatically:
1. Create a virtual environment (`venv`).
2. Install all required dependencies.
3. Start the bot.

#### Option B: Manual Terminal Execution
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac / Linux:
# source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start the bot
python bot.py
```

---

## 🛠 Customizing Your Bot

### Change Services & Budget Ranges
Open [config.py](file:///C:/Users/Ahmad/OneDrive/Desktop/simple%20project/config.py) and modify:
```python
SERVICES = [
    "🌐 Web & App Development",
    "📈 Lead Gen & Digital Marketing",
    "🤖 Telegram & AI Automation",
    "📊 CRM & Workflow Setup",
    "💡 Other / Custom Consulting"
]

BUDGET_RANGES = [
    "💵 Under $500",
    "💵 $500 - $1,500",
    "💵 $1,500 - $5,000",
    "🚀 $5,000+"
]
```

### Connect to CRM / Webhook
In your `.env` file, set:
```env
CRM_WEBHOOK_URL=https://hook.eu1.make.com/your-webhook-id
```
Whenever a lead is submitted, a JSON payload is immediately dispatched to your webhook.

### Enable AI-Powered Answers (Optional)
To let the bot answer custom client questions using Google Gemini or OpenAI:
```env
AI_PROVIDER=gemini       # or openai
AI_API_KEY=your_api_key_here
```

---

## 👑 Admin Commands

- `/admin` - Open the interactive admin dashboard.
- `/export` - Download the CSV export of all captured leads.
- `/broadcast` - Mass-send an announcement to all users who have interacted with the bot.

---

## 🔒 License & Support
Custom developed for high-converting lead generation workflows. Clean, modular, and ready for deployment on any Windows server, Linux VPS, or cloud platform.
