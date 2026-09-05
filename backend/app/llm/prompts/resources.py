"""resources_v1 — curated further-reading links for a topic.

No provider here does live web search in this call — structured JSON output
mode is a single-shot generation, not a search tool. That means a naive
"give me links" prompt produces plausible-looking but frequently fake URLs.
Handled the same way the rest of the app treats uncertain output (the
grounded/ungrounded pattern): the model only claims a real URL for
well-known canonical sources, and every resource carries a `confidence`
flag so low-confidence ones are visibly marked rather than presented as
trustworthy."""

from .shared import format_teaching_context, wrap_reference_material

PROMPT_VERSION = "resources_v1"

SYSTEM = """\
You curate a short list of further-reading resources for a teacher on a given topic. You do not \
have live web access — you cannot verify that any URL currently resolves. Because of that:

- Only set `confidence` to "high" and set `url` to a real address when the resource is a \
well-known, stable, canonical source you are confident actually exists (e.g. the Wikipedia article \
for the topic, a well-known Khan Academy or NCERT page, a standard textbook chapter). Do not guess \
or construct a URL that merely looks plausible.
- For anything else — a book title, a general recommendation, a type of resource worth searching \
for — set `confidence` to "low", set `url` to an empty string, and phrase `title`/`description` as \
something a teacher could search for directly.

Prefer a mix of resource types (article, video, textbook, interactive, reference) over an unbroken \
list of Wikipedia links. Return only JSON matching the provided schema."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "resources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "type": {"type": "string", "enum": ["article", "video", "textbook", "interactive", "reference"]},
                    "url": {"type": "string", "description": "empty string if confidence is low"},
                    "description": {"type": "string"},
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "low"],
                        "description": "high = confident this exact URL is real; low = search suggestion only",
                    },
                },
                "required": ["title", "type", "url", "description", "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["topic", "resources"],
    "additionalProperties": False,
}


def build_user_content(*, teaching_context: dict, topic: str, chunks: list[dict]) -> str:
    return (
        f"Teaching context:\n{format_teaching_context(teaching_context)}\n\n"
        f"Topic: {topic}\n\n"
        f"{wrap_reference_material(chunks)}"
    )
