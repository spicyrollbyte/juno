"""Google Sheets tool schemas and actions for the execution agent."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from server.services.sheets import execute_sheets_tool, get_active_sheets_user_id

_NOT_CONNECTED = {"error": "Google Sheets not connected. Please connect it in settings first."}

_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "sheets_create_spreadsheet",
            "description": "Create a new Google Sheets spreadsheet. Returns the spreadsheet_id needed for all other sheet operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the new spreadsheet."},
                },
                "required": ["title"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_execute_sql",
            "description": (
                "Run SQL against a Google Sheet. Supports SELECT, INSERT, UPDATE, DELETE. "
                "Table name = sheet tab name in double quotes (e.g. \"Applications\"). "
                "Examples: SELECT * FROM \"Applications\"; "
                "INSERT INTO \"Applications\" (Company, Role, Status, Date) VALUES ('Acme', 'SWE', 'Applied', '2026-04-20'); "
                "UPDATE \"Applications\" SET Status='Interview' WHERE Company='Acme'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string", "description": "The spreadsheet ID from the URL or creation response."},
                    "sql": {"type": "string", "description": "SQL query to execute."},
                },
                "required": ["spreadsheet_id", "sql"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_batch_update",
            "description": "Write a 2D array of values to a sheet tab (overwrites from top-left). Use for setting headers or bulk-writing rows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string", "description": "Spreadsheet ID."},
                    "sheet_name": {"type": "string", "description": "Sheet tab name (e.g. 'Applications')."},
                    "values": {
                        "type": "array",
                        "items": {"type": "array", "items": {}},
                        "description": "2D array: first row is headers, subsequent rows are data.",
                    },
                },
                "required": ["spreadsheet_id", "sheet_name", "values"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_read",
            "description": "Read cell ranges from a spreadsheet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string", "description": "Spreadsheet ID."},
                    "ranges": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Cell ranges in A1 notation (e.g. ['Applications!A1:F50']).",
                    },
                },
                "required": ["spreadsheet_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_get_sheet_names",
            "description": "List all sheet tab names in a spreadsheet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string", "description": "Spreadsheet ID."},
                },
                "required": ["spreadsheet_id"],
                "additionalProperties": False,
            },
        },
    },
]


_SCHEMAS += [
    {
        "type": "function",
        "function": {
            "name": "sheets_save_id",
            "description": "Save a spreadsheet ID under a friendly name so it can be retrieved later (e.g. save 'Internships' sheet ID after creating it).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Friendly name (e.g. 'Internships')."},
                    "spreadsheet_id": {"type": "string", "description": "The Google Sheets spreadsheet ID."},
                },
                "required": ["name", "spreadsheet_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_get_saved_id",
            "description": "Retrieve a previously saved spreadsheet ID and its URL by friendly name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Friendly name (e.g. 'Internships')."},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    },
]


def get_schemas() -> List[Dict[str, Any]]:
    return _SCHEMAS


def _uid() -> Optional[str]:
    return get_active_sheets_user_id()


def sheets_create_spreadsheet(title: str) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    return execute_sheets_tool("GOOGLESHEETS_CREATE_GOOGLE_SHEET1", uid, arguments={"title": title})


def sheets_execute_sql(spreadsheet_id: str, sql: str) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    return execute_sheets_tool("GOOGLESHEETS_EXECUTE_SQL", uid, arguments={"spreadsheet_id": spreadsheet_id, "sql": sql})


def sheets_batch_update(
    spreadsheet_id: str,
    sheet_name: str,
    values: List[List[Any]],
) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    return execute_sheets_tool("GOOGLESHEETS_BATCH_UPDATE", uid, arguments={
        "spreadsheet_id": spreadsheet_id,
        "sheet_name": sheet_name,
        "values": values,
    })


def sheets_read(spreadsheet_id: str, ranges: Optional[List[str]] = None) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    args: Dict[str, Any] = {"spreadsheet_id": spreadsheet_id}
    if ranges:
        args["ranges"] = ranges
    return execute_sheets_tool("GOOGLESHEETS_BATCH_GET", uid, arguments=args)


def sheets_get_sheet_names(spreadsheet_id: str) -> Dict[str, Any]:
    uid = _uid()
    if not uid:
        return _NOT_CONNECTED
    return execute_sheets_tool("GOOGLESHEETS_GET_SHEET_NAMES", uid, arguments={"spreadsheet_id": spreadsheet_id})


def sheets_save_id(name: str, spreadsheet_id: str) -> Dict[str, Any]:
    """Persist a spreadsheet ID by name so Juno can link to it later."""
    from server.services.account_state import set_value
    set_value(f"sheet_id:{name.lower()}", spreadsheet_id)
    return {"ok": True, "name": name, "spreadsheet_id": spreadsheet_id}


def sheets_get_saved_id(name: str) -> Dict[str, Any]:
    """Retrieve a previously saved spreadsheet ID by name."""
    from server.services.account_state import get_value
    sheet_id = get_value(f"sheet_id:{name.lower()}")
    if sheet_id:
        return {"spreadsheet_id": sheet_id, "url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"}
    return {"error": f"No saved sheet found for '{name}'"}


def build_registry(agent_name: str) -> Dict[str, Callable[..., Any]]:  # noqa: ARG001
    return {
        "sheets_create_spreadsheet": sheets_create_spreadsheet,
        "sheets_execute_sql": sheets_execute_sql,
        "sheets_batch_update": sheets_batch_update,
        "sheets_read": sheets_read,
        "sheets_get_sheet_names": sheets_get_sheet_names,
        "sheets_save_id": sheets_save_id,
        "sheets_get_saved_id": sheets_get_saved_id,
    }


__all__ = ["get_schemas", "build_registry"]
