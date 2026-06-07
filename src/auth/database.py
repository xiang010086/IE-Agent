from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
# IE_AGENT_DB overrides the SQLite location (used by tests for isolation, and
# by deployments that keep the DB outside the repo).
DB_PATH = Path(os.environ.get("IE_AGENT_DB") or (DATA_DIR / "ie_agent.db"))

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)

# Enable WAL mode for better concurrent read performance
@event.listens_for(engine, "connect")
def _set_wal(conn, _):
    conn.execute("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables and seed the default admin account."""
    from src.auth import models as _  # noqa: F401 — registers ORM classes
    Base.metadata.create_all(engine)
    _seed_admin()


def _seed_admin() -> None:
    from src.auth.models import User
    from src.auth.auth_service import hash_password

    with SessionLocal() as s:
        if s.query(User).count() == 0:
            s.add(
                User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    role="admin",
                    factory_name="总部",
                )
            )
            s.commit()
