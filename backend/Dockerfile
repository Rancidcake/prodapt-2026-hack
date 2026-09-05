# MyLesson.ai — backend + frontend runtime image.
#
# Built with context = repo root (see docker-compose.yml) so this single
# image can serve both the FastAPI backend and the Streamlit frontend —
# docker-compose overrides CMD per service rather than building twice.
# Additive infrastructure only; does not modify any application code.
#
# `--app-dir backend` (not WORKDIR backend/) keeps the on-disk layout
# identical to local dev (backend/app/main.py, frontend/app.py as
# siblings) without changing how either app resolves its own imports.

FROM python:3.11-slim

WORKDIR /app

# postgresql-client gives `pg_isready`/`psql` for connection debugging from
# inside the container — not required by the app itself.
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first so this layer is cached across code-only changes.
COPY backend/requirements.txt ./backend/requirements.txt
COPY frontend/requirements.txt ./frontend/requirements.txt
RUN pip install --no-cache-dir \
    -r backend/requirements.txt \
    -r frontend/requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

EXPOSE 8000
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

# Default: FastAPI backend. docker-compose overrides this for the frontend
# service (`streamlit run frontend/app.py ...`).
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
