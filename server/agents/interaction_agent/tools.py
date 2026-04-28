"""Tool definitions for interaction agent."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Optional

from ...logging_config import logger
from ...services.conversation import get_conversation_log
from ...services.execution import get_agent_roster, get_execution_agent_logs
from ..execution_agent.batch_manager import ExecutionBatchManager


@dataclass
class ToolResult:
    """Standardized payload returned by interaction-agent tools."""

    success: bool
    payload: Any = None
    user_message: Optional[str] = None
    recorded_reply: bool = False

# Tool schemas for Anthropic
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "send_message_to_agent",
            "description": "Deliver instructions to a specific execution agent. Creates a new agent if the name doesn't exist in the roster, or reuses an existing one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Human-readable agent name describing its purpose (e.g., 'Vercel Job Offer', 'Email to Sharanjeet'). This name will be used to identify and potentially reuse the agent."
                    },
                    "instructions": {"type": "string", "description": "Instructions for the agent to execute."},
                },
                "required": ["agent_name", "instructions"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message_to_user",
            "description": "Deliver a natural-language response directly to the user. Use this for updates, confirmations, or any assistant response the user should see immediately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Plain-text message that will be shown to the user and recorded in the conversation log.",
                    },
                },
                "required": ["message"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_save_link",
            "description": "Save a Google Sheets spreadsheet ID under a friendly name. Use when the user pastes a Sheets URL or after creating a new sheet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Friendly name (e.g. 'Internships')."},
                    "spreadsheet_id": {"type": "string", "description": "The spreadsheet ID from the URL."},
                },
                "required": ["name", "spreadsheet_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_get_link",
            "description": "Return the Google Sheets URL for a named spreadsheet (e.g. 'Internships'). Use when the user asks to see or open a sheet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Friendly name of the sheet (e.g. 'Internships')."},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_clear_all",
            "description": "Permanently delete ALL events from the user's Google Calendar. Use only when the user explicitly asks to wipe or clear their entire calendar and has confirmed it's irreversible.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_draft",
            "description": "Record an email draft so the user can review the exact text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email for the draft.",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject for the draft.",
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content (plain text).",
                    },
                },
                "required": ["to", "subject", "body"],
                "additionalProperties": False,
            },
        },
    },
]

_batch_managers: dict[str, ExecutionBatchManager] = {}


def _get_batch_manager() -> ExecutionBatchManager:
    from ...services.user_context import get_current_user_id
    uid = get_current_user_id()
    if uid not in _batch_managers:
        _batch_managers[uid] = ExecutionBatchManager(user_id=uid)
    return _batch_managers[uid]


# Create or reuse execution agent and dispatch instructions asynchronously
def send_message_to_agent(agent_name: str, instructions: str) -> ToolResult:
    """Send instructions to an execution agent."""
    roster = get_agent_roster()
    roster.load()
    existing_agents = set(roster.get_agents())
    is_new = agent_name not in existing_agents

    if is_new:
        roster.add_agent(agent_name)

    get_execution_agent_logs().record_request(agent_name, instructions)

    action = "Created" if is_new else "Reused"
    logger.info(f"{action} agent: {agent_name}")

    batch_manager = _get_batch_manager()

    async def _execute_async() -> None:
        try:
            result = await batch_manager.execute_agent(agent_name, instructions)
            status = "SUCCESS" if result.success else "FAILED"
            logger.info(f"Agent '{agent_name}' completed: {status}")
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Agent '{agent_name}' failed: {str(exc)}")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.error("No running event loop available for async execution")
        return ToolResult(success=False, payload={"error": "No event loop available"})

    loop.create_task(_execute_async())

    return ToolResult(
        success=True,
        payload={
            "status": "submitted",
            "agent_name": agent_name,
            "new_agent_created": is_new,
        },
    )


# Send immediate message to user and record in conversation history
def send_message_to_user(message: str) -> ToolResult:
    """Record a user-visible reply in the conversation log and push via SMS if needed."""
    from ...services.user_context import get_current_user_id, is_sms_user

    log = get_conversation_log()
    log.record_reply(message)

    uid = get_current_user_id()
    if is_sms_user(uid):
        try:
            from ...services.sms.client import send_sms_sync
            send_sms_sync(to=uid, body=message)
        except Exception as exc:
            logger.warning(f"SMS send failed for {uid}: {exc}")

    return ToolResult(
        success=True,
        payload={"status": "delivered"},
        user_message=message,
        recorded_reply=True,
    )


# Format and record email draft for user review
def send_draft(
    to: str,
    subject: str,
    body: str,
) -> ToolResult:
    """Record a draft update in the conversation log for the interaction agent."""
    log = get_conversation_log()

    message = f"To: {to}\nSubject: {subject}\n\n{body}"

    log.record_reply(message)
    logger.info(f"Draft recorded for: {to}")

    return ToolResult(
        success=True,
        payload={
            "status": "draft_recorded",
            "to": to,
            "subject": subject,
        },
        recorded_reply=True,
    )


def sheets_save_link(name: str, spreadsheet_id: str) -> ToolResult:
    """Persist a spreadsheet ID under a friendly name."""
    from server.services.account_state import set_value
    set_value(f"sheet_id:{name.lower()}", spreadsheet_id)
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    return send_message_to_user(f"Saved. Here's your {name} sheet: {url}")


def sheets_get_link(name: str) -> ToolResult:
    """Return the Google Sheets URL for a saved spreadsheet."""
    from server.services.account_state import get_value
    sheet_id = get_value(f"sheet_id:{name.lower()}")
    if sheet_id:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        return send_message_to_user(f"Here's your {name} sheet: {url}")
    return ToolResult(success=False, payload={"error": f"No saved sheet for '{name}'"})


def calendar_clear_all() -> ToolResult:
    """Delete every event on the user's primary Google Calendar."""
    from ..execution_agent.tools.calendar import calendar_clear_all as _clear
    result = _clear()
    deleted = result.get("deleted", 0)
    errors = result.get("errors", 0)
    msg = f"Cleared {deleted} calendar event{'s' if deleted != 1 else ''}."
    if errors:
        msg += f" ({errors} failed to delete.)"
    return send_message_to_user(msg)


# Record silent wait state to avoid duplicate responses
def wait(reason: str) -> ToolResult:
    """Wait silently and add a wait log entry that is not visible to the user."""
    log = get_conversation_log()
    
    # Record a dedicated wait entry so the UI knows to ignore it
    log.record_wait(reason)
    

    return ToolResult(
        success=True,
        payload={
            "status": "waiting",
            "reason": reason,
        },
        recorded_reply=True,
    )


# Return predefined tool schemas for LLM function calling
def get_tool_schemas():
    """Return OpenAI-compatible tool schemas."""
    return TOOL_SCHEMAS


# Route tool calls to appropriate handlers with argument validation and error handling
def handle_tool_call(name: str, arguments: Any) -> ToolResult:
    """Handle tool calls from interaction agent."""
    try:
        if isinstance(arguments, str):
            args = json.loads(arguments) if arguments.strip() else {}
        elif isinstance(arguments, dict):
            args = arguments
        else:
            return ToolResult(success=False, payload={"error": "Invalid arguments format"})

        if name == "send_message_to_agent":
            return send_message_to_agent(**args)
        if name == "send_message_to_user":
            return send_message_to_user(**args)
        if name == "send_draft":
            return send_draft(**args)
        if name == "wait":
            return wait(**args)
        if name == "calendar_clear_all":
            return calendar_clear_all()
        if name == "sheets_get_link":
            return sheets_get_link(**args)
        if name == "sheets_save_link":
            return sheets_save_link(**args)

        logger.warning("unexpected tool", extra={"tool": name})
        return ToolResult(success=False, payload={"error": f"Unknown tool: {name}"})
    except json.JSONDecodeError:
        return ToolResult(success=False, payload={"error": "Invalid JSON"})
    except TypeError as exc:
        return ToolResult(success=False, payload={"error": f"Missing required arguments: {exc}"})
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("tool call failed", extra={"tool": name, "error": str(exc)})
        return ToolResult(success=False, payload={"error": "Failed to execute"})
