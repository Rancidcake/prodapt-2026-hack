"""Top-k similarity retrieval over document_chunks — cosine distance via pgvector's
`<=>` operator. Output shape matches what llm/prompts/shared.py's
wrap_reference_material() expects, so this plugs straight into the existing
generation call sites (KT.md §10)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...llm.embeddings import embed_text
from ...models.document import DocumentChunk, SourceDocument


def retrieve(session: Session, query: str, document_ids: list[int], top_k: int = 6) -> list[dict]:
    if not document_ids:
        return []

    query_embedding = embed_text(query)

    stmt = (
        select(DocumentChunk, SourceDocument.title)
        .join(SourceDocument, DocumentChunk.document_id == SourceDocument.id)
        .where(DocumentChunk.document_id.in_(document_ids))
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    rows = session.execute(stmt).all()

    return [
        {
            "chunk_id": str(chunk.id),
            "document_title": title,
            "page": chunk.page,
            "text": chunk.text,
        }
        for chunk, title in rows
    ]
