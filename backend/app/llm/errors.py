"""Provider-agnostic exceptions and result type.

Every provider backend under providers/ raises these, never its own SDK's
exception types — callers (client.py, the orchestrator, the API layer) never
need to know or care which provider is actually running the request.
"""

from typing import Any

from pydantic import BaseModel


class GenerationTruncatedError(RuntimeError):
    def __init__(self, task_type: str, prompt_version: str):
        super().__init__(f"{task_type} ({prompt_version}) hit the output token limit before completing")


class GenerationRefusedError(RuntimeError):
    def __init__(self, task_type: str, reason: str | None):
        super().__init__(f"{task_type} was blocked by safety filters (reason={reason})")


class MissingCredentialsError(RuntimeError):
    """Raised with a provider-specific message telling the user which env var to set."""


class LLMProviderError(RuntimeError):
    """The provider's API rejected the request or couldn't be reached — billing, quota, outages."""


class GenerationResult(BaseModel):
    output: dict[str, Any]
    model: str
    input_tokens: int
    output_tokens: int
    pii_detected: list[str]
