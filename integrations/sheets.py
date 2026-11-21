import logging
import os
from config import GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SHEET_NAME

logger = logging.getLogger(__name__)

async def append_lead_to_google_sheet(lead_data: dict) -> bool:
    """
    Appends the lead row into a Google Sheet using a service account credentials JSON file.
    Requires `gspread` if activated.
    """
    if not GOOGLE_SERVICE_ACCOUNT_JSON or not os.path.exists(GOOGLE_SERVICE_ACCOUNT_JSON):
        logger.debug("Google service account JSON not set or file does not exist; skipping Sheets sync.")
        return False

    try:
        import gspread
        gc = gspread.service_account(filename=GOOGLE_SERVICE_ACCOUNT_JSON)
        sh = gc.open(GOOGLE_SHEET_NAME)
        worksheet = sh.sheet1

        row = [
            str(lead_data.get("id", "")),
            str(lead_data.get("user_id", "")),
            lead_data.get("username", "") or "",
            lead_data.get("full_name", ""),
            lead_data.get("email", ""),
            lead_data.get("phone", ""),
            lead_data.get("service", ""),
            lead_data.get("budget", ""),
            lead_data.get("notes", ""),
            lead_data.get("status", "NEW"),
            lead_data.get("created_at", "")
        ]

        worksheet.append_row(row)
        logger.info(f"Appended lead #{lead_data.get('id')} to Google Sheet: {GOOGLE_SHEET_NAME}")
        return True
    except ImportError:
        logger.warning("gspread library is not installed. To sync with Google Sheets, run: pip install gspread")
        return False
    except Exception as e:
        logger.error(f"Failed to append row to Google Sheets: {e}")
        return False
