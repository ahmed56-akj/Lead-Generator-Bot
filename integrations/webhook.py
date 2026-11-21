import logging
import httpx
from config import CRM_WEBHOOK_URL

logger = logging.getLogger(__name__)

async def trigger_crm_webhook(lead_data: dict) -> bool:
    """
    Sends the new lead data as JSON to the configured CRM or automation webhook.
    Compatible with Zapier, Make.com, n8n, HubSpot, Pabbly, or custom API endpoints.
    """
    if not CRM_WEBHOOK_URL:
        logger.debug("CRM_WEBHOOK_URL is not configured; skipping webhook dispatch.")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(CRM_WEBHOOK_URL, json=lead_data)
            if response.status_code in [200, 201, 202, 204]:
                logger.info(f"Successfully posted lead #{lead_data.get('id')} to CRM webhook.")
                return True
            else:
                logger.warning(
                    f"CRM webhook returned non-success code: {response.status_code} - {response.text}"
                )
                return False
    except Exception as e:
        logger.error(f"Error sending lead to CRM webhook: {e}")
        return False
