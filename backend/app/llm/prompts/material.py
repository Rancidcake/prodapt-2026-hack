"""material_v1 — handouts, revision summaries, board/slide outlines, worksheets."""

from .shared import format_teaching_context, wrap_reference_material

PROMPT_VERSION = "material_v1"

SYSTEM = """\
You are a classroom-material assistant for educators (school teachers, college faculty, tutors). \
Produce ready-to-use Markdown for the requested subtype — handout, revision summary, or worksheet. \
Match language and complexity to the audience level given.

Rules:
- Do not fabricate statistics, dates, or specific real-world facts you are unsure of; use general, \
safe examples instead.
- Follow the subtype structure provided exactly — do not add, remove, or reorder sections.
- Use # / ## headings, bullet points, bold key terms.
- Output only the document content: no preamble, no meta-commentary, no code fences."""

SUBTYPE_INSTRUCTIONS = {
    "handout": "Definition → plain explanation → one real-world example → '## Key Takeaway' (1-2 lines).",
    "revision_summary": "4-6 bullets, exam-relevant facts only. No paragraphs, no examples.",
    "worksheet": "5 audience-appropriate questions with blank lines for answers, then '## Answer Key' listing correct answers.",
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "subtype": {"type": "string", "enum": ["handout", "summary", "slide_outline", "worksheet"]},
        "title": {"type": "string"},
        "blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "content": {"type": "string"},
                    "is_grounded": {"type": "boolean"},
                    "citations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["heading", "content", "is_grounded", "citations"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["subtype", "title", "blocks"],
    "additionalProperties": False,
}


def build_user_content(*, teaching_context: dict, subtype: str, topic: str, chunks: list[dict]) -> str:
    return (
        f"Teaching context:\n{format_teaching_context(teaching_context)}\n\n"
        f"Material type: {subtype}\n"
        f"Topic: {topic}\n\n"
        f"{wrap_reference_material(chunks)}"
    )
