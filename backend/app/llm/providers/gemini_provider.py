"""Gemini backend for the LLM abstraction layer — selected via client.py.

Talks to the plain `generateContent` REST endpoint directly rather than
through an SDK, since that REST contract is the stable, long-documented
surface — verified live against the real API while building this (see the
request/response shapes referenced in the comments below).

Two things this backend does differently from the Anthropic one, both
confirmed by hitting the real endpoint:

1. Gemini's `responseSchema` rejects `additionalProperties` outright (400
   INVALID_ARGUMENT) — our prompt schemas set it everywhere for Anthropic's
   structured outputs, so it has to be stripped recursively before sending.
2. The non-"lite" flash models do hidden "thinking" by default and bill it
   as tokens even when the visible output is trivial (measured: 131 total
   tokens to say "Hello", 120 of them thinking). `thinkingConfig.thinkingBudget: 0`
   eliminates that. The "lite" models (e.g. `gemini-flash-lite-latest`)
   don't do hidden thinking at all and reject `thinkingConfig` outright
   (400 INVALID_ARGUMENT) — confirmed live — so it's only sent for models
   that aren't "lite".
"""

import json
import os
from typing import Any

import requests

from ..errors import (
    GenerationRefusedError,
    GenerationResult,
    GenerationTruncatedError,
    LLMProviderError,
    MissingCredentialsError,
)
from ..pii_guard import scrub_pii

MODEL_PRIMARY = os.environ.get("LLM_MODEL_PRIMARY", "gemini-flash-lite-latest")
_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

_TRUNCATED_REASONS = {"MAX_TOKENS"}
_REFUSED_REASONS = {"SAFETY", "RECITATION", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "OTHER"}


def _strip_unsupported_keys(schema: Any) -> Any:
    """Recursively drops JSON-Schema keys Gemini's responseSchema doesn't accept."""
    if isinstance(schema, dict):
        return {k: _strip_unsupported_keys(v) for k, v in schema.items() if k != "additionalProperties"}
    if isinstance(schema, list):
        return [_strip_unsupported_keys(item) for item in schema]
    return schema


def generate(
    *,
    system: str,
    user_content: str,
    output_schema: dict[str, Any],
    task_type: str,
    prompt_version: str,
    effort: str = "high",  # no Gemini equivalent — kept for interface parity with the Anthropic backend
    max_tokens: int = 8000,
) -> GenerationResult:
    clean_content, pii_hits = scrub_pii(user_content)

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise MissingCredentialsError("GEMINI_API_KEY is not set. Put it in .env before calling the LLM.")

    generation_config: dict[str, Any] = {
        "responseMimeType": "application/json",
        "responseSchema": _strip_unsupported_keys(output_schema),
        "maxOutputTokens": max_tokens,
    }
    if "lite" not in MODEL_PRIMARY:
        generation_config["thinkingConfig"] = {"thinkingBudget": 0}

    try:
        response = requests.post(
            f"{_API_BASE}/{MODEL_PRIMARY}:generateContent",
            headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
            json={
                "contents": [{"parts": [{"text": clean_content}]}],
                "systemInstruction": {"parts": [{"text": system}]},
                "generationConfig": generation_config,
            },
            timeout=120,
        )
    except requests.RequestException as exc:
        raise LLMProviderError(f"Could not reach Gemini's API: {exc}") from exc

    if response.status_code != 200:
        try:
            detail = response.json().get("error", {}).get("message")
        except ValueError:
            detail = response.text
        raise LLMProviderError(detail or f"HTTP {response.status_code}")

    body = response.json()
    candidate = body["candidates"][0]
    finish_reason = candidate.get("finishReason")

    if finish_reason in _TRUNCATED_REASONS:
        raise GenerationTruncatedError(task_type, prompt_version)
    if finish_reason in _REFUSED_REASONS:
        raise GenerationRefusedError(task_type, finish_reason)

    text = candidate["content"]["parts"][0]["text"]
    usage = body.get("usageMetadata", {})

    return GenerationResult(
        output=json.loads(text),
        model=body.get("modelVersion", MODEL_PRIMARY),
        input_tokens=usage.get("promptTokenCount", 0),
        output_tokens=usage.get("candidatesTokenCount", 0),
        pii_detected=pii_hits,
    )
