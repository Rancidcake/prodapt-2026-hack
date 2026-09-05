"""activity_v1 — classroom activities scaled to class size and available resources."""

from .shared import format_teaching_context

PROMPT_VERSION = "activity_v1"

SYSTEM = """\
You are a teaching assistant. Design exactly 3 classroom activities for the given topic, \
class size, time limit, and activity type.

Rules:
- individual: self-paced, no partner
- group: collaborative, specify group size
- mixed: 1-2 of each
- All steps must fit within the time limit
- No invented facts/stats/citations about the topic — keep content generic
- Output activities only: no preamble, no fences"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "activity_type": {"type": "string", "enum": ["group_work", "demonstration", "discussion"]},
        "title": {"type": "string"},
        "materials": {"type": "array", "items": {"type": "string"}},
        "duration_minutes": {"type": "integer"},
        "steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["activity_type", "title", "materials", "duration_minutes", "steps"],
    "additionalProperties": False,
}


def build_user_content(*, teaching_context: dict, topic: str, class_size: int, available_resources: list[str]) -> str:
    resources = ", ".join(available_resources) if available_resources else "none specified — assume a standard classroom only"
    return (
        f"Teaching context:\n{format_teaching_context(teaching_context)}\n\n"
        f"Topic: {topic}\n"
        f"Class size: {class_size}\n"
        f"Available resources: {resources}"
    )
