from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .llm.client import (
    GenerationRefusedError,
    GenerationTruncatedError,
    LLMProviderError,
    MissingCredentialsError,
)
from .schemas.generation import (
    LessonPlanRequest,
    LessonPlanResponse,
    QuizRequest,
    QuizResponse,
)
from .services.generation.orchestrator import generate

app = FastAPI(title="MyLesson.ai")

# Streamlit runs on a different port in dev — allow it through.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate/lesson-plan", response_model=LessonPlanResponse)
def generate_lesson_plan(req: LessonPlanRequest) -> LessonPlanResponse:
    try:
        result = generate(
            "lesson_plan",
            teaching_context=req.teaching_context.model_dump(),
            topic=req.topic,
            duration_minutes=req.duration_minutes,
            chunks=[],
        )
    except MissingCredentialsError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (GenerationTruncatedError, GenerationRefusedError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return LessonPlanResponse(**result.output)


@app.post("/generate/quiz", response_model=QuizResponse)
def generate_quiz(req: QuizRequest) -> QuizResponse:
    try:
        result = generate(
            "quiz",
            teaching_context=req.teaching_context.model_dump(),
            objectives=[o.model_dump() for o in req.objectives],
            item_counts=req.item_counts,
            difficulty=req.difficulty,
            chunks=[],
        )
    except MissingCredentialsError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (GenerationTruncatedError, GenerationRefusedError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return QuizResponse(**result.output)
