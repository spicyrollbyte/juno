"""Persist connected account user IDs across server restarts."""

from __future__ import annotations

import json
import threading
from pathlib import Path

_LOCK = threading.Lock()
_STATE_FILE = Path(__file__).parent.parent / "data" / "connected_accounts.json"


def _load() -> dict:
    try:
        return json.loads(_STATE_FILE.read_text())
    except Exception:
        return {}


def _save(state: dict) -> None:
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps(state))
    except Exception:
        pass


def get_user_id(service: str) -> str | None:
    with _LOCK:
        return _load().get(service) or None


def set_user_id(service: str, user_id: str | None) -> None:
    with _LOCK:
        state = _load()
        if user_id:
            state[service] = user_id
        else:
            state.pop(service, None)
        _save(state)


def get_value(key: str) -> str | None:
    with _LOCK:
        return _load().get(key) or None


def set_value(key: str, value: str | None) -> None:
    with _LOCK:
        state = _load()
        if value:
            state[key] = value
        else:
            state.pop(key, None)
        _save(state)
