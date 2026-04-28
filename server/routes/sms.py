"""Twilio SMS webhook — receives inbound messages and responds asynchronously."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Form, Response

from ..logging_config import logger
from ..services.sms.handler import handle_incoming_sms

router = APIRouter(prefix="/sms", tags=["sms"])

_TWIML_EMPTY = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


@router.post("/incoming")
async def sms_incoming(
    From: Annotated[str, Form()] = "",
    Body: Annotated[str, Form()] = "",
) -> Response:
    """Receive inbound SMS from Twilio, fire processing task, return empty TwiML."""
    if not From or not Body.strip():
        return Response(content=_TWIML_EMPTY, media_type="application/xml")

    logger.info(f"Incoming SMS from {From}: {Body[:80]}")
    asyncio.create_task(handle_incoming_sms(from_number=From, body=Body))

    return Response(content=_TWIML_EMPTY, media_type="application/xml")
