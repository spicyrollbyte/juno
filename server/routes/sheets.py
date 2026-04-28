"""Google Sheets OAuth routes."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import Settings, get_settings
from ..services.sheets.client import disconnect_account, fetch_status, initiate_connect

router = APIRouter(prefix="/sheets", tags=["sheets"])


class SheetsConnectPayload(BaseModel):
    user_id: str | None = None
    auth_config_id: str | None = None


class SheetsUserPayload(BaseModel):
    user_id: str


@router.post("/connect")
async def sheets_connect(
    payload: SheetsConnectPayload,
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    auth_config_id = payload.auth_config_id or settings.composio_sheets_auth_config_id or ""
    if not auth_config_id:
        return JSONResponse({"ok": False, "error": "Missing auth_config_id. Set COMPOSIO_SHEETS_AUTH_CONFIG_ID."}, status_code=400)
    user_id = payload.user_id or f"sheets-web-{os.getpid()}"
    try:
        return JSONResponse(initiate_connect(user_id, auth_config_id))
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@router.post("/status")
async def sheets_status(payload: SheetsUserPayload) -> JSONResponse:
    return JSONResponse(fetch_status(payload.user_id))


@router.post("/disconnect")
async def sheets_disconnect(payload: SheetsUserPayload) -> JSONResponse:
    return JSONResponse(disconnect_account(payload.user_id))
