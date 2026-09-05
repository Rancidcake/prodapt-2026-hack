"""lesson_plan_v1 — Decision 1 (curriculum-agnostic), Decision 3 (grounding), Decision 5 (objectives)."""

from .shared import format_teaching_context, wrap_reference_material

PROMPT_VERSION = "lesson_plan_v1"

SYSTEM = """\
You are a curriculum-agnostic lesson planning assistant for teachers. You never assume a specific \
board, grade, or country — all of that comes from the Teaching Context given to you, which may \
describe any grade from primary school to university, any subject, any board or none.

Produce a structured lesson plan with explicit, gradeable learning objectives, timed sections, \
differentiation notes for mixed-ability classrooms, and checks for understanding embedded at natural \
breakpoints. Every section must list which objective IDs it addresses.

Return only JSON matching the provided schema."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "duration_minutes": {"type": "integer"},
        "objectives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "short stable slug, e.g. obj_1"},
                    "text": {"type": "string"},
                },
                "required": ["id", "text"],
                "additionalProperties": False,
            },
        },
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "timing_minutes": {"type": "integer"},
                    "content": {"type": "string"},
                    "checks_for_understanding": {"type": "string"},
                    "objective_ids": {"type": "array", "items": {"type": "string"}},
                    "is_grounded": {"type": "boolean"},
                    "citations": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title",
                    "timing_minutes",
                    "content",
                    "checks_for_understanding",
                    "objective_ids",
                    "is_grounded",
                    "citations",
                ],
                "additionalProperties": False,
            },
        },
        "differentiation_notes": {"type": "string"},
    },
    "required": ["topic", "duration_minutes", "objectives", "sections", "differentiation_notes"],
    "additionalProperties": False,
}


def build_user_content(*, teaching_context: dict, topic: str, duration_minutes: int, chunks: list[dict]) -> str:
    return (
        f"Teaching context:\n{format_teaching_context(teaching_context)}\n\n"
        f"Topic: {topic}\n"
        f"Available class time: {duration_minutes} minutes\n\n"
        f"{wrap_reference_material(chunks)}"
    )
