@echo off
title Telegram Lead Generation Bot
echo ========================================================
echo   Telegram Lead Generation & CRM Bot Runner
echo ========================================================
echo.

cd /d "%~dp0"

IF NOT EXIST "venv" (
    echo [1/3] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Ensure Python 3.10+ is installed.
        pause
        exit /b 1
    )
)

echo [2/3] Activating virtual environment and installing dependencies...
call venv\Scripts\activate
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

IF NOT EXIST ".env" (
    echo.
    echo [ATTENTION] No .env file detected!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo ----------------------------------------------------
    echo [ACTION REQUIRED]
    echo Open the newly created .env file in Notepad:
    echo 1. Insert your TELEGRAM_BOT_TOKEN from @BotFather
    echo 2. Insert your ADMIN_CHAT_IDS from @userinfobot
    echo ----------------------------------------------------
    echo.
    pause
)

echo [3/3] Starting Bot...
python bot.py
pause
