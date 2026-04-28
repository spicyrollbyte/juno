"""Google Calendar OAuth routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import Settings, get_settings
from ..services.calendar.client import (
    disconnect_account,
    fetch_status,
    get_active_calendar_user_id,
    initiate_connect,
)

router = APIRouter(prefix="/calendar", tags=["calendar"])


class CalendarConnectPayload(BaseModel):
    user_id: str | None = None
    auth_config_id: str | None = None


class CalendarUserPayload(BaseModel):
    user_id: str


@router.post("/connect")
async def calendar_connect(
    payload: CalendarConnectPayload,
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    auth_config_id = payload.auth_config_id or settings.composio_gcal_auth_config_id or ""
    if not auth_config_id:
        return JSONResponse(
            {"ok": False, "error": "Missing auth_config_id. Set COMPOSIO_GCAL_AUTH_CONFIG_ID."},
            status_code=400,
        )
    import os
    user_id = payload.user_id or f"gcal-web-{os.getpid()}"
    try:
        return JSONResponse(initiate_connect(user_id, auth_config_id))
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@router.post("/status")
async def calendar_status(payload: CalendarUserPayload) -> JSONResponse:
    return JSONResponse(fetch_status(payload.user_id))


@router.post("/disconnect")
async def calendar_disconnect(payload: CalendarUserPayload) -> JSONResponse:
    return JSONResponse(disconnect_account(payload.user_id))
