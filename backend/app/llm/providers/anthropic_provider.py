"""Anthropic backend for the LLM abstraction layer — selected via client.py."""

import json
import os
from typing import Any

import anthropic

from ..errors import (
    GenerationRefusedError,
    GenerationResult,
    GenerationTruncatedError,
    LLMProviderError,
    MissingCredentialsError,
)
from ..pii_guard import scrub_pii

MODEL_PRIMARY = os.environ.get("LLM_MODEL_PRIMARY", "claude-opus-4-8")

# Adaptive thinking and the `effort` param only exist on the 4.6+ tier — Haiku 4.5
# (and other older/cheaper models) reject both with a 400. Structured outputs
# (output_config.format) work on every current model, so that stays unconditional.
_ADAPTIVE_MODEL_PREFIXES = (
    "claude-opus-4-6",
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-sonnet-5",
    "claude-fable-5",
    "claude-mythos-5",
)


def _supports_adaptive_thinking(model: str) -> bool:
    return model.startswith(_ADAPTIVE_MODEL_PREFIXES)


_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def generate(
    *,
    system: str,
    user_content: str,
    output_schema: dict[str, Any],
    task_type: str,
    prompt_version: str,
    effort: str = "high",
    max_tokens: int = 8000,
    model: str | None = None,
) -> GenerationResult:
    resolved_model = model or MODEL_PRIMARY
    clean_content, pii_hits = scrub_pii(user_content)

    request: dict[str, Any] = {
        "model": resolved_model,
        "max_tokens": max_tokens,
        "output_config": {"format": {"type": "json_schema", "schema": output_schema}},
        "system": system,
        "messages": [{"role": "user", "content": clean_content}],
    }
    if _supports_adaptive_thinking(resolved_model):
        request["thinking"] = {"type": "adaptive"}
        request["output_config"]["effort"] = effort

    try:
        response = _client.messages.create(**request)
    except TypeError as exc:
        if "authentication method" in str(exc):
            raise MissingCredentialsError(
                "ANTHROPIC_API_KEY is not set. Export it, or run `ant auth login`, before calling the LLM."
            ) from exc
        raise
    except anthropic.APIStatusError as exc:
        detail = exc.body.get("error", {}).get("message") if isinstance(exc.body, dict) else None
        raise LLMProviderError(detail or str(exc)) from exc
    except anthropic.APIConnectionError as exc:
        raise LLMProviderError(f"Could not reach Anthropic's API: {exc}") from exc

    if response.stop_reason == "max_tokens":
        raise GenerationTruncatedError(task_type, prompt_version)
    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else None
        raise GenerationRefusedError(task_type, category)

    text = next(block.text for block in response.content if block.type == "text")

    return GenerationResult(
        output=json.loads(text),
        model=response.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        pii_detected=pii_hits,
    )
