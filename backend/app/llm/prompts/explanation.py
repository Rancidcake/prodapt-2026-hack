"""explanation_v1 — concept simplification with analogies and misconceptions."""

from .shared import format_teaching_context, wrap_reference_material

PROMPT_VERSION = "explanation_v1"

SYSTEM = """\
You explain a single concept to a teacher who will relay it to students at a specific grade level. \
Include at least one concrete analogy appropriate to that level, and explicitly list the \
misconceptions students at that level commonly hold about the topic — don't just explain the \
correct version.

Return only JSON matching the provided schema."""

# "Extra support" mode — for students with learning difficulties (dyslexia, ADHD, intellectual
# disability), English-language learners, or anyone who needs a slower on-ramp. Grounded in real
# inclusive-teaching practice, not just "simpler words": chunked steps, concrete-before-abstract,
# no idioms/ambiguity, redundant phrasing of the core idea.
_EXTRA_SUPPORT_INSTRUCTIONS = """

The teacher has flagged this for students who need additional support (e.g. dyslexia, ADHD, an \
intellectual disability, or English-language learners). Adjust the explanation accordingly:
- Short sentences, everyday words. No idioms, sarcasm, or ambiguous phrasing.
- Break the idea into small, sequential steps rather than one dense paragraph.
- Lead with a concrete, familiar example before any abstract idea.
- Restate the core idea a second time, in different words, before moving on.
- Prefer short bullet points over long paragraphs in the explanation text itself."""

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


def build_user_content(
    *, teaching_context: dict, topic: str, chunks: list[dict], extra_support: bool = False
) -> str:
    support_block = _EXTRA_SUPPORT_INSTRUCTIONS if extra_support else ""
    return (
        f"Teaching context:\n{format_teaching_context(teaching_context)}\n\n"
        f"Concept to explain: {topic}"
        f"{support_block}\n\n"
        f"{wrap_reference_material(chunks)}"
    )
