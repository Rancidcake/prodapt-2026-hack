"""PDF text extraction — preserves page numbers, which citations depend on."""

import pymupdf as fitz


def parse_pdf(path: str) -> list[dict]:
    """Returns [{"text": ..., "page": 1-indexed page number}, ...] — one entry per non-empty page."""
    pages = []
    with fitz.open(path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if text:
                pages.append({"text": text, "page": page_number})
    return pages
