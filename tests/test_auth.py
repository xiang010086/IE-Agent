"""Tests for the auth service layer (no Streamlit, no network).

Isolation: we point IE_AGENT_DB at a throwaway temp file BEFORE importing any
src.auth module, so database.py builds its engine against the temp DB and never
touches the real data/ie_agent.db.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# MUST be set before importing src.auth.* — the engine is built at import time.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["IE_AGENT_DB"] = _tmp.name

from src.auth.auth_service import (  # noqa: E402
    hash_password,
    list_all_users,
    login,
    log_analysis_done,
    log_analysis_start,
    register,
    register_project,
    verify_password,
)
from src.auth.database import init_db  # noqa: E402


def setup():
    init_db()


def test_hash_and_verify():
    h = hash_password("secret")
    assert h != "secret"
    assert verify_password("secret", h)
    assert not verify_password("wrong", h)
    print("hash/verify OK")


def test_register_and_login():
    setup()
    user = register("testuser", "pass123", factory_name="A厂")
    assert user["username"] == "testuser"
    assert user["role"] == "user"
    assert user["factory_name"] == "A厂"

    logged = login("testuser", "pass123")
    assert logged is not None
    assert logged["id"] == user["id"]

    assert login("testuser", "wrongpass") is None
    print("register/login OK")


def test_duplicate_username():
    setup()
    # testuser may already exist from the previous test in the same run
    if not login("dupuser", "pass123"):
        register("dupuser", "pass123")
    try:
        register("dupuser", "other")
        assert False, "should have raised"
    except ValueError as e:
        assert "已存在" in str(e)
    print("duplicate username OK")


def test_admin_seeded():
    setup()
    users = list_all_users()
    assert any(u["username"] == "admin" and u["role"] == "admin" for u in users)
    print("admin seed OK")


def test_project_registration():
    setup()
    p = register_project("proj_test_001", "测试项目", owner_id=None)
    assert p["fs_project_id"] == "proj_test_001"
    p2 = register_project("proj_test_001", "测试项目", owner_id=None)  # idempotent
    assert p2["id"] == p["id"]
    print("project registration OK")


def test_analysis_log():
    setup()
    register_project("proj_log_test", "日志项目", owner_id=None)
    log_id = log_analysis_start("proj_log_test", user_id=None)
    assert isinstance(log_id, int)
    log_analysis_done(log_id, {"lbr": 88.5, "station_count": 3})
    print("analysis log OK")


def main():
    test_hash_and_verify()
    test_register_and_login()
    test_duplicate_username()
    test_admin_seeded()
    test_project_registration()
    test_analysis_log()
    print("\nauth 测试全部通过")


if __name__ == "__main__":
    main()
