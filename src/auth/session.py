from __future__ import annotations

import streamlit as st

_SESSION_KEY = "_auth_user"


def get_current_user() -> dict | None:
    return st.session_state.get(_SESSION_KEY)


def set_current_user(user: dict) -> None:
    st.session_state[_SESSION_KEY] = user


def clear_session() -> None:
    st.session_state.pop(_SESSION_KEY, None)
    st.session_state.pop("project_id", None)
    st.session_state.pop("summary", None)
    st.session_state.pop("outputs", None)


def require_login() -> dict:
    """Return current user dict; redirect to login page if not authenticated."""
    user = get_current_user()
    if not user:
        st.switch_page("pages/login.py")
        st.stop()
    return user


def require_admin() -> dict:
    """Return current user dict; error if not admin."""
    user = require_login()
    if user.get("role") != "admin":
        st.error("需要管理员权限")
        st.stop()
    return user
