from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import bcrypt

from src.auth.database import SessionLocal
from src.auth.models import AnalysisLog, Project, User


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login(username: str, password: str) -> Optional[dict]:
    """Return user dict on success, None on failure."""
    with SessionLocal() as s:
        user = s.query(User).filter_by(username=username, is_active=True).first()
        if user and verify_password(password, user.password_hash):
            return user.to_dict()
    return None


def register(username: str, password: str, factory_name: str = "", email: str = "") -> dict:
    """Create a new regular user. Raises ValueError on duplicate username."""
    with SessionLocal() as s:
        if s.query(User).filter_by(username=username).first():
            raise ValueError(f"用户名 '{username}' 已存在")
        user = User(
            username=username,
            email=email or None,
            password_hash=hash_password(password),
            role="user",
            factory_name=factory_name or None,
        )
        s.add(user)
        s.commit()
        s.refresh(user)
        return user.to_dict()


# ---------------------------------------------------------------------------
# User management (admin)
# ---------------------------------------------------------------------------

def list_all_users() -> list[dict]:
    with SessionLocal() as s:
        return [u.to_dict() for u in s.query(User).order_by(User.created_at.desc()).all()]


def set_user_active(user_id: int, active: bool) -> None:
    with SessionLocal() as s:
        user = s.get(User, user_id)
        if user:
            user.is_active = active
            s.commit()


def reset_password(user_id: int, new_password: str) -> None:
    with SessionLocal() as s:
        user = s.get(User, user_id)
        if user:
            user.password_hash = hash_password(new_password)
            s.commit()


# ---------------------------------------------------------------------------
# Project registration
# ---------------------------------------------------------------------------

def register_project(fs_project_id: str, name: str, owner_id: Optional[int]) -> dict:
    """Register a filesystem project in the DB (idempotent)."""
    with SessionLocal() as s:
        existing = s.query(Project).filter_by(fs_project_id=fs_project_id).first()
        if existing:
            return existing.to_dict()
        proj = Project(fs_project_id=fs_project_id, name=name, owner_id=owner_id)
        s.add(proj)
        s.commit()
        s.refresh(proj)
        return proj.to_dict()


def update_project_status(fs_project_id: str, status: str, station_count: int = 0) -> None:
    with SessionLocal() as s:
        proj = s.query(Project).filter_by(fs_project_id=fs_project_id).first()
        if proj:
            proj.status = status
            if station_count:
                proj.station_count = station_count
            s.commit()


def get_user_projects(user_id: int, is_admin: bool = False) -> list[dict]:
    """Return projects owned by user_id, or all projects if is_admin."""
    with SessionLocal() as s:
        q = s.query(Project).order_by(Project.created_at.desc())
        if not is_admin:
            q = q.filter_by(owner_id=user_id)
        return [p.to_dict() for p in q.all()]


def list_all_projects() -> list[dict]:
    with SessionLocal() as s:
        return [
            p.to_dict()
            for p in s.query(Project).order_by(Project.created_at.desc()).all()
        ]


# ---------------------------------------------------------------------------
# Analysis logging
# ---------------------------------------------------------------------------

def log_analysis_start(fs_project_id: str, user_id: Optional[int]) -> int:
    """Return log id."""
    with SessionLocal() as s:
        proj = s.query(Project).filter_by(fs_project_id=fs_project_id).first()
        log = AnalysisLog(
            project_id=proj.id if proj else None,
            user_id=user_id,
            status="running",
        )
        s.add(log)
        s.commit()
        return log.id


def log_analysis_done(log_id: int, result_summary: dict, status: str = "done") -> None:
    with SessionLocal() as s:
        log = s.get(AnalysisLog, log_id)
        if log:
            log.completed_at = datetime.utcnow()
            log.status = status
            log.result_summary = json.dumps(result_summary, ensure_ascii=False)
            s.commit()


def list_recent_logs(limit: int = 50) -> list[dict]:
    with SessionLocal() as s:
        logs = (
            s.query(AnalysisLog)
            .order_by(AnalysisLog.started_at.desc())
            .limit(limit)
            .all()
        )
        return [lg.to_dict() for lg in logs]
