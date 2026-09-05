"""Embeddings always go through Gemini, independent of LLM_PROVIDER.

Anthropic has no first-party embeddings API (they point you at Voyage AI as
a separate integration). Gemini's embedding endpoint is free-tier friendly
and this way embeddings don't need their own provider-abstraction layer —
see KT.md §10. Verified live: gemini-embedding-001 supports
`outputDimensionality` to request a smaller vector (768 here, well under
pgvector's 2000-dim index ceiling) instead of its default 3072.
"""

import os

import requests

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768
_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class EmbeddingError(RuntimeError):
    pass


def embed_text(text: str) -> list[float]:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EmbeddingError(
            "GEMINI_API_KEY is not set — embeddings always use Gemini regardless of LLM_PROVIDER."
        )

    try:
        response = requests.post(
            f"{_API_BASE}/{EMBEDDING_MODEL}:embedContent",
            headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
            json={
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": EMBEDDING_DIM,
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        raise EmbeddingError(f"Could not reach Gemini's embedding API: {exc}") from exc

    if response.status_code != 200:
        try:
            detail = response.json().get("error", {}).get("message")
        except ValueError:
            detail = response.text
        raise EmbeddingError(detail or f"HTTP {response.status_code}")

    return response.json()["embedding"]["values"]
