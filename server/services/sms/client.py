"""Twilio SMS client — send outbound messages via the REST API."""

from __future__ import annotations

import httpx

from ...config import get_settings
from ...logging_config import logger

_TWILIO_API = "https://api.twilio.com/2010-04-01"


def _auth() -> tuple[str, str]:
    s = get_settings()
    return (s.twilio_account_sid or "", s.twilio_auth_token or "")


def _from_number() -> str:
    return get_settings().twilio_phone_number or ""


async def send_sms(to: str, body: str) -> None:
    """Send an SMS asynchronously via Twilio REST API."""
    sid, token = _auth()
    if not sid or not token:
        logger.warning("Twilio credentials missing — SMS not sent")
        return

    url = f"{_TWILIO_API}/Accounts/{sid}/Messages.json"
    data = {"From": _from_number(), "To": to, "Body": body[:1600]}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, data=data, auth=(sid, token), timeout=15.0)
            resp.raise_for_status()
            logger.info(f"SMS sent to {to}")
        except Exception as exc:
            logger.error(f"Twilio send failed: {exc}")


def send_sms_sync(to: str, body: str) -> None:
    """Send an SMS synchronously (used from sync tool handlers)."""
    sid, token = _auth()
    if not sid or not token:
        logger.warning("Twilio credentials missing — SMS not sent")
        return

    url = f"{_TWILIO_API}/Accounts/{sid}/Messages.json"
    data = {"From": _from_number(), "To": to, "Body": body[:1600]}

    try:
        resp = httpx.post(url, data=data, auth=(sid, token), timeout=15.0)
        resp.raise_for_status()
        logger.info(f"SMS sent to {to}")
    except Exception as exc:
        logger.error(f"Twilio send failed: {exc}")


__all__ = ["send_sms", "send_sms_sync"]
