"""Interaction agent helpers for prompt construction."""

from html import escape
from pathlib import Path
from typing import Any, Dict, List

from ...services.execution import get_agent_roster

_prompt_path = Path(__file__).parent / "system_prompt.md"
SYSTEM_PROMPT = _prompt_path.read_text(encoding="utf-8").strip()

# Lines of transcript kept in the live (non-cached) block each turn.
# Everything before this is frozen and eligible for caching.
_LIVE_TRANSCRIPT_LINES = 6


# Load and return the pre-defined system prompt from markdown file
def build_system_prompt() -> str:
    """Return the static system prompt for the interaction agent."""
    return SYSTEM_PROMPT


# Build structured message with conversation history, active agents, and current turn.
# Splits history into a frozen (cacheable) block and a small live block so that
# the stable prefix is read from the Anthropic prompt cache on repeated calls.
def prepare_message_with_history(
    latest_text: str,
    transcript: str,
    message_type: str = "user",
) -> List[Dict[str, Any]]:
    """Compose a message that bundles history, roster, and the latest turn."""
    lines = [l for l in (transcript or "").splitlines() if l.strip()]

    # Split into frozen (cached) prefix and live (fresh) tail
    if len(lines) > _LIVE_TRANSCRIPT_LINES:
        frozen_lines = lines[:-_LIVE_TRANSCRIPT_LINES]
        live_lines = lines[-_LIVE_TRANSCRIPT_LINES:]
    else:
        frozen_lines = []
        live_lines = lines

    content_blocks: List[Dict[str, Any]] = []

    # Frozen block — stable history, marked for caching.
    # Anthropic caches this after it crosses the 1024-token minimum.
    if frozen_lines:
        frozen_text = "<context>\n" + "\n".join(frozen_lines) + "\n</context>"
        content_blocks.append({
            "type": "text",
            "text": frozen_text,
            "cache_control": {"type": "ephemeral"},
        })

    # Live block — recent history + active agents + current turn (billed fresh each call)
    live_history = "\n".join(live_lines) if live_lines else "None"
    live_sections = [
        f"<conversation_history>\n{live_history}\n</conversation_history>",
        f"<active_agents>\n{_render_active_agents()}\n</active_agents>",
        _render_current_turn(latest_text, message_type),
    ]
    content_blocks.append({"type": "text", "text": "\n\n".join(live_sections)})

    return [{"role": "user", "content": content_blocks}]


# Format currently active execution agents into XML tags for LLM awareness
def _render_active_agents() -> str:
    roster = get_agent_roster()
    roster.load()
    agents = roster.get_agents()

    if not agents:
        return "None"

    rendered: List[str] = []
    for agent_name in agents:
        name = escape(agent_name or "agent", quote=True)
        rendered.append(f'<agent name="{name}" />')

    return "\n".join(rendered)


# Wrap the current message in appropriate XML tags based on sender type
def _render_current_turn(latest_text: str, message_type: str) -> str:
    tag = "new_agent_message" if message_type == "agent" else "new_user_message"
    body = latest_text.strip()
    return f"<{tag}>\n{body}\n</{tag}>"
