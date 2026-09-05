"""Top-k similarity retrieval over document_chunks — cosine distance via pgvector's
`<=>` operator. Output shape matches what llm/prompts/shared.py's
wrap_reference_material() expects, so this plugs straight into the existing
generation call sites (KT.md §10).

`tenant_id` is enforced in the query itself, not just checked by the caller —
a document_id belonging to another tenant is silently excluded rather than
trusted, so a guessed or leaked ID can't be used to pull another teacher's
content through retrieval (README: "queries are tenant-scoped in the data
layer, not only in application code")."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...llm.embeddings import embed_text
from ...models.document import DocumentChunk, SourceDocument


def retrieve(session: Session, query: str, document_ids: list[int], tenant_id: int, top_k: int = 6) -> list[dict]:
    if not document_ids:
        return []

    query_embedding = embed_text(query)

    stmt = (
        select(DocumentChunk, SourceDocument.title)
        .join(SourceDocument, DocumentChunk.document_id == SourceDocument.id)
        .where(
            DocumentChunk.document_id.in_(document_ids),
            SourceDocument.tenant_id == tenant_id,
        )
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
