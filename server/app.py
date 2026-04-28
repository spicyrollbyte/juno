from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .logging_config import configure_logging, logger
from .routes import api_router
from .services import get_important_email_watcher, get_trigger_scheduler


# Register global exception handlers for consistent error responses across the API
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.debug("validation error", extra={"errors": exc.errors(), "path": str(request.url)})
        return JSONResponse(
            {"ok": False, "error": "Invalid request", "detail": exc.errors()},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        logger.debug(
            "http error",
            extra={"detail": exc.detail, "status": exc.status_code, "path": str(request.url)},
        )
        detail = exc.detail
        if not isinstance(detail, str):
            detail = json.dumps(detail)
        return JSONResponse({"ok": False, "error": detail}, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error", extra={"path": str(request.url)})
        return JSONResponse(
            {"ok": False, "error": "Internal server error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


configure_logging()
_settings = get_settings()

app = FastAPI(
    title=_settings.app_name,
    version=_settings.app_version,
    docs_url=_settings.resolved_docs_url,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router)


@app.on_event("startup")
async def _start_trigger_scheduler() -> None:
    scheduler = get_trigger_scheduler()
    await scheduler.start()
    watcher = get_important_email_watcher()
    await watcher.start()
    _restore_connected_accounts()


def _restore_connected_accounts() -> None:
    """Auto-detect connected Composio accounts on startup so tools work without clicking Connect."""
    try:
        from .services.gmail.client import _get_composio_client, _set_active_gmail_user_id, get_active_gmail_user_id
        from .services.calendar.client import _set_active_calendar_user_id, get_active_calendar_user_id

        # Already set (e.g. from persisted state file)
        if get_active_gmail_user_id() and get_active_calendar_user_id():
            return

        client = _get_composio_client()
        user_id = "default"

        if not get_active_gmail_user_id():
            try:
                items = client.connected_accounts.list(user_ids=[user_id], toolkit_slugs=["GMAIL"], statuses=["ACTIVE"])
                data = getattr(items, "data", None) or (items if isinstance(items, list) else None)
                if data:
                    _set_active_gmail_user_id(user_id)
                    logger.info("Auto-restored Gmail connection for user: %s", user_id)
            except Exception as exc:
                logger.debug("Gmail auto-restore skipped: %s", exc)

        if not get_active_calendar_user_id():
            try:
                items = client.connected_accounts.list(user_ids=[user_id], toolkit_slugs=["GOOGLECALENDAR"], statuses=["ACTIVE"])
                data = getattr(items, "data", None) or (items if isinstance(items, list) else None)
                if data:
                    _set_active_calendar_user_id(user_id)
                    logger.info("Auto-restored Google Calendar connection for user: %s", user_id)
            except Exception as exc:
                logger.debug("Calendar auto-restore skipped: %s", exc)

        try:
            from .services.sheets.client import get_active_sheets_user_id, _set_active_sheets_user_id
            if not get_active_sheets_user_id():
                items = client.connected_accounts.list(user_ids=[user_id], toolkit_slugs=["GOOGLESHEETS"], statuses=["ACTIVE"])
                data = getattr(items, "data", None) or (items if isinstance(items, list) else None)
                if data:
                    _set_active_sheets_user_id(user_id)
                    logger.info("Auto-restored Google Sheets connection for user: %s", user_id)
        except Exception as exc:
            logger.debug("Sheets auto-restore skipped: %s", exc)
    except Exception as exc:
        logger.debug("Account auto-restore failed: %s", exc)


@app.on_event("shutdown")
# Gracefully shutdown background services when the app stops
async def _stop_trigger_scheduler() -> None:
    scheduler = get_trigger_scheduler()
    await scheduler.stop()
    watcher = get_important_email_watcher()
    await watcher.stop()


__all__ = ["app"]
