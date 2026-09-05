"""Database session + table setup.

No Alembic yet — for a hackathon-scale schema, `Base.metadata.create_all()`
on startup is enough. Add Alembic when the schema needs to evolve without
dropping data (see KT.md §9).
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://localhost/mylesson")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from . import models  # noqa: F401 — import registers models on Base.metadata

    Base.metadata.create_all(bind=engine)
