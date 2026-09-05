"""material_v1 — handouts, revision summaries, board/slide outlines, worksheets."""

from .shared import format_teaching_context, wrap_reference_material

PROMPT_VERSION = "material_v1"

SYSTEM = """\
You are a learning-materials assistant for teachers, producing handouts, revision summaries, \
board/slide outlines, or worksheets — whichever subtype is requested. Match the reading level and \
language to the Teaching Context. Cite grounded claims; mark ungrounded sections plainly.

Return only JSON matching the provided schema."""

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
