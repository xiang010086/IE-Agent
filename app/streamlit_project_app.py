from __future__ import annotations

import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.auth import (
    clear_session,
    get_current_user,
    get_user_projects,
    init_db,
    log_analysis_done,
    log_analysis_start,
    register_project,
    require_login,
    update_project_status,
)
from src.core.concurrent_analyzer import ConcurrentAnalyzer
from src.core.project_manager import ProjectManager
from src.core.validation import AccuracyValidator, ValidationThresholds
from src.report.line_report_generator import LineReportGenerator
from src.utils.icons import icon
from src.utils.theme import apply_app_theme, avatar_initial, step_header
from src.utils.ui_helpers import build_timeline_html, mode_badge, term_help, timeline_legend_html

st.set_page_config(page_title="工业IE智能体", page_icon="🏭", layout="wide",
                   initial_sidebar_state="expanded")

# ── DB init + auth guard ────────────────────────────────────────────────────
init_db()
user = require_login()

manager = ProjectManager(ROOT / "data" / "projects")
analyzer = ConcurrentAnalyzer(manager)
reporter = LineReportGenerator(manager)
validator = AccuracyValidator(manager)


def _lang() -> str:
    return st.session_state.get("lang", "zh")


def t(zh: str, en: str) -> str:
    return zh if _lang() == "zh" else en


def ensure_project(user_id: int) -> str:
    """Return current project id, auto-creating and registering to DB."""
    pid = st.session_state.get("project_id")
    if not pid:
        config = manager.create_project(t("快速分析", "Quick analysis"), "")
        pid = config["project"]["id"]
        st.session_state["project_id"] = pid
        register_project(pid, config["project"]["name"], owner_id=user_id)
    return pid


# ── Theme + language sync (must run before any t() call) ───────────────────
apply_app_theme()

if "lang_radio" not in st.session_state:
    st.session_state["lang_radio"] = "中文"
st.session_state["lang"] = "zh" if st.session_state["lang_radio"] == "中文" else "en"

is_admin = user.get("role") == "admin"

# ── Sidebar: brand · controls · (spacer) · user card ───────────────────────
with st.sidebar:
    st.markdown(
        f'<div class="sb-brand"><span class="logo">{icon("factory", 24)}</span>'
        f'<span class="name">{t("工业IE智能体", "Industrial IE Agent")}</span></div>'
        f'<div class="sb-tag">{t("工位视频 → MTM动作分析 → 精益改善", "Video → MTM analysis → lean improvement")}</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown(
        f'<div class="sb-section">{icon("languages", 13)}{t("语言", "Language")}</div>',
        unsafe_allow_html=True,
    )
    st.radio(
        "lang", ["中文", "English"], horizontal=True,
        label_visibility="collapsed", key="lang_radio",
    )

    show_adv = st.toggle(t("高级设置", "Advanced settings"),
                         value=st.session_state.get("show_adv", False))
    st.session_state["show_adv"] = show_adv

    # ── My projects: header + "＋" create, then click a name to switch ─────
    _hcols = st.columns([3, 1], vertical_alignment="center")
    _hcols[0].markdown(
        f'<div class="sb-section">{icon("folder", 13)}{t("我的项目", "My Projects")}</div>',
        unsafe_allow_html=True,
    )
    with _hcols[1].popover(":material/add:", use_container_width=True,
                           help=t("新建项目", "New project")):
        st.markdown(f"**{t('新建项目', 'New project')}**")
        _new_name = st.text_input(
            t("项目名称", "Project name"),
            key="_new_proj_name",
            placeholder=t("如：A线总装工位", "e.g. Line-A assembly"),
        )
        if st.button(t("创建", "Create"), key="_new_proj_create",
                     type="primary", use_container_width=True):
            _nm = (_new_name or "").strip() or t("未命名项目", "Untitled project")
            _cfg = manager.create_project(_nm, "")
            _new_pid = _cfg["project"]["id"]
            register_project(_new_pid, _nm, owner_id=user["id"])
            st.session_state["project_id"] = _new_pid
            for _k in ("summary", "outputs", "_uploaded_sig"):
                st.session_state.pop(_k, None)
            st.rerun()

    _sb_projects = get_user_projects(user["id"], is_admin=is_admin)
    _cur_pid = st.session_state.get("project_id")
    if not _sb_projects:
        st.caption(t("还没有项目，点上方 ＋ 新建。", "No projects yet — click ＋ above."))
    else:
        for _p in _sb_projects[:20]:
            _is_cur = _p["fs_project_id"] == _cur_pid
            if st.button(
                _p["name"],
                key=f"sb_p_{_p['fs_project_id']}",
                use_container_width=True,
                type="primary" if _is_cur else "secondary",
            ):
                st.session_state["project_id"] = _p["fs_project_id"]
                st.session_state.pop("summary", None)
                st.session_state.pop("outputs", None)
                st.rerun()

    # user card pinned to bottom (theme.py flex chain → this last container)
    with st.container():
        factory = user.get("factory_name") or ("管理员" if is_admin else "")
        st.markdown(
            '<div class="sb-user">'
            f'<div class="sb-avatar">{avatar_initial(user["username"])}</div>'
            f'<div class="who"><div class="u">{user["username"]}</div>'
            f'<div class="f">{factory}</div></div></div>',
            unsafe_allow_html=True,
        )
        if is_admin:
            if st.button(":material/settings: " + t("管理控制台", "Admin console"), use_container_width=True):
                st.switch_page("pages/admin.py")
        if st.button(":material/logout: " + t("退出登录", "Logout"), use_container_width=True):
            clear_session()
            st.switch_page("pages/login.py")

# ── Sync filesystem projects into DB (legacy projects created before auth) ──
db_ids = {p["fs_project_id"] for p in get_user_projects(user["id"], is_admin=is_admin)}
for fsp in manager.list_projects():
    fid = fsp["project"]["id"]
    if fid not in db_ids:
        register_project(fid, fsp["project"]["name"], owner_id=user["id"])

pid = st.session_state.get("project_id")

# ── Current project indicator (create / switch via the left sidebar) ────────
if pid:
    _cur_name = (manager.load_config(pid).get("project", {}) or {}).get("name", pid)
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:.5rem;margin:.1rem 0 .3rem;'
        f'font-size:1.05rem;color:#1f2d3d;">{icon("folder", 18)}'
        f'<span>{t("当前项目", "Current project")}：<b>{_cur_name}</b></span></div>',
        unsafe_allow_html=True,
    )
else:
    st.info(t("请在左侧『我的项目』点 ＋ 新建一个项目，或选择一个已有项目。",
              "Click ＋ in 'My Projects' on the left to create a project, or pick an existing one."))

# ── Step 1: Upload ──────────────────────────────────────────────────────────
st.divider()
step_header(1, t("上传工位视频", "Upload station videos"), "upload_cloud",
            t("每个视频 = 一个工位，可一次拖多个", "Each video = one station; drop several at once"))
# Per-project uploader key: switching projects gives a fresh, empty uploader.
uploads = st.file_uploader(
    t("拖入或选择视频（可多选，每个=一个工位，松开即自动加入）",
      "Drop or select videos (multiple; each = one station; auto-added on drop)"),
    type=["mp4", "avi", "mov", "mkv"],
    accept_multiple_files=True,
    key=f"uploader_{pid or 'new'}",
)
# Auto-import on upload — no separate "add stations" click. Dedup by
# (project, name, size) so reruns don't import the same file twice.
if uploads:
    target_pid = ensure_project(user["id"])
    processed = st.session_state.setdefault("_uploaded_sig", set())
    new_uploads = [up for up in uploads if (target_pid, up.name, up.size) not in processed]
    if new_uploads:
        for up in new_uploads:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(up.name).suffix) as tmp:
                tmp.write(up.getbuffer())
                tmp_path = Path(tmp.name)
            manager.import_video(target_pid, tmp_path, station_name=up.name)
            tmp_path.unlink(missing_ok=True)
            processed.add((target_pid, up.name, up.size))
        st.toast(t(f"已加入 {len(new_uploads)} 个工位", f"Added {len(new_uploads)} station(s)"), icon="✅")
        st.rerun()

pid = st.session_state.get("project_id")
stations = manager.load_config(pid).get("stations", []) if pid else []
if stations:
    st.caption(
        t("已加入 ", "Stations: ")
        + str(len(stations))
        + t(" 个工位：", ": ")
        + "、".join(s.get("name", "") for s in stations)
    )

# ── Project info (optional; powers Takt + 加人/换人/拆分工序 decisions) ──────
if pid:
    _pinfo = manager.load_project_info(pid)
    with st.expander(t("项目信息（可选，用于节拍/产能与加人·换人·拆分工序判断）",
                       "Project info (optional; enables Takt & add/swap/split decisions)"),
                     expanded=False):
        with st.form("project_info_form"):
            _r1 = st.columns(3)
            _industry = _r1[0].text_input(t("行业", "Industry"), value=_pinfo.get("industry", ""))
            _product = _r1[1].text_input(t("产品", "Product"), value=_pinfo.get("product", ""))
            _line = _r1[2].text_input(t("产线/工序", "Line/Process"), value=_pinfo.get("line_name", ""))
            _r2 = st.columns(3)
            _analyst = _r2[0].text_input(t("分析人员", "Analyst"), value=_pinfo.get("analyst", ""))
            try:
                _rd_default = datetime.fromisoformat(_pinfo["report_date"]).date() if _pinfo.get("report_date") else date.today()
            except Exception:
                _rd_default = date.today()
            _report_date = _r2[1].date_input(t("报告日期", "Report date"), value=_rd_default)
            _operator = _r2[2].number_input(t("现有工人数(0=未填)", "Workers (0=unset)"),
                                            min_value=0, step=1, value=int(_pinfo.get("operator_count") or 0))
            st.caption(t("下列为节拍/产能与人力判断所需（任一为0=未提供，将跳过节拍分析）：",
                         "Below feed Takt/capacity & manpower (any 0 = unset → Takt skipped):"))
            _r3 = st.columns(4)
            _shift = _r3[0].number_input(t("班次时长(分)", "Shift (min)"), min_value=0.0, step=30.0,
                                         value=float(_pinfo.get("shift_minutes") or 0.0))
            _break = _r3[1].number_input(t("休息(分,可为0)", "Break (min, 0 ok)"), min_value=0.0, step=10.0,
                                         value=float(_pinfo.get("break_minutes") or 0.0))
            _demand = _r3[2].number_input(t("班次需求量(件)", "Demand/shift"), min_value=0, step=10,
                                          value=int(_pinfo.get("demand_per_shift") or 0))
            _rate_pct = _r3[3].number_input(t("有效作业率(%)", "Effective rate (%)"),
                                            min_value=0.0, max_value=100.0, step=5.0,
                                            value=float((_pinfo.get("effective_rate") or 0.0) * 100))
            _r4 = st.columns(2)
            _allow = _r4[0].number_input(t("宽放系数(如1.13，0=未填)", "Allowance (e.g. 1.13, 0=unset)"),
                                         min_value=0.0, step=0.01, value=float(_pinfo.get("allowance_factor") or 0.0))
            _labor = _r4[1].number_input(t("人工成本(元/小时,0=未填)", "Labor cost/hr (0=unset)"),
                                         min_value=0.0, step=1.0, value=float(_pinfo.get("labor_cost_per_hour") or 0.0))
            if st.form_submit_button(t("保存项目信息", "Save project info"), type="primary"):
                manager.save_project_info(pid, {
                    "industry": _industry.strip(),
                    "product": _product.strip(),
                    "line_name": _line.strip(),
                    "analyst": _analyst.strip(),
                    "report_date": _report_date.isoformat(),
                    "operator_count": int(_operator) or None,
                    "shift_minutes": _shift or None,
                    "break_minutes": _break,  # 0 is a valid (no-break) value
                    "demand_per_shift": int(_demand) or None,
                    "effective_rate": (_rate_pct / 100.0) or None,
                    "allowance_factor": _allow or None,
                    "labor_cost_per_hour": _labor or None,
                })
                st.session_state.pop("summary", None)  # force takt/decisions recompute
                st.toast(t("已保存项目信息", "Project info saved"), icon="✅")
                st.rerun()
        _hard_missing = [k for k in ("shift_minutes", "demand_per_shift", "effective_rate")
                         if not manager.load_project_info(pid).get(k)]
        if _hard_missing:
            st.caption("⚠ " + t("未提供班次时长/需求量/有效率，将跳过节拍与人力(加人/换人)判断。",
                                "Missing shift/demand/rate; Takt & manpower decisions will be skipped."))

# ── Step 2: Analyze ─────────────────────────────────────────────────────────
st.divider()
step_header(2, t("开始分析", "Analyze"), "play",
            t("俯视工位走真实识别，其它走时长估算", "Top-down = real recognition; others = duration estimate"))
if not stations:
    st.info(t("请先在上方上传至少一个工位视频，按钮才会亮起。",
              "Upload at least one station video above to enable analysis."))
if st.button(":material/play_arrow: " + t("开始分析", "Run analysis"), type="primary", disabled=not stations):
    log_id = log_analysis_start(pid, user["id"])
    try:
        with st.spinner(t("正在分析（真实识别较慢，请稍候）...", "Analyzing (real recognition is slow)...")):
            summary_result = analyzer.analyze_project(pid)
        st.session_state["summary"] = summary_result
        line_m = summary_result.get("line_metrics", {})
        result_stations = summary_result.get("stations", [])
        log_analysis_done(log_id, {
            "lbr": line_m.get("lbr"),
            "station_count": len(result_stations),
            "bottleneck": (line_m.get("bottleneck") or {}).get("station_name"),
            "estimated_hourly_capacity": line_m.get("estimated_hourly_capacity"),
            "stations": [
                {
                    "name": s.get("station_name"),
                    "mode": s.get("analysis_mode"),
                    "cycle_time": s.get("cycle_time_metrics", {}).get("total_cycle_time"),
                    "efficiency": s.get("cycle_time_metrics", {}).get("efficiency"),
                    "action_count": s.get("mtm_summary", {}).get("action_count"),
                }
                for s in result_stations
            ],
        })
        update_project_status(pid, "done", station_count=len(result_stations))
        st.success(t("分析完成", "Analysis complete"))
    except Exception as e:
        log_analysis_done(log_id, {"error": str(e)}, status="error")
        update_project_status(pid, "error")
        st.error(str(e))

# ── Step 3: Results ──────────────────────────────────────────────────────────
st.divider()
step_header(3, t("分析结果", "Results"), "chart")
summary = st.session_state.get("summary") or (manager.load_summary(pid) if pid else {})
if summary and summary.get("stations"):
    lang = _lang()
    for s in summary["stations"]:
        m = s.get("cycle_time_metrics", {})
        mm = s.get("mtm_summary", {})
        with st.container():
            st.markdown(
                '<div class="result-card-marker"></div>'
                f'<div class="card-head"><span class="card-title">{icon("factory", 16)}'
                f'{s.get("station_name")}</span>'
                f'<span class="mode-pill">{mode_badge(s.get("analysis_mode"), lang)}</span></div>',
                unsafe_allow_html=True,
            )
            timeline = s.get("action_timeline") or []
            html = build_timeline_html(timeline, total_seconds=m.get("total_cycle_time"))
            if html:
                st.markdown(
                    f'<div class="tl-caption">{t("动作时间轴（手在每个时刻做什么）", "Action timeline — what the hand does over time")}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(html + timeline_legend_html(), unsafe_allow_html=True)
            elif s.get("analysis_mode") == "error":
                st.caption("⛔ " + (s.get("error") or ""))
            else:
                st.markdown(
                    f'<div class="tl-caption">{t("估算模式：仅有时长，无动作时间轴", "Estimate mode: duration only, no action timeline")}</div>',
                    unsafe_allow_html=True,
                )
            c = st.columns(4)
            c[0].metric(t("节拍", "Cycle"), f"{m.get('total_cycle_time', 0)}s", help=term_help("cycle_time", lang))
            c[1].metric(t("工时", "Work"), f"{mm.get('total_tmus', 0)} TMU", help=term_help("tmu", lang))
            c[2].metric(t("效率", "Efficiency"), f"{m.get('efficiency', 0)}%", help=term_help("efficiency", lang))
            c[3].metric(t("动作数", "Actions"), mm.get("action_count", 0))

    line = summary.get("line_metrics", {})
    if line:
        with st.container():
            st.markdown(
                '<div class="summary-card-marker"></div>'
                f'<div class="card-title">{icon("gauge", 16)}{t("产线汇总", "Line summary")}</div>',
                unsafe_allow_html=True,
            )
            b = st.columns(3)
            lbr_val = line.get("lbr", 0)
            b[0].metric("LBR", f"{lbr_val}%", help=term_help("lbr", lang))
            if pid:
                lbr_target = manager.load_config(pid).get("target", {}).get("lbr_target")
                if lbr_target:
                    ok = lbr_val >= lbr_target
                    cls = "lbr-ok" if ok else "lbr-warn"
                    mark = icon("target", 13)
                    tail = t("（达标）", " met") if ok else t("（未达标）", " below")
                    b[0].markdown(
                        f'<div class="lbr-target {cls}">{mark}'
                        f'<span>{t("目标", "Target")} {lbr_target}%{tail}</span></div>',
                        unsafe_allow_html=True,
                    )
            bottleneck = (line.get("bottleneck") or {}).get("station_name", "-")
            b[1].metric(t("瓶颈工位", "Bottleneck"), bottleneck, help=term_help("bottleneck", lang))
            b[2].metric(t("小时产能", "Pieces/hour"), line.get("estimated_hourly_capacity", 0), help=term_help("capacity", lang))

    # ── Takt / capacity (节拍与产能) ──────────────────────────────────────
    takt = summary.get("takt_analysis") or {}
    if takt.get("skipped"):
        st.caption("ℹ " + t("节拍分析：", "Takt: ") + (takt.get("skip_reason") or ""))
    elif takt.get("takt_time_s"):
        with st.container():
            st.markdown(
                f'<div class="card-title">{icon("clock", 16)}{t("节拍与产能", "Takt & capacity")}</div>',
                unsafe_allow_html=True,
            )
            cap_ok = takt.get("capacity_status") == "ok"
            tk = st.columns(4)
            tk[0].metric(t("客户节拍 Takt", "Takt time"), f"{takt.get('takt_time_s')}s")
            tk[1].metric(t("瓶颈节拍", "Bottleneck cycle"), f"{takt.get('bottleneck_cycle_s', '-')}s")
            tk[2].metric(t("产能", "Capacity"),
                         t("充足", "OK") if cap_ok else t("不足", "Short"))
            _req, _cur = takt.get("required_workers"), takt.get("current_workers")
            tk[3].metric(t("需求/现有人数", "Need/Have"),
                         f"{_req if _req is not None else '-'} / {_cur if _cur is not None else '-'}")

    # ── 改善决策：加人 / 换人 / 拆分工序（产品靶心）───────────────────────
    actions = summary.get("action_recommendations") or []
    if actions:
        _label = {"add_worker": ("➕ " + t("加人", "Add worker"), "lbr-warn"),
                  "split_task": ("✂ " + t("拆分工序", "Split task"), "lbr-warn"),
                  "swap_worker": ("🔄 " + t("换人/调岗", "Swap/Reassign"), "lbr-warn"),
                  "ok": ("✓ " + t("维持现状", "Keep as-is"), "lbr-ok")}
        with st.container():
            st.markdown(
                f'<div class="card-title">{icon("target", 16)}{t("改善决策", "Action verdict")}</div>',
                unsafe_allow_html=True,
            )
            for a in actions:
                lbl, cls = _label.get(a.get("action"), (a.get("action", ""), "lbr-warn"))
                tgt = a.get("target", "")
                st.markdown(
                    f'<div class="lbr-target {cls}" style="align-items:flex-start">'
                    f'<span><b>{lbl}</b>（{tgt}）：{a.get("reason", "")}</span></div>',
                    unsafe_allow_html=True,
                )

    with st.expander(t("原始数据 (JSON)", "Raw data (JSON)")):
        st.json(summary)
else:
    st.info(t("还没有结果。先上传视频，再点『开始分析』。", "No results yet. Upload videos, then Run analysis."))

# ── Step 4: Export ──────────────────────────────────────────────────────────
st.divider()
step_header(4, t("导出报告", "Export report"), "download")
if summary and summary.get("stations"):
    _ai_on = st.session_state.get("use_ai", True)
    st.caption(t("报告由 DeepSeek 结合 IE 理论知识库生成分析（数字由系统精确计算）；启用 AI 时约需 10–30 秒。"
                 if _ai_on else "AI 未启用，将用规则引擎生成报告。可在高级设置中开启 AI。",
                 "Report narrative by DeepSeek grounded in the IE knowledge base (numbers are computed); "
                 "~10–30s with AI on." if _ai_on else "AI off; report uses the rule engine."))
    if st.button(":material/description: " + t("生成报告 (PDF/CSV/JSON)", "Generate report (PDF/CSV/JSON)")):
        with st.spinner(t("正在生成报告（AI 撰写分析中，请稍候）...", "Generating report (AI is writing the analysis)...")):
            st.session_state["outputs"] = reporter.generate(
                pid,
                use_ai=st.session_state.get("use_ai", True),
                provider=st.session_state.get("provider", "deepseek"),
            )
    outputs = st.session_state.get("outputs")
    if outputs:
        _src = (outputs.get("narrative_source") or "")
        if _src.startswith("ai_"):
            st.success(t("报告分析由 AI 生成（" + _src.replace("ai_", "") + "）。",
                         "Report narrative generated by AI (" + _src.replace("ai_", "") + ")."))
        elif _src:
            st.info(t("报告分析由规则引擎生成（AI 未启用或不可用）。",
                      "Report narrative generated by the rule engine (AI off/unavailable)."))
        dl = st.columns(3)
        for col, (label, key) in zip(dl, [("PDF", "pdf"), ("CSV", "csv"), ("JSON", "json")]):
            file_path = Path(outputs[key])
            if file_path.exists():
                col.download_button(":material/download: " + label, file_path.read_bytes(),
                                    file_name=file_path.name, use_container_width=True)
else:
    st.caption(t("分析完成后即可导出。", "Export becomes available after analysis."))

# ── Advanced settings ───────────────────────────────────────────────────────
if show_adv and pid:
    st.divider()
    st.markdown(
        f'<div class="step-head"><span class="step-ic">{icon("sliders", 20)}</span>'
        f'<span class="step-title">{t("高级设置", "Advanced settings")}</span></div>',
        unsafe_allow_html=True,
    )
    config = manager.load_config(pid)

    with st.expander(t("工位参数 / 机位类型", "Station params / camera view")):
        st.caption(t("节拍填0=用视频时长；等待填-1=自动估算；机位 top_down 走真实识别。",
                     "Cycle 0 = use duration; wait -1 = auto; view top_down uses real recognition."))
        view_map = {t("俯视(真实识别)", "Top-down (real)"): "top_down",
                    t("正面(估算)", "Front (estimate)"): "front",
                    t("未指定(估算)", "Unspecified (estimate)"): ""}
        view_labels = list(view_map.keys())
        view_values = list(view_map.values())
        with st.form("station_form"):
            edited = []
            for stn in config.get("stations", []):
                col = st.columns([2, 1, 1, 1.6])
                name = col[0].text_input(t("名称", "Name"), value=stn.get("name", ""), key=f"n_{stn['id']}")
                cyc = col[1].number_input(t("节拍覆盖", "Cycle"), value=float(stn.get("cycle_time") or 0.0),
                                          min_value=0.0, step=1.0, key=f"c_{stn['id']}")
                wat = col[2].number_input(t("等待覆盖", "Wait"), value=float(stn.get("manual_wait_time", -1.0)),
                                          min_value=-1.0, step=1.0, key=f"w_{stn['id']}")
                cur_view = stn.get("view_type") or ""
                vi = view_values.index(cur_view) if cur_view in view_values else len(view_values) - 1
                vlabel = col[3].selectbox(t("机位", "View"), view_labels, index=vi, key=f"v_{stn['id']}")
                upd = dict(stn)
                upd["name"] = name
                upd["cycle_time"] = cyc if cyc > 0 else None
                if wat >= 0:
                    upd["manual_wait_time"] = wat
                else:
                    upd.pop("manual_wait_time", None)
                vval = view_map[vlabel]
                if vval:
                    upd["view_type"] = vval
                else:
                    upd.pop("view_type", None)
                edited.append(upd)
            if st.form_submit_button(t("保存工位设置", "Save stations")):
                config["stations"] = edited
                manager.save_config(pid, config)
                st.rerun()

    with st.expander(t("分析参数", "Analysis tuning")):
        analysis = config.setdefault("analysis", {})
        vision = analysis.setdefault("vision", {})
        tuning = analysis.setdefault("tuning", {})
        with st.form("tuning_form"):
            analysis["concurrency"] = st.slider(t("并发数(仅估算工位)", "Concurrency (estimate only)"),
                                                 1, 8, int(analysis.get("concurrency", 2)))
            r1 = st.columns(3)
            analysis["sample_rate"] = r1[0].number_input(t("抽帧步长", "Frame stride"),
                                                          value=int(analysis.get("sample_rate", 5)), min_value=1, step=1)
            vision["min_hand_confidence"] = r1[1].number_input(t("手部置信度(低清调到0.2)", "Hand conf (0.2 for low-res)"),
                                                               value=float(vision.get("min_hand_confidence", 0.3)),
                                                               min_value=0.05, max_value=0.9, step=0.05)
            vision["min_action_frames"] = r1[2].number_input(t("最小动作帧", "Min action frames"),
                                                             value=int(vision.get("min_action_frames", 4)), min_value=1, step=1)
            r2 = st.columns(3)
            tuning["min_cycle_time"] = r2[0].number_input(t("最小节拍", "Min cycle"), value=float(tuning.get("min_cycle_time", 5.0)), min_value=1.0, step=1.0)
            tuning["max_cycle_time"] = r2[1].number_input(t("最大节拍", "Max cycle"), value=float(tuning.get("max_cycle_time", 180.0)), min_value=10.0, step=10.0)
            tuning["wait_ratio_min"] = r2[2].number_input(t("等待占比下限", "Wait ratio min"), value=float(tuning.get("wait_ratio_min", 0.06)), min_value=0.0, max_value=0.8, step=0.01)
            r3 = st.columns(3)
            tuning["wait_ratio_max"] = r3[0].number_input(t("等待占比上限", "Wait ratio max"), value=float(tuning.get("wait_ratio_max", 0.22)), min_value=0.0, max_value=0.8, step=0.01)
            tuning["action_seconds_min"] = r3[1].number_input(t("单动作秒数下限", "Action sec min"), value=float(tuning.get("action_seconds_min", 2.5)), min_value=0.5, step=0.5)
            tuning["action_seconds_max"] = r3[2].number_input(t("单动作秒数上限", "Action sec max"), value=float(tuning.get("action_seconds_max", 5.0)), min_value=1.0, step=0.5)
            if st.form_submit_button(t("保存参数", "Save params")):
                manager.save_config(pid, config)
                st.rerun()

    with st.expander(t("AI 分析与改善建议", "AI analysis & suggestions")):
        st.session_state["use_ai"] = st.checkbox(
            t("调用 AI 生成报告分析与改善建议", "Use AI for report narrative & suggestions"),
            value=st.session_state.get("use_ai", True))
        st.caption(t("开启后，报告的诊断/根因/改善方案由 DeepSeek 结合 IE 理论库撰写（数字仍由系统计算）；关闭则用规则引擎。",
                     "On: DeepSeek writes the report analysis grounded in the IE knowledge base (numbers stay computed). Off: rule engine."))
        st.session_state["provider"] = st.selectbox(t("AI 提供商", "Provider"), ["deepseek", "qwen", "kimi"],
                                                     index=["deepseek", "qwen", "kimi"].index(st.session_state.get("provider", "deepseek")))

    with st.expander(t("准确率验证", "Accuracy validation")):
        st.caption(t("以动作数准确率为核心；节拍准确率为弱证据。", "Action-count accuracy is the key; cycle accuracy is weak evidence."))
        paths = manager.get_paths(pid)
        template_path = paths.exports / "ground_truth_template.csv"
        vc = st.columns(2)
        if vc[0].button(t("生成标注模板", "Make template")):
            template_path = validator.create_ground_truth_template(pid)
            st.rerun()
        if template_path.exists():
            vc[1].download_button(t("下载模板", "Download template"), template_path.read_bytes(),
                                  file_name=template_path.name, mime="text/csv")
        uploaded_truth = st.file_uploader(t("上传已填写的标注 CSV", "Upload filled ground-truth CSV"), type=["csv"], key="gt_upload")
        use_existing = st.checkbox(t("用项目里的模板文件验证", "Use project template file"), value=False)
        tcols = st.columns(3)
        a_tol = tcols[0].number_input(t("动作数容许误差", "Action tol"), value=2, min_value=0, step=1)
        c_tol = tcols[1].number_input(t("节拍容许误差(%)", "Cycle tol %"), value=10.0, min_value=0.0, step=1.0)
        w_tol = tcols[2].number_input(t("等待容许误差(%)", "Wait tol %"), value=20.0, min_value=0.0, step=1.0)
        if st.button(t("运行验证", "Run validation")):
            gt_file = None
            if uploaded_truth is not None:
                gt_file = paths.exports / "ground_truth_uploaded.csv"
                gt_file.write_bytes(uploaded_truth.getbuffer())
            elif use_existing and template_path.exists():
                gt_file = template_path
            if gt_file is None:
                st.warning(t("请上传标注 CSV 或勾选使用模板文件。", "Upload a CSV or tick 'use template'."))
            else:
                report = validator.validate(pid, gt_file, ValidationThresholds(int(a_tol), float(c_tol), float(w_tol)))
                vs = report.get("summary", {})
                rc = st.columns(4)
                rc[0].metric(t("动作数准确率", "Action acc."), f"{vs.get('action_count_accuracy_pct') or 0}%")
                rc[1].metric(t("已验证工位", "Validated"), vs.get("validated_station_count", 0))
                rc[2].metric(t("达标率", "Pass rate"), f"{vs.get('pass_rate_pct', 0)}%")
                rc[3].metric(t("节拍准确率", "Cycle acc."), f"{vs.get('cycle_time_accuracy_pct') or 0}%")
                if vs.get("cycle_time_note"):
                    st.caption("⚠ " + vs["cycle_time_note"])
