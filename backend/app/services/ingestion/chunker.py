"""Fixed-size chunking with overlap. Deliberately simple — semantic/recursive
chunking isn't worth the complexity for a hackathon-scale corpus (KT.md §10)."""

CHUNK_SIZE_CHARS = 2000
CHUNK_OVERLAP_CHARS = 200


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Returns [{"text": ..., "page": ...}, ...] — chunks never cross a page boundary,
    so every chunk keeps a single, accurate page number for citations."""
    chunks = []
    for page in pages:
        text = page["text"]
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE_CHARS
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page": page["page"]})
            if end >= len(text):
                break
            start = end - CHUNK_OVERLAP_CHARS
    return chunks
