import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .db import get_session, init_db
from .llm.client import (
    GenerationRefusedError,
    GenerationTruncatedError,
    LLMProviderError,
    MissingCredentialsError,
)
from .llm.embeddings import EmbeddingError, embed_text
from .models.document import DocumentChunk, SourceDocument
from .schemas.document import DocumentResponse
from .schemas.generation import (
    LessonPlanRequest,
    LessonPlanResponse,
    QuizRequest,
    QuizResponse,
)
from .services.generation.orchestrator import generate
from .services.ingestion.chunker import chunk_pages
from .services.ingestion.parser import parse_pdf
from .services.retrieval.retriever import retrieve

app = FastAPI(title="MyLesson.ai")

# Streamlit runs on a different port in dev — allow it through.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# --- Documents (ingestion) ---


@app.post("/documents", response_model=DocumentResponse)
def upload_document(file: UploadFile, session: Session = Depends(get_session)) -> DocumentResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF upload is supported right now.")

    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(file.file.read())
        tmp.flush()
        pages = parse_pdf(tmp.name)

    if not pages:
        raise HTTPException(status_code=400, detail="No extractable text found — is this a scanned/image-only PDF?")

    chunks = chunk_pages(pages)

    document = SourceDocument(title=Path(file.filename).stem, filename=file.filename)
    session.add(document)
    session.flush()  # assigns document.id without committing yet

    try:
        for index, chunk in enumerate(chunks):
            embedding = embed_text(chunk["text"])
            session.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    page=chunk["page"],
                    text=chunk["text"],
                    embedding=embedding,
                )
            )
    except EmbeddingError as exc:
        session.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session.commit()

    return DocumentResponse(
        id=document.id,
        title=document.title,
        filename=document.filename,
        chunk_count=len(chunks),
    )


@app.get("/documents", response_model=list[DocumentResponse])
def list_documents(session: Session = Depends(get_session)) -> list[DocumentResponse]:
    stmt = (
        select(SourceDocument, func.count(DocumentChunk.id))
        .outerjoin(DocumentChunk, DocumentChunk.document_id == SourceDocument.id)
        .group_by(SourceDocument.id)
        .order_by(SourceDocument.created_at.desc())
    )
    rows = session.execute(stmt).all()
    return [
        DocumentResponse(id=doc.id, title=doc.title, filename=doc.filename, chunk_count=count)
        for doc, count in rows
    ]


# --- Generation ---


@app.post("/generate/lesson-plan", response_model=LessonPlanResponse)
def generate_lesson_plan(req: LessonPlanRequest, session: Session = Depends(get_session)) -> LessonPlanResponse:
    try:
        chunks = retrieve(session, query=req.topic, document_ids=req.document_ids)
        result = generate(
            "lesson_plan",
            teaching_context=req.teaching_context.model_dump(),
            topic=req.topic,
            duration_minutes=req.duration_minutes,
            chunks=chunks,
        )
    except EmbeddingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except MissingCredentialsError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (GenerationTruncatedError, GenerationRefusedError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return LessonPlanResponse(**result.output)


@app.post("/generate/quiz", response_model=QuizResponse)
def generate_quiz(req: QuizRequest, session: Session = Depends(get_session)) -> QuizResponse:
    try:
        query = "\n".join(o.text for o in req.objectives)
        chunks = retrieve(session, query=query, document_ids=req.document_ids)
        result = generate(
            "quiz",
            teaching_context=req.teaching_context.model_dump(),
            objectives=[o.model_dump() for o in req.objectives],
            item_counts=req.item_counts,
            difficulty=req.difficulty,
            chunks=chunks,
        )
    except EmbeddingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except MissingCredentialsError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (GenerationTruncatedError, GenerationRefusedError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return QuizResponse(**result.output)
