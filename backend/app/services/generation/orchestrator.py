"""Decision 12 — one code path for every task type, dispatched by task_type."""

from ...llm import client
from ...llm.prompts import activity, explanation, lesson_plan, material, quiz, resources, section_regenerate

_REGISTRY = {
    "lesson_plan": lesson_plan,
    "quiz": quiz,
    "material": material,
    "explanation": explanation,
    "activity": activity,
    "resources": resources,
    "section_regenerate": section_regenerate,
}


def generate(
    task_type: str, *, provider: str | None = None, model: str | None = None, **kwargs
) -> client.GenerationResult:
    module = _REGISTRY[task_type]
    user_content = module.build_user_content(**kwargs)
    return client.generate(
        system=module.SYSTEM,
        user_content=user_content,
        output_schema=module.OUTPUT_SCHEMA,
        task_type=task_type,
        prompt_version=module.PROMPT_VERSION,
        provider=provider,
        model=model,
    )
