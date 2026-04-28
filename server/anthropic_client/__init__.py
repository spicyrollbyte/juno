"""Provider-agnostic LLM client (OpenAI-compatible)."""

from .client import LLMError, request_chat_completion

# Alias for backward compat with any code that imported AnthropicError
AnthropicError = LLMError

__all__ = ["request_chat_completion", "LLMError", "AnthropicError"]
