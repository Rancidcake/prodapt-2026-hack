"""section_regenerate_v1 — edit-in-place with a teacher's free-text instruction."""

from .shared import wrap_reference_material

PROMPT_VERSION = "section_regenerate_v1"

SYSTEM = """\
You revise a single section of an existing artifact based on the teacher's free-text instruction. \
Return only the revised section — do not repeat or alter the neighboring sections given to you for \
context, and do not introduce contradictions with them.

Return only JSON matching the provided schema."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "revised_content": {"type": "string"},
        "is_grounded": {"type": "boolean"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["revised_content", "is_grounded", "citations"],
    "additionalProperties": False,
}


def build_user_content(
    *,
    existing_section_content: str,
    teacher_instruction: str,
    neighboring_sections: list[dict],
    chunks: list[dict],
) -> str:
    neighbors_block = "\n\n".join(f"[{n['title']}]\n{n['content']}" for n in neighboring_sections)
    return (
        f"Current section content:\n{existing_section_content}\n\n"
        f"Teacher's instruction: {teacher_instruction}\n\n"
        f"Neighboring sections (for context only — do not repeat these):\n{neighbors_block}\n\n"
        f"{wrap_reference_material(chunks)}"
    )
