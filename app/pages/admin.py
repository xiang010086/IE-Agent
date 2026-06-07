from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.auth.auth_service import (
    list_all_projects,
    list_all_users,
    list_recent_logs,
    reset_password,
    set_user_active,
)
from src.auth.database import init_db
from src.auth.session import clear_session, require_admin
from src.utils.icons import icon
from src.utils.theme import apply_app_theme, avatar_initial

st.set_page_config(page_title="IE智能体 — 管理控制台", page_icon="🏭", layout="wide",
                   initial_sidebar_state="expanded")

init_db()
user = require_admin()
apply_app_theme()

# ── Sidebar: brand · nav · user card ───────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div class="sb-brand"><span class="logo">{icon("factory", 24)}</span>'
        '<span class="name">工业IE智能体</span></div>'
        '<div class="sb-tag">管理控制台</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button(":material/arrow_back: 返回主界面", use_container_width=True):
        st.switch_page("streamlit_project_app.py")

    with st.container():
        st.markdown(
            '<div class="sb-user">'
            f'<div class="sb-avatar">{avatar_initial(user["username"])}</div>'
            f'<div class="who"><div class="u">{user["username"]}</div>'
            f'<div class="f">{user.get("factory_name") or "管理员"}</div></div></div>',
            unsafe_allow_html=True,
        )
        if st.button(":material/logout: 退出登录", use_container_width=True):
            clear_session()
            st.switch_page("pages/login.py")

st.markdown(
    f'<div class="step-head"><span class="step-ic">{icon("settings", 22)}</span>'
    '<span class="step-title" style="font-size:1.4rem">管理控制台</span></div>',
    unsafe_allow_html=True,
)
st.divider()

tab_users, tab_projects, tab_logs = st.tabs(["用户管理", "全局项目", "分析历史"])

# ── 用户管理 ─────────────────────────────────────────────────────────────
with tab_users:
    users = list_all_users()
    st.caption(f"共 {len(users)} 个用户")

    for u in users:
        is_self = u["id"] == user["id"]
        cols = st.columns([2, 1.5, 2, 1, 1, 1.5])
        role_tag = " · admin" if u["role"] == "admin" else ""
        cols[0].write(f"**{u['username']}**{role_tag}")
        cols[1].write(u.get("factory_name") or "—")
        cols[2].write(u.get("created_at", "")[:10] if u.get("created_at") else "—")
        cols[3].write("活跃" if u["is_active"] else "停用")

        if not is_self:
            label = "停用" if u["is_active"] else "激活"
            if cols[4].button(label, key=f"toggle_{u['id']}"):
                set_user_active(u["id"], not u["is_active"])
                st.rerun()
        else:
            cols[4].write("（自己）")

        with cols[5].popover("重置密码"):
            new_pw = st.text_input("新密码（≥6位）", type="password", key=f"newpw_{u['id']}")
            if st.button("确认重置", key=f"resetpw_{u['id']}"):
                if len(new_pw) >= 6:
                    reset_password(u["id"], new_pw)
                    st.success("已重置")
                else:
                    st.error("密码至少6位")

    st.divider()
    with st.expander("新建用户"):
        from src.auth.auth_service import register as reg_fn
        with st.form("admin_new_user"):
            nu = st.text_input("用户名")
            nf = st.text_input("工厂/部门")
            np = st.text_input("密码", type="password")
            nr = st.selectbox("角色", ["user", "admin"])
            if st.form_submit_button("创建"):
                try:
                    created = reg_fn(nu, np, factory_name=nf)
                    if nr == "admin":
                        from src.auth.database import SessionLocal
                        from src.auth.models import User as UModel
                        with SessionLocal() as sess:
                            uu = sess.get(UModel, created["id"])
                            if uu:
                                uu.role = "admin"
                                sess.commit()
                    st.success(f"用户 {nu} 已创建")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

# ── 全局项目 ─────────────────────────────────────────────────────────────
with tab_projects:
    projects = list_all_projects()
    factories = sorted({p.get("owner_username") or "未知" for p in projects})
    sel_factory = st.selectbox("按所有者筛选", ["全部"] + factories)
    if sel_factory != "全部":
        projects = [p for p in projects if (p.get("owner_username") or "未知") == sel_factory]

    st.caption(f"共 {len(projects)} 个项目")
    for p in projects:
        cols = st.columns([3, 1.5, 1.5, 1, 1])
        cols[0].write(f"**{p['name']}**  `{p['fs_project_id']}`")
        cols[1].write(p.get("owner_username") or "未知")
        cols[2].write((p.get("created_at") or "")[:10])
        cols[3].write(p.get("status", "—"))
        cols[4].write(f"{p.get('station_count', 0)} 工位")

# ── 分析历史 ─────────────────────────────────────────────────────────────
with tab_logs:
    logs = list_recent_logs(50)
    st.caption(f"最近 {len(logs)} 条记录")
    for lg in logs:
        duration = ""
        if lg.get("started_at") and lg.get("completed_at"):
            from datetime import datetime
            try:
                s = datetime.fromisoformat(lg["started_at"])
                e = datetime.fromisoformat(lg["completed_at"])
                secs = int((e - s).total_seconds())
                duration = f"({secs}s)"
            except Exception:
                pass

        summary_str = ""
        if lg.get("result_summary"):
            try:
                sm = json.loads(lg["result_summary"])
                lbr = sm.get("line_metrics", {}).get("lbr")
                if lbr is not None:
                    summary_str = f"LBR {lbr}%"
            except Exception:
                pass

        cols = st.columns([2, 2, 2, 1, 1.5])
        cols[0].write(lg.get("project_name") or "—")
        cols[1].write(lg.get("username") or "—")
        cols[2].write((lg.get("started_at") or "")[:16])
        cols[3].write(lg["status"])
        cols[4].write(f"{duration} {summary_str}")
