"""explanation_v1 — concept simplification with analogies and misconceptions."""

from .shared import format_teaching_context, wrap_reference_material

PROMPT_VERSION = "explanation_v1"

SYSTEM = """\
You explain a single concept to a teacher who will relay it to students at a specific grade level. \
Include at least one concrete analogy appropriate to that level, and explicitly list the \
misconceptions students at that level commonly hold about the topic — don't just explain the \
correct version.

Return only JSON matching the provided schema."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "explanation": {"type": "string"},
        "analogies": {"type": "array", "items": {"type": "string"}},
        "common_misconceptions": {"type": "array", "items": {"type": "string"}},
        "is_grounded": {"type": "boolean"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["explanation", "analogies", "common_misconceptions", "is_grounded", "citations"],
    "additionalProperties": False,
}


def build_user_content(*, teaching_context: dict, topic: str, chunks: list[dict]) -> str:
    return (
        f"Teaching context:\n{format_teaching_context(teaching_context)}\n\n"
        f"Concept to explain: {topic}\n\n"
        f"{wrap_reference_material(chunks)}"
    )
