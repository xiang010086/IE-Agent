from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.auth.auth_service import login, register
from src.auth.database import init_db
from src.auth.session import get_current_user, set_current_user
from src.utils.icons import icon
from src.utils.theme import apply_auth_theme

st.set_page_config(page_title="工业IE智能体 — 登录", page_icon="🏭", layout="centered",
                   initial_sidebar_state="collapsed")

init_db()

# Already logged in → go back to main app
if get_current_user():
    st.switch_page("streamlit_project_app.py")
    st.stop()

apply_auth_theme()

st.markdown(
    '<div style="text-align:center;margin-bottom:1.5rem">'
    '<div style="display:inline-flex;align-items:center;justify-content:center;'
    'width:58px;height:58px;border-radius:15px;color:#fff;'
    'background:linear-gradient(135deg,#0f766e,#2dd4bf)">'
    f'{icon("factory", 30, 1.8)}</div>'
    '<div style="font-size:1.5rem;font-weight:600;color:#15212e;margin-top:0.55rem">工业IE智能体</div>'
    '<div style="color:#5b6b7c;font-size:13px;margin-top:0.2rem">'
    '工位视频 → MTM动作分析 → 精益改善</div></div>',
    unsafe_allow_html=True,
)

tab_login, tab_reg = st.tabs(["登录", "注册"])

# ── 登录 ──────────────────────────────────────────────────────────────────
with tab_login:
    with st.form("login_form"):
        username = st.text_input("用户名", placeholder="请输入用户名")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        submitted = st.form_submit_button(":material/login: 登录", use_container_width=True, type="primary")

    if submitted:
        if not username or not password:
            st.error("用户名和密码不能为空")
        else:
            user = login(username, password)
            if user:
                set_current_user(user)
                st.success(f"欢迎回来，{user['username']}！")
                st.switch_page("streamlit_project_app.py")
            else:
                st.error("用户名或密码错误，请重试")

    st.caption("默认管理员：admin / admin123")

# ── 注册 ──────────────────────────────────────────────────────────────────
with tab_reg:
    with st.form("reg_form"):
        new_username = st.text_input("用户名", placeholder="4-32个字符", key="reg_user")
        new_factory = st.text_input("工厂/部门", placeholder="例如：总装车间（可选）", key="reg_factory")
        new_email = st.text_input("邮箱", placeholder="可选", key="reg_email")
        new_pw = st.text_input("密码", type="password", placeholder="至少6位", key="reg_pw")
        new_pw2 = st.text_input("确认密码", type="password", key="reg_pw2")
        reg_submitted = st.form_submit_button(":material/person_add: 注册", use_container_width=True, type="primary")

    if reg_submitted:
        if not new_username or not new_pw:
            st.error("用户名和密码为必填项")
        elif len(new_username) < 2:
            st.error("用户名至少2个字符")
        elif len(new_pw) < 6:
            st.error("密码至少6位")
        elif new_pw != new_pw2:
            st.error("两次密码不一致")
        else:
            try:
                user = register(new_username, new_pw, factory_name=new_factory, email=new_email)
                set_current_user(user)
                st.success(f"注册成功，欢迎 {user['username']}！")
                st.switch_page("streamlit_project_app.py")
            except ValueError as e:
                st.error(str(e))
