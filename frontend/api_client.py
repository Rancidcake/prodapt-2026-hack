import os

import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

Auth = tuple[str, str]


def register(username: str, password: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": username, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def whoami(auth: Auth) -> dict:
    response = requests.get(f"{API_BASE_URL}/auth/me", auth=auth, timeout=30)
    response.raise_for_status()
    return response.json()


def list_providers() -> dict:
    response = requests.get(f"{API_BASE_URL}/providers", timeout=30)
    response.raise_for_status()
    return response.json()


def upload_document(auth: Auth, filename: str, file_bytes: bytes) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/documents",
        auth=auth,
        files={"file": (filename, file_bytes, "application/pdf")},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def list_documents(auth: Auth) -> list[dict]:
    response = requests.get(f"{API_BASE_URL}/documents", auth=auth, timeout=30)
    response.raise_for_status()
    return response.json()


def generate_lesson_plan(
    auth: Auth,
    teaching_context: dict,
    topic: str,
    duration_minutes: int,
    document_ids: list[int] | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/generate/lesson-plan",
        auth=auth,
        json={
            "teaching_context": teaching_context,
            "topic": topic,
            "duration_minutes": duration_minutes,
            "document_ids": document_ids or [],
            "provider": provider,
            "model": model,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def generate_quiz(
    auth: Auth,
    teaching_context: dict,
    objectives: list[dict],
    item_counts: dict,
    difficulty: str,
    document_ids: list[int] | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/generate/quiz",
        auth=auth,
        json={
            "teaching_context": teaching_context,
            "objectives": objectives,
            "item_counts": item_counts,
            "difficulty": difficulty,
            "document_ids": document_ids or [],
            "provider": provider,
            "model": model,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def generate_resources(
    auth: Auth,
    teaching_context: dict,
    topic: str,
    document_ids: list[int] | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/generate/resources",
        auth=auth,
        json={
            "teaching_context": teaching_context,
            "topic": topic,
            "document_ids": document_ids or [],
            "provider": provider,
            "model": model,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()
