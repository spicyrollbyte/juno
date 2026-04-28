from __future__ import annotations

from fastapi import APIRouter

from .calendar import router as calendar_router
from .chat import router as chat_router
from .dashboard import router as dashboard_router
from .gmail import router as gmail_router
from .meta import router as meta_router
from .sheets import router as sheets_router
from .sms import router as sms_router
from .syllabus import router as syllabus_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(meta_router)
api_router.include_router(chat_router)
api_router.include_router(gmail_router)
api_router.include_router(calendar_router)
api_router.include_router(sheets_router)
api_router.include_router(dashboard_router)
api_router.include_router(sms_router)
api_router.include_router(syllabus_router)

__all__ = ["api_router"]
