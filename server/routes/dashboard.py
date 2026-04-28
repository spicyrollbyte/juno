"""Dashboard route — returns live data for the frontend panels."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from ..services import get_agent_roster, get_execution_agent_logs, get_trigger_service
from ..services.calendar.client import get_active_calendar_user_id
from ..services.gmail.client import get_active_gmail_user_id
from ..services.sheets.client import get_active_sheets_user_id

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class AgentSummary(BaseModel):
    name: str
    last_activity: str | None = None


class TriggerSummary(BaseModel):
    id: int
    agent_name: str
    payload: str
    next_trigger: str | None
    recurrence_rule: str | None
    status: str


class DashboardResponse(BaseModel):
    agents: List[AgentSummary]
    triggers: List[TriggerSummary]
    gmail_connected: bool
    gmail_user: str | None
    calendar_connected: bool
    sheets_connected: bool


@router.get("", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    """Return live state for all dashboard panels."""
    roster = get_agent_roster()
    roster.load()
    log_store = get_execution_agent_logs()

    agents: List[AgentSummary] = []
    for name in roster.get_agents():
        recent = log_store.load_recent(name, limit=1)
        last_ts = recent[-1][1] if recent else None
        agents.append(AgentSummary(name=name, last_activity=last_ts))

    trigger_svc = get_trigger_service()
    all_triggers = trigger_svc.list_all_triggers()
    triggers: List[TriggerSummary] = [
        TriggerSummary(
            id=t.id,
            agent_name=t.agent_name,
            payload=t.payload[:120],
            next_trigger=t.next_trigger,
            recurrence_rule=t.recurrence_rule,
            status=t.status,
        )
        for t in all_triggers
        if t.status == "active"
    ]

    gmail_user = get_active_gmail_user_id()
    calendar_user = get_active_calendar_user_id()
    sheets_user = get_active_sheets_user_id()
    return DashboardResponse(
        agents=agents,
        triggers=triggers,
        gmail_connected=gmail_user is not None,
        gmail_user=gmail_user,
        calendar_connected=calendar_user is not None,
        sheets_connected=sheets_user is not None,
    )
