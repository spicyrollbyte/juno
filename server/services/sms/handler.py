"""Handle an incoming Twilio SMS webhook."""

from __future__ import annotations

import asyncio

from ...agents.interaction_agent.runtime import InteractionAgentRuntime
from ...logging_config import logger
from ...services.user_context import set_current_user_id


async def handle_incoming_sms(from_number: str, body: str) -> None:
    """Process an inbound SMS as a Juno chat message for the given user."""
    token = set_current_user_id(from_number)
    try:
        logger.info(f"SMS from {from_number}: {body[:80]}")
        runtime = InteractionAgentRuntime()
        await runtime.execute(user_message=body.strip())
    except Exception as exc:
        logger.error(f"SMS handler failed for {from_number}: {exc}")
    finally:
        # Context is per-task; reset is informational only
        pass


__all__ = ["handle_incoming_sms"]
