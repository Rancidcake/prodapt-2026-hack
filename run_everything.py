#!/usr/bin/env python3
"""One-click dev runner.

Loads .env, creates a shared virtualenv and installs backend + frontend
dependencies on first run, then starts the FastAPI backend and the
Streamlit frontend together. Ctrl+C stops both.

Usage: python run_everything.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = ROOT / ".venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
BACKEND_PORT = 8000
FRONTEND_PORT = 8501


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ensure_venv() -> None:
    if VENV_PY.exists():
        return
    print("Creating shared virtualenv at .venv ...")
    subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    print("Installing backend + frontend dependencies ...")
    subprocess.run(
        [
            str(VENV_PY), "-m", "pip", "install", "-q",
            "-r", str(BACKEND / "requirements.txt"),
            "-r", str(FRONTEND / "requirements.txt"),
        ],
        check=True,
    )


def wait_for_backend(timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    url = f"http://localhost:{BACKEND_PORT}/health"
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError("Backend did not become healthy in time — check its output above.")


def main() -> None:
    load_dotenv(ROOT / ".env")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set. Put it in .env at the repo root, then re-run.")
        sys.exit(1)

    ensure_venv()
    os.environ.setdefault("API_BASE_URL", f"http://localhost:{BACKEND_PORT}")

    procs: list[subprocess.Popen] = []
    try:
        backend_proc = subprocess.Popen(
            [str(VENV_PY), "-m", "uvicorn", "app.main:app", "--reload", "--port", str(BACKEND_PORT)],
            cwd=BACKEND,
            env=os.environ,
        )
        procs.append(backend_proc)

        print("Waiting for backend to come up ...")
        wait_for_backend()
        print(f"Backend ready:  http://localhost:{BACKEND_PORT}/docs")

        frontend_proc = subprocess.Popen(
            [str(VENV_PY), "-m", "streamlit", "run", "app.py", "--server.port", str(FRONTEND_PORT)],
            cwd=FRONTEND,
            env=os.environ,
        )
        procs.append(frontend_proc)

        print(f"Frontend ready: http://localhost:{FRONTEND_PORT}")
        print("Press Ctrl+C to stop both.\n")
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping ...")
    except Exception as exc:  # noqa: BLE001 — surface setup/runtime errors plainly
        print(f"Error: {exc}")
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
