"""quiz_v1 — the objective_id tagging is Decision 5's central modelling choice made real."""

from .shared import format_teaching_context, wrap_reference_material

PROMPT_VERSION = "quiz_v1"

SYSTEM = """\
You are a quiz-generation assistant for teachers. Every question you write must be tagged with the \
learning objective it tests, using the objective IDs given to you — never invent new objective IDs, \
and never leave a question untagged. This tagging is what lets the product report which objectives \
are and are not covered by the assessment, so it is the single most important constraint here.

If an objective in the input list has no question mapped to it, list its ID in \
`uncovered_objective_ids` rather than forcing a weak question onto it.

Return only JSON matching the provided schema."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["mcq", "short", "long", "numerical"]},
                    "stem": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "correct_answer": {"type": "string"},
                    "objective_id": {"type": "string"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    "is_grounded": {"type": "boolean"},
                    "citations": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "type",
                    "stem",
                    "options",
                    "correct_answer",
                    "objective_id",
                    "difficulty",
                    "is_grounded",
                    "citations",
                ],
                "additionalProperties": False,
            },
        },
        "uncovered_objective_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["questions", "uncovered_objective_ids"],
    "additionalProperties": False,
}


def build_user_content(
    *,
    teaching_context: dict,
    objectives: list[dict],
    item_counts: dict[str, int],
    difficulty: str,
    chunks: list[dict],
) -> str:
    objectives_block = "\n".join(f"- {o['id']}: {o['text']}" for o in objectives)
    counts_block = "\n".join(f"- {qtype}: {count}" for qtype, count in item_counts.items())
    return (
        f"Teaching context:\n{format_teaching_context(teaching_context)}\n\n"
        f"Learning objectives to assess (use these exact IDs):\n{objectives_block}\n\n"
        f"Item counts by type:\n{counts_block}\n"
        f"Target difficulty: {difficulty}\n\n"
        f"{wrap_reference_material(chunks)}"
    )
