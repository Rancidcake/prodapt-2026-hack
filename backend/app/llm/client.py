"""The one abstraction layer every feature calls through — Decision 9.

Which provider actually runs the request is chosen here, by the
LLM_PROVIDER env var — prompts and the orchestrator never know or care.
Swapping providers means adding a providers/<name>.py backend and picking
it below; nothing else in the codebase changes.
"""

import os

from .errors import (  # noqa: F401 — re-exported for callers
    GenerationRefusedError,
    GenerationResult,
    GenerationTruncatedError,
    LLMProviderError,
    MissingCredentialsError,
)

_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()

if _PROVIDER == "gemini":
    from .providers.gemini_provider import generate  # noqa: F401
elif _PROVIDER == "anthropic":
    from .providers.anthropic_provider import generate  # noqa: F401
else:
    raise ValueError(f"Unknown LLM_PROVIDER: {_PROVIDER!r} (expected 'anthropic' or 'gemini')")
