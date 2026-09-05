"""The one abstraction layer every feature calls through — Decision 9.

Provider selection is a **per-call** choice, not a fixed import-time one —
`LLM_PROVIDER` in `.env` is only the default. Prompts and the orchestrator
never import a provider directly; the caller (an API endpoint, ultimately
the teacher via the UI) can override provider and model on every request.

To add a third provider: create `providers/<name>.py` exposing a
`generate(*, system, user_content, output_schema, task_type, prompt_version,
effort, max_tokens, model) -> GenerationResult`, raising only the exception
types from `errors.py`, then add one entry to `_PROVIDERS` below.
"""

import os
from typing import Any

from .errors import (  # noqa: F401 — re-exported for callers
    GenerationRefusedError,
    GenerationResult,
    GenerationTruncatedError,
    LLMProviderError,
    MissingCredentialsError,
)
from .providers import anthropic_provider, gemini_provider

_PROVIDERS = {
    "anthropic": anthropic_provider,
    "gemini": gemini_provider,
}

DEFAULT_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()

# Shown in the frontend's provider/model pickers — not exhaustive, just the
# combinations verified to work together (see KT.md §4 for the per-model gotchas).
AVAILABLE_MODELS = {
    "anthropic": ["claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"],
    "gemini": ["gemini-flash-lite-latest", "gemini-flash-latest"],
}


def generate(
    *,
    system: str,
    user_content: str,
    output_schema: dict[str, Any],
    task_type: str,
    prompt_version: str,
    effort: str = "high",
    max_tokens: int = 8000,
    provider: str | None = None,
    model: str | None = None,
) -> GenerationResult:
    provider_name = (provider or DEFAULT_PROVIDER).lower()
    if provider_name not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name!r} (expected one of {list(_PROVIDERS)})")

    return _PROVIDERS[provider_name].generate(
        system=system,
        user_content=user_content,
        output_schema=output_schema,
        task_type=task_type,
        prompt_version=prompt_version,
        effort=effort,
        max_tokens=max_tokens,
        model=model,
    )
