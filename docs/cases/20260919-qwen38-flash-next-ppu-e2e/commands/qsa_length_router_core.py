"""Pure, fail-closed routing rules for the fw-015 QSA length router."""

from __future__ import annotations

from typing import Any


BOUND_TOKENS = 8448 * 4


def build_tokenize_payload(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Build the authoritative vLLM /tokenize request or fail closed."""

    if path.endswith("/chat/completions"):
        if not isinstance(payload.get("messages"), list):
            return None
        allowed = (
            "model",
            "messages",
            "add_generation_prompt",
            "continue_final_message",
            "add_special_tokens",
            "chat_template",
            "chat_template_kwargs",
            "media_io_kwargs",
            "mm_processor_kwargs",
            "tools",
        )
        result = {key: payload[key] for key in allowed if key in payload}
        # Qwen3.8-Flash-Next is language-only. Any multimodal content is routed
        # unbounded instead of trying to prove a token limit in the proxy.
        for message in payload["messages"]:
            if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                return None
        return result

    if path.endswith("/completions"):
        if not isinstance(payload.get("prompt"), str):
            return None
        allowed = ("model", "prompt", "add_special_tokens")
        return {key: payload[key] for key in allowed if key in payload}

    return None


def bounded_is_safe(
    payload: dict[str, Any], prompt_count: int, bound_tokens: int = BOUND_TOKENS
) -> tuple[bool, str]:
    """Return bounded admission only with a complete integer upper-bound proof."""

    max_tokens = payload.get("max_tokens")
    if isinstance(max_tokens, bool) or not isinstance(max_tokens, int):
        return False, "missing_or_non_integer_max_tokens"
    if max_tokens < 0 or isinstance(prompt_count, bool) or not isinstance(prompt_count, int):
        return False, "invalid_token_count"
    if prompt_count < 0:
        return False, "invalid_token_count"
    total = prompt_count + max_tokens
    if total > bound_tokens:
        return False, f"total_tokens_{total}_exceeds_{bound_tokens}"
    return True, f"total_tokens_{total}_within_{bound_tokens}"
