"""Per-request user identity via asyncio ContextVar.

Set once at the entry point (HTTP request or SMS webhook); propagates
automatically into every create_task() spawned from that context.
"""

from __future__ import annotations

from contextvars import ContextVar, Token

_user_id: ContextVar[str] = ContextVar("user_id", default="default")


def get_current_user_id() -> str:
    return _user_id.get()


def set_current_user_id(user_id: str) -> Token:
    return _user_id.set(user_id)


def is_sms_user(user_id: str | None = None) -> bool:
    uid = user_id or get_current_user_id()
    return uid.startswith("+")


__all__ = ["get_current_user_id", "set_current_user_id", "is_sms_user"]
