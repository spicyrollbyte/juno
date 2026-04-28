"""Google Calendar tool schemas and actions for the execution agent."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from server.services.calendar import execute_calendar_tool, get_active_calendar_user_id

_NOT_CONNECTED = {"error": "Google Calendar not connected. Please connect it in settings first."}

_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "calendar_clear_all",
            "description": "Delete ALL events from the user's Google Calendar. Use when the user wants to wipe their entire calendar. This is irreversible — only call it when explicitly instructed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "Calendar ID, defaults to 'primary'."},
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_create_event",
            "description": "Create a new Google Calendar event. Returns the created event including its id — save the id if you may need to delete or update it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title."},
                    "start_datetime": {"type": "string", "description": "Start time ISO 8601 (e.g. 2026-04-21T13:00:00). Do NOT include timezone offset — pass timezone separately."},
                    "end_datetime": {"type": "string", "description": "End time ISO 8601. If omitted, uses event_duration_hour/minutes."},
                    "timezone": {"type": "string", "description": "IANA timezone (e.g. America/New_York). Auto-injected from user settings if omitted."},
                    "description": {"type": "string", "description": "Event description (optional)."},
                    "location": {"type": "string", "description": "Event location (optional)."},
                    "event_duration_hour": {"type": "integer", "description": "Duration hours (used if end_datetime not provided)."},
                    "event_duration_minutes": {"type": "integer", "description": "Duration minutes 0-59 (used if end_datetime not provided)."},
                    "recurrence": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "RRULE strings for recurring events.",
                    },
                    "calendar_id": {"type": "string", "description": "Calendar ID, defaults to 'primary'."},
                    "color_id": {
                        "type": "string",
                        "description": (
                            "Google Calendar color ID (1-11). Use consistently by event type: "
                            "9=Blueberry (study sessions), 11=Tomato (exams/deadlines), "
                            "7=Peacock (work/meetings), 2=Sage (personal/health), "
                            "5=Banana (social), 6=Tangerine (reminders/tasks). "
                            "Omit to use the calendar default."
                        ),
                    },
                },
                "required": ["summary", "start_datetime"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_delete_event",
            "description": "Delete a Google Calendar event by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "Event ID to delete (from creation response or find/list)."},
                    "calendar_id": {"type": "string", "description": "Calendar ID, defaults to 'primary'."},
                },
                "required": ["event_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_list_events",
            "description": "List Google Calendar events in a time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "Calendar ID, use 'primary'."},
                    "time_min": {"type": "string", "description": "Start of range, RFC3339 (e.g. 2026-04-21T00:00:00Z)."},
                    "time_max": {"type": "string", "description": "End of range, RFC3339."},
                    "query": {"type": "string", "description": "Optional text search within events."},
                    "max_results": {"type": "integer", "description": "Max events to return (default 10)."},
                },
                "required": ["calendar_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_find_event",
            "description": "Search Google Calendar events by keyword or time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text to search for in event titles/descriptions."},
                    "time_min": {"type": "string", "description": "Search from this datetime (optional)."},
                    "time_max": {"type": "string", "description": "Search until this datetime (optional)."},
                    "max_results": {"type": "integer", "description": "Max events to return."},
                },
                "additionalProperties": False,
            },
        },
    },
]


def get_schemas() -> List[Dict[str, Any]]:
    return _SCHEMAS


def _uid() -> Optional[str]:
    return get_active_calendar_user_id()


def calendar_clear_all(calendar_id: Optional[str] = None) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    cal_id = calendar_id or "primary"
    from datetime import datetime, timezone
    # List all events across a wide window
    now = datetime.now(timezone.utc)
    time_min = "2000-01-01T00:00:00Z"
    time_max = "2100-01-01T00:00:00Z"
    deleted = 0
    errors = 0
    page_token = None
    while True:
        args: Dict[str, Any] = {
            "calendarId": cal_id,
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 100,
        }
        if page_token:
            args["pageToken"] = page_token
        result = execute_calendar_tool("GOOGLECALENDAR_EVENTS_LIST", uid, arguments=args)
        items = result.get("items") or result.get("data", {}).get("items") or []
        if not items:
            break
        for event in items:
            event_id = event.get("id") or event.get("event_id")
            if not event_id:
                continue
            try:
                execute_calendar_tool("GOOGLECALENDAR_DELETE_EVENT", uid, arguments={
                    "event_id": event_id,
                    "calendar_id": cal_id,
                })
                deleted += 1
            except Exception:
                errors += 1
        page_token = result.get("nextPageToken") or result.get("data", {}).get("nextPageToken")
        if not page_token or len(items) < 100:
            break
    return {"ok": True, "deleted": deleted, "errors": errors}


def _user_timezone() -> str:
    try:
        from server.services.timezone_store import get_timezone_store
        return get_timezone_store().get_timezone(default="UTC")
    except Exception:
        return "UTC"


def calendar_create_event(
    summary: str,
    start_datetime: str,
    end_datetime: Optional[str] = None,
    timezone: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    event_duration_hour: Optional[int] = None,
    event_duration_minutes: Optional[int] = None,
    recurrence: Optional[List[str]] = None,
    calendar_id: Optional[str] = None,
    color_id: Optional[str] = None,
) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    tz = timezone or _user_timezone()
    args: Dict[str, Any] = {
        "summary": summary,
        "start_datetime": start_datetime,
        "calendar_id": calendar_id or "primary",
        "timezone": tz,
    }
    if end_datetime:
        args["end_datetime"] = end_datetime
    if description:
        args["description"] = description
    if location:
        args["location"] = location
    if event_duration_hour is not None:
        args["event_duration_hour"] = event_duration_hour
    if event_duration_minutes is not None:
        args["event_duration_minutes"] = event_duration_minutes
    if recurrence:
        args["recurrence"] = recurrence
    if color_id is not None:
        args["colorId"] = str(color_id)
    return execute_calendar_tool("GOOGLECALENDAR_CREATE_EVENT", uid, arguments=args)


def calendar_delete_event(
    event_id: str,
    calendar_id: Optional[str] = None,
) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    return execute_calendar_tool("GOOGLECALENDAR_DELETE_EVENT", uid, arguments={
        "event_id": event_id,
        "calendar_id": calendar_id or "primary",
    })


def calendar_list_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    query: Optional[str] = None,
    max_results: Optional[int] = None,
) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    args: Dict[str, Any] = {"calendarId": calendar_id}
    if time_min:
        args["timeMin"] = time_min
    if time_max:
        args["timeMax"] = time_max
    if query:
        args["q"] = query
    if max_results:
        args["maxResults"] = max_results
    args["singleEvents"] = True
    args["orderBy"] = "startTime"
    return execute_calendar_tool("GOOGLECALENDAR_EVENTS_LIST", uid, arguments=args)


def calendar_find_event(
    query: Optional[str] = None,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: Optional[int] = None,
) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    args: Dict[str, Any] = {}
    if query:
        args["query"] = query
    if time_min:
        args["timeMin"] = time_min
    if time_max:
        args["timeMax"] = time_max
    if max_results:
        args["max_results"] = max_results
    return execute_calendar_tool("GOOGLECALENDAR_FIND_EVENT", uid, arguments=args)


def build_registry(agent_name: str) -> Dict[str, Callable[..., Any]]:  # noqa: ARG001
    return {
        "calendar_clear_all": calendar_clear_all,
        "calendar_create_event": calendar_create_event,
        "calendar_delete_event": calendar_delete_event,
        "calendar_list_events": calendar_list_events,
        "calendar_find_event": calendar_find_event,
    }


__all__ = ["get_schemas", "build_registry"]
