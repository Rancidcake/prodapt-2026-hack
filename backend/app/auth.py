"""Username/password auth via HTTP Basic, checked against the users table.

Each user is their own tenant (tenant_id == user.id) — the simplest
onboarding model that still gives real data isolation between teachers:
sign up and you automatically have your own private space, no separate org
step. Passwords are bcrypt-hashed, never stored or logged in plain text.

Not production-grade as-is: no rate limiting on login attempts, no password
reset flow, no MFA. Good enough for a hackathon demo where the goal is
"can't see another teacher's uploads or generations," not a hardened
identity system. See KT.md for what a real deployment would add.
"""

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_session
from .models.user import User

_security = HTTPBasic()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def get_current_user(
    credentials: HTTPBasicCredentials = Depends(_security),
    session: Session = Depends(get_session),
) -> User:
    user = session.execute(select(User).where(User.username == credentials.username)).scalar_one_or_none()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user
