"""Google Calendar service via Composio."""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from ...logging_config import logger

_ACTIVE_USER_ID_LOCK = threading.Lock()
_ACTIVE_USER_ID: Optional[str] = None


def get_active_calendar_user_id() -> Optional[str]:
    global _ACTIVE_USER_ID
    with _ACTIVE_USER_ID_LOCK:
        if _ACTIVE_USER_ID is not None:
            return _ACTIVE_USER_ID
    from ..account_state import get_user_id as _load
    persisted = _load("calendar")
    if persisted:
        with _ACTIVE_USER_ID_LOCK:
            _ACTIVE_USER_ID = persisted
        return persisted
    return None


def _set_active_calendar_user_id(user_id: Optional[str]) -> None:
    from ..account_state import set_user_id as _persist
    sanitized = (user_id or "").strip() or None
    with _ACTIVE_USER_ID_LOCK:
        global _ACTIVE_USER_ID
        _ACTIVE_USER_ID = sanitized
    _persist("calendar", sanitized)


def execute_calendar_tool(
    tool_name: str,
    composio_user_id: str,
    *,
    arguments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    from ..gmail.client import _get_composio_client, _normalize_tool_response

    prepared = {k: v for k, v in (arguments or {}).items() if v is not None}
    try:
        client = _get_composio_client()
        result = client.client.tools.execute(
            tool_name,
            user_id=composio_user_id,
            arguments=prepared,
        )
        return _normalize_tool_response(result)
    except Exception as exc:
        logger.exception("calendar tool execution failed", extra={"tool": tool_name})
        raise RuntimeError(f"{tool_name} failed: {exc}") from exc


def initiate_connect(user_id: str, auth_config_id: str) -> Dict[str, Any]:
    from ..gmail.client import _get_composio_client

    _set_active_calendar_user_id(user_id)
    client = _get_composio_client()
    # Reuse existing connection if already present
    try:
        existing = client.connected_accounts.list(user_ids=[user_id], toolkit_slugs=["GOOGLECALENDAR"], statuses=["ACTIVE"])
        existing_data = getattr(existing, "data", None) or (existing if isinstance(existing, list) else None)
        if existing_data:
            return {"ok": True, "redirect_url": None, "already_connected": True, "user_id": user_id}
    except Exception:
        pass
    req = client.connected_accounts.initiate(user_id=user_id, auth_config_id=auth_config_id)
    return {
        "ok": True,
        "redirect_url": getattr(req, "redirect_url", None) or getattr(req, "redirectUrl", None),
        "user_id": user_id,
    }


def fetch_status(user_id: str) -> Dict[str, Any]:
    from ..gmail.client import _get_composio_client

    client = _get_composio_client()
    try:
        accounts = client.connected_accounts.list(user_id=user_id)
        connected = any(
            "GOOGLECALENDAR" in str(getattr(a, "app_name", "") or "").upper()
            or "GOOGLE_CALENDAR" in str(getattr(a, "app_name", "") or "").upper()
            for a in (accounts or [])
        )
        if connected:
            _set_active_calendar_user_id(user_id)
        return {"ok": True, "connected": connected, "user_id": user_id if connected else None}
    except Exception as exc:
        logger.warning("calendar status check failed: %s", exc)
        return {"ok": False, "connected": False, "user_id": None}


def disconnect_account(user_id: str) -> Dict[str, Any]:
    _set_active_calendar_user_id(None)
    return {"ok": True}


__all__ = [
    "execute_calendar_tool",
    "get_active_calendar_user_id",
    "initiate_connect",
    "fetch_status",
    "disconnect_account",
]
