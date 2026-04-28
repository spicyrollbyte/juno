"""Provider-agnostic LLM client.

Routes to the Anthropic SDK (with prompt caching) when the API key starts with
'sk-ant-' or LLM_BASE_URL contains 'anthropic.com'.  All other providers use
the OpenAI-compatible httpx path (Groq, OpenRouter, Together, etc.).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

import httpx

from ..logging_config import logger

_MAX_RETRIES = 4
_BASE_BACKOFF = 2.0


class LLMError(RuntimeError):
    """Raised on unrecoverable errors from the upstream LLM API."""


# ── Provider detection ────────────────────────────────────────────────────────

def _use_anthropic_sdk(api_key: Optional[str], base_url: str) -> bool:
    return bool(
        (api_key and api_key.startswith("sk-ant-"))
        or "anthropic.com" in base_url
    )


# ── Tool schema helpers ───────────────────────────────────────────────────────

def _to_anthropic_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """OpenAI tool schema → Anthropic tool schema."""
    converted = []
    for t in tools:
        fn = t.get("function", {})
        converted.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    # Cache the tool list so repeated calls don't re-tokenize it
    if converted:
        converted[-1]["cache_control"] = {"type": "ephemeral"}
    return converted


# ── Message format conversion ─────────────────────────────────────────────────

def _to_anthropic_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert OpenAI-format message list to Anthropic format.

    Consecutive tool results are merged into one user message (Anthropic
    requires this — multiple tool results must appear in a single turn).
    """
    result: List[Dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role")

        if role == "system":
            continue  # handled via the system= parameter

        if role == "tool":
            block = {
                "type": "tool_result",
                "tool_use_id": msg.get("tool_call_id", ""),
                "content": msg.get("content", ""),
            }
            # Append to the previous user message if it already holds tool_results
            if result and result[-1]["role"] == "user" and isinstance(result[-1]["content"], list):
                result[-1]["content"].append(block)
            else:
                result.append({"role": "user", "content": [block]})
            continue

        if role == "assistant":
            blocks: List[Dict[str, Any]] = []
            text = (msg.get("content") or "").strip()
            if text:
                blocks.append({"type": "text", "text": text})
            for tc in (msg.get("tool_calls") or []):
                fn = tc.get("function", {})
                raw_args = fn.get("arguments", {})
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except Exception:
                        raw_args = {}
                blocks.append({
                    "type": "tool_use",
                    "id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "input": raw_args,
                })
            result.append({"role": "assistant", "content": blocks or [{"type": "text", "text": ""}]})
            continue

        # user message — plain string content is fine
        result.append({"role": "user", "content": msg.get("content", "")})

    return result


def _from_anthropic_response(response: Any) -> Dict[str, Any]:
    """Convert Anthropic SDK response → OpenAI-compat response dict."""
    text_parts: List[str] = []
    tool_calls: List[Dict[str, Any]] = []

    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "tool_use":
            tool_calls.append({
                "id": block.id,
                "type": "function",
                "function": {
                    "name": block.name,
                    "arguments": json.dumps(block.input),
                },
            })

    message: Dict[str, Any] = {
        "role": "assistant",
        "content": "\n".join(text_parts) if text_parts else None,
    }
    if tool_calls:
        message["tool_calls"] = tool_calls

    usage = response.usage
    cache_read = getattr(usage, "cache_read_input_tokens", 0)
    cache_write = getattr(usage, "cache_creation_input_tokens", 0)
    logger.info(
        f"Anthropic usage — in: {usage.input_tokens} out: {usage.output_tokens} "
        f"cache_read: {cache_read} cache_write: {cache_write}"
    )

    return {"choices": [{"message": message}]}


# ── Anthropic SDK path ────────────────────────────────────────────────────────

async def _request_anthropic(
    model: str,
    messages: List[Dict[str, Any]],
    system: Optional[str],
    api_key: str,
    tools: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    import anthropic  # lazy import — only needed on this path

    client = anthropic.AsyncAnthropic(api_key=api_key)

    system_param: Any = []
    if system:
        # Mark the system prompt for caching — saves ~50% on repeated calls
        system_param = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]

    anthropic_messages = _to_anthropic_messages(messages)
    anthropic_tools = _to_anthropic_tools(tools) if tools else []

    kwargs: Dict[str, Any] = {
        "model": model,
        "max_tokens": 4096,
        "messages": anthropic_messages,
    }
    if system_param:
        kwargs["system"] = system_param
    if anthropic_tools:
        kwargs["tools"] = anthropic_tools

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await client.messages.create(**kwargs)
            return _from_anthropic_response(response)
        except anthropic.RateLimitError as exc:
            if attempt == _MAX_RETRIES:
                last_exc = exc
                break
            wait = _BASE_BACKOFF * (2 ** attempt)
            logger.warning(f"Anthropic rate limit — retrying in {wait:.1f}s (attempt {attempt + 1}/{_MAX_RETRIES})")
            await asyncio.sleep(wait)
        except anthropic.APIError as exc:
            raise LLMError(f"Anthropic API error: {exc}") from exc

    raise LLMError(f"Anthropic rate limited after {_MAX_RETRIES} retries") from last_exc


# ── OpenAI-compat path ────────────────────────────────────────────────────────

def _build_openai_payload(
    model: str,
    messages: List[Dict[str, Any]],
    system: Optional[str],
    tools: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    all_messages: List[Dict[str, Any]] = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)
    payload: Dict[str, Any] = {"model": model, "messages": all_messages, "stream": False}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    return payload


def _parse_retry_after(resp: httpx.Response) -> float:
    raw = resp.headers.get("retry-after") or resp.headers.get("x-ratelimit-reset-requests")
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return 0.0


async def _request_openai_compat(
    model: str,
    messages: List[Dict[str, Any]],
    system: Optional[str],
    api_key: Optional[str],
    tools: Optional[List[Dict[str, Any]]],
    base_url: str,
) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = _build_openai_payload(model, messages, system, tools)

    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=120.0) as client:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    if attempt == _MAX_RETRIES:
                        last_exc = exc
                        break
                    wait = _parse_retry_after(exc.response) or (_BASE_BACKOFF * (2 ** attempt))
                    logger.warning(f"Rate limited — retrying in {wait:.1f}s (attempt {attempt + 1}/{_MAX_RETRIES})")
                    await asyncio.sleep(wait)
                    continue
                try:
                    detail = exc.response.json().get("error") or exc.response.text
                except Exception:
                    detail = exc.response.text
                raise LLMError(f"LLM request failed ({exc.response.status_code}): {detail}") from exc
            except httpx.HTTPError as exc:
                raise LLMError(f"LLM request failed: {exc}") from exc

    if last_exc is not None:
        try:
            detail = last_exc.response.json().get("error") or last_exc.response.text  # type: ignore[union-attr]
        except Exception:
            detail = str(last_exc)
        raise LLMError(f"LLM rate limited after {_MAX_RETRIES} retries: {detail}") from last_exc
    raise LLMError("LLM request failed: unknown error")


# ── Public interface ──────────────────────────────────────────────────────────

async def request_chat_completion(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    system: Optional[str] = None,
    api_key: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    base_url: str = "https://api.groq.com/openai/v1",
    **_kwargs: Any,
) -> Dict[str, Any]:
    """Call the appropriate LLM backend and return an OpenAI-compat response dict."""
    logger.debug("Calling LLM", extra={"model": model, "tools": len(tools or [])})

    if _use_anthropic_sdk(api_key, base_url):
        return await _request_anthropic(model, messages, system, api_key or "", tools)
    return await _request_openai_compat(model, messages, system, api_key, tools, base_url)


__all__ = ["request_chat_completion", "LLMError"]
