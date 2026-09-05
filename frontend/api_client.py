import os

import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def generate_lesson_plan(teaching_context: dict, topic: str, duration_minutes: int) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/generate/lesson-plan",
        json={
            "teaching_context": teaching_context,
            "topic": topic,
            "duration_minutes": duration_minutes,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def generate_quiz(teaching_context: dict, objectives: list[dict], item_counts: dict, difficulty: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/generate/quiz",
        json={
            "teaching_context": teaching_context,
            "objectives": objectives,
            "item_counts": item_counts,
            "difficulty": difficulty,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()
