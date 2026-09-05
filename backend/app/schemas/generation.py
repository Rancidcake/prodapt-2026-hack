from pydantic import BaseModel


class TeachingContext(BaseModel):
    grade: str
    subject: str
    board: str | None = None
    language: str | None = None


class Objective(BaseModel):
    id: str
    text: str


# --- Lesson plan ---


class LessonPlanRequest(BaseModel):
    teaching_context: TeachingContext
    topic: str
    duration_minutes: int = 40
    document_ids: list[int] = []
    provider: str | None = None
    model: str | None = None


class LessonPlanSection(BaseModel):
    title: str
    timing_minutes: int
    content: str
    checks_for_understanding: str
    objective_ids: list[str]
    is_grounded: bool
    citations: list[str]


class LessonPlanResponse(BaseModel):
    topic: str
    duration_minutes: int
    objectives: list[Objective]
    sections: list[LessonPlanSection]
    differentiation_notes: str


# --- Quiz ---


class QuizRequest(BaseModel):
    teaching_context: TeachingContext
    objectives: list[Objective]
    item_counts: dict[str, int] = {"mcq": 5}
    difficulty: str = "medium"
    document_ids: list[int] = []
    provider: str | None = None
    model: str | None = None


class QuizQuestion(BaseModel):
    type: str
    stem: str
    options: list[str] = []
    correct_answer: str
    objective_id: str
    difficulty: str
    is_grounded: bool
    citations: list[str]


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]
    uncovered_objective_ids: list[str]


# --- Learning resources (further-reading links) ---


class ResourcesRequest(BaseModel):
    teaching_context: TeachingContext
    topic: str
    document_ids: list[int] = []
    provider: str | None = None
    model: str | None = None


class Resource(BaseModel):
    title: str
    type: str
    url: str
    description: str
    confidence: str


class ResourcesResponse(BaseModel):
    topic: str
    resources: list[Resource]


# --- Explanation (concept simplification) ---


class ExplanationRequest(BaseModel):
    teaching_context: TeachingContext
    topic: str
    document_ids: list[int] = []
    extra_support: bool = False
    provider: str | None = None
    model: str | None = None


class ExplanationResponse(BaseModel):
    explanation: str
    analogies: list[str]
    common_misconceptions: list[str]
    is_grounded: bool
    citations: list[str]


# --- Classroom activities ---


class ActivityRequest(BaseModel):
    teaching_context: TeachingContext
    topic: str
    class_size: int = 30
    available_resources: list[str] = []
    provider: str | None = None
    model: str | None = None


class ActivityResponse(BaseModel):
    activity_type: str
    title: str
    materials: list[str]
    duration_minutes: int
    steps: list[str]
