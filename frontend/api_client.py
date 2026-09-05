import os

import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def upload_document(filename: str, file_bytes: bytes) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/documents",
        files={"file": (filename, file_bytes, "application/pdf")},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def list_documents() -> list[dict]:
    response = requests.get(f"{API_BASE_URL}/documents", timeout=30)
    response.raise_for_status()
    return response.json()


def generate_lesson_plan(
    teaching_context: dict, topic: str, duration_minutes: int, document_ids: list[int] | None = None
) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/generate/lesson-plan",
        json={
            "teaching_context": teaching_context,
            "topic": topic,
            "duration_minutes": duration_minutes,
            "document_ids": document_ids or [],
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def generate_quiz(
    teaching_context: dict,
    objectives: list[dict],
    item_counts: dict,
    difficulty: str,
    document_ids: list[int] | None = None,
) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/generate/quiz",
        json={
            "teaching_context": teaching_context,
            "objectives": objectives,
            "item_counts": item_counts,
            "difficulty": difficulty,
            "document_ids": document_ids or [],
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()
