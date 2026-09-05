"""lesson_plan_v1 — Decision 1 (curriculum-agnostic), Decision 3 (grounding), Decision 5 (objectives)."""

from .shared import format_teaching_context, wrap_reference_material

PROMPT_VERSION = "lesson_plan_v1"

SYSTEM = """\
You are a curriculum-agnostic lesson planning assistant. All grade/board/country context comes \
solely from the Teaching Context provided — never assume a national curriculum or standard unless \
Teaching Context names one. Calibrate vocabulary, depth, and abstraction to the stated level only.

Objectives: one per distinct skill/concept; each must open with a measurable Bloom's verb (explain, \
compare, construct, calculate, critically evaluate, synthesize, etc.) matched to cognitive demand for \
the level — never "understand" or "learn about".

Sections: use as many as the lesson needs (a lecture may need one long section; a young-learner class \
may need five short ones); timing_minutes must sum exactly to the given class time — verify before \
returning. Each section's content covers both instructor actions and learner actions, not a topic \
label. checks_for_understanding must be verifiable within the section itself (quick question, \
show-of-hands, one-line response) — never a quiz or homework. Every objective_id must appear in at \
least one section; every section must list which objective_ids it addresses.

Grounding: set is_grounded true and list citations only when content draws specific facts from the \
given reference chunks; otherwise false and []. Never cite an unused chunk or mark ungrounded content \
as grounded.

prerequisite_knowledge: list explicitly anything the topic assumes that isn't safely typical for the \
stated level; else [].

differentiation_notes: one concrete, specific adjustment each for struggling and advanced learners — \
never generic ("provide support as needed").

standard_tag: null unless Teaching Context explicitly provides one — never invent.

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
