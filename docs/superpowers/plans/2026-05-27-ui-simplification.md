# 前端向导式简化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 4 标签页的 Streamlit 前端改成向导式单页（上传→分析→结果→导出），新增动作时间轴，术语加人话解释，内部功能收进「高级设置」。

**Architecture:** 把可测试逻辑（时间轴 HTML、术语表、识别徽章）抽成 `src/utils/ui_helpers.py` 纯函数并用 TDD 覆盖；后端结果新增 `action_timeline` 字段供时间轴渲染；`app/streamlit_project_app.py` 重写为向导单页并复用这些 helper，靠"启动应用 + py_compile"验证。

**Tech Stack:** Python 3.13、Streamlit、MediaPipe Tasks、ultralytics/torch、现有 vision pipeline。

**注意：本项目不是 git 仓库**，所以每个任务最后一步是"验证检查点"（运行所列检查），不是 git commit。所有命令需在 `files-mentioned-by-the-user-ie/` 目录、且带 `KMP_DUPLICATE_LIB_OK=TRUE` 前缀（torch/mediapipe OpenMP 规避）。

参考规格：`docs/superpowers/specs/2026-05-27-ui-simplification-design.md`

---

## File Structure

| 文件 | 职责 | 动作 |
|---|---|---|
| `src/core/vision/actions.py` | 加 `segments_to_timeline()` 把分段转成 UI 用的列表 | Modify |
| `src/core/vision/base.py` | `assemble_result` 增加可选 `action_timeline` 写入结果 | Modify |
| `src/core/vision/hands_yolo.py` | 把 `classify()` 的 segments 转 timeline 传入结果 | Modify |
| `src/utils/ui_helpers.py` | 术语表、动作配色、时间轴 HTML、识别徽章（纯函数）| Create |
| `tests/test_ui_helpers.py` | 覆盖 ui_helpers 纯函数 | Create |
| `tests/test_vision.py` | 增 timeline 相关断言 | Modify |
| `app/streamlit_project_app.py` | 4 tabs → 向导单页 + 高级折叠区，复用 helper | Rewrite |

---

## Task 1: 动作分段转时间轴列表（actions.segments_to_timeline）

**Files:**
- Modify: `src/core/vision/actions.py`
- Test: `tests/test_vision.py`

- [ ] **Step 1: 写失败测试** — 加到 `tests/test_vision.py`

```python
def test_segments_to_timeline() -> None:
    from src.core.vision.actions import ActionSegment, segments_to_timeline
    segs = [ActionSegment("R_伸手", 0.0, 1000.0), ActionSegment("Wait_等待", 1000.0, 3000.0)]
    tl = segments_to_timeline(segs)
    assert tl == [
        {"label": "R_伸手", "start_s": 0.0, "end_s": 1.0},
        {"label": "Wait_等待", "start_s": 1.0, "end_s": 3.0},
    ]
    assert segments_to_timeline([]) == []
    print("segments_to_timeline OK")
```

并在 `main()` 里调用 `test_segments_to_timeline()`。

- [ ] **Step 2: 运行测试确认失败**

Run: `KMP_DUPLICATE_LIB_OK=TRUE python tests/test_vision.py`
Expected: FAIL — `ImportError: cannot import name 'segments_to_timeline'`

- [ ] **Step 3: 实现** — 在 `src/core/vision/actions.py` 末尾（`classify` 之后）追加

```python
def segments_to_timeline(segments: list[ActionSegment]) -> list[dict[str, float | str]]:
    """Convert action segments to a UI-friendly timeline list (seconds)."""
    return [
        {"label": seg.label, "start_s": round(seg.start_ms / 1000.0, 2), "end_s": round(seg.end_ms / 1000.0, 2)}
        for seg in segments
    ]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `KMP_DUPLICATE_LIB_OK=TRUE python tests/test_vision.py`
Expected: PASS，打印 `segments_to_timeline OK`

- [ ] **Step 5: 检查点** — `python -m py_compile src/core/vision/actions.py` 无报错。

---

## Task 2: 结果带上 action_timeline（base + hands_yolo + heuristic）

**Files:**
- Modify: `src/core/vision/base.py`（`assemble_result`）
- Modify: `src/core/vision/hands_yolo.py`（`analyze`）
- Test: `tests/test_vision.py`

- [ ] **Step 1: 写失败测试** — 加到 `tests/test_vision.py`

```python
def test_assemble_result_carries_timeline() -> None:
    from src.core.vision.heuristic import HeuristicEstimatePipeline
    p = HeuristicEstimatePipeline()
    station = {"id": "s", "name": "t", "video_file": "x.mp4"}
    timeline = [{"label": "R_伸手", "start_s": 0.0, "end_s": 1.0}]
    r = p.assemble_result(station, total_cycle_time=10.0, wait_time=2.0, action_count=1,
                          action_breakdown={"R_伸手": 1.0}, runtime_seconds=0.1, action_timeline=timeline)
    assert r["action_timeline"] == timeline
    # 不传时为空列表（估算模式）
    r2 = p.assemble_result(station, total_cycle_time=10.0, wait_time=2.0, action_count=1,
                           action_breakdown={}, runtime_seconds=0.1)
    assert r2["action_timeline"] == []
    print("assemble_result timeline OK")
```

并在 `main()` 里调用。

- [ ] **Step 2: 运行确认失败**

Run: `KMP_DUPLICATE_LIB_OK=TRUE python tests/test_vision.py`
Expected: FAIL — `TypeError: assemble_result() got an unexpected keyword argument 'action_timeline'`

- [ ] **Step 3a: 改 `base.py`** — `assemble_result` 签名与结果体

把签名末尾加参数：
```python
    def assemble_result(
        self,
        station: dict[str, Any],
        *,
        total_cycle_time: float,
        wait_time: float,
        action_count: int,
        action_breakdown: dict[str, float],
        runtime_seconds: float,
        action_timeline: list[dict[str, Any]] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
```
在 `result` 字典里 `"analysis_mode": self.analysis_mode,` 之后加一行：
```python
            "action_timeline": action_timeline or [],
```

- [ ] **Step 3b: 改 `hands_yolo.py`** — `analyze` 传入 timeline

把 `_segments, summary = classify(signals, self.classifier_params)` 改为：
```python
        from .actions import segments_to_timeline
        segments, summary = classify(signals, self.classifier_params)
```
并在 `return self.assemble_result(...)` 调用里，`runtime_seconds=...` 之后加：
```python
            action_timeline=segments_to_timeline(segments),
```

- [ ] **Step 4: 运行确认通过**

Run: `KMP_DUPLICATE_LIB_OK=TRUE python tests/test_vision.py`
Expected: PASS，打印 `assemble_result timeline OK`，且原有 `test_pipeline_smoke` 仍通过。

- [ ] **Step 5: 检查点** — `python -m py_compile src/core/vision/base.py src/core/vision/hands_yolo.py` 无报错。

---

## Task 3: UI 纯函数 helper（术语/配色/时间轴HTML/徽章）

**Files:**
- Create: `src/utils/ui_helpers.py`
- Test: `tests/test_ui_helpers.py`

- [ ] **Step 1: 写失败测试** — 新建 `tests/test_ui_helpers.py`

```python
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.ui_helpers import TERMS, build_timeline_html, mode_badge


def test_terms_have_both_languages() -> None:
    for key, val in TERMS.items():
        assert "zh" in val and "en" in val and val["zh"], key


def test_build_timeline_html() -> None:
    tl = [{"label": "R_伸手", "start_s": 0.0, "end_s": 1.0},
          {"label": "Wait_等待", "start_s": 1.0, "end_s": 3.0}]
    html = build_timeline_html(tl)
    assert "width:33.33%" in html or "width:33.3" in html  # 1/3 段
    assert "width:66.6" in html                            # 2/3 段
    assert build_timeline_html([]) == ""                   # 空 → 空串


def test_mode_badge() -> None:
    assert "真实" in mode_badge("vision_handsyolo", "zh")
    assert "估算" in mode_badge("heuristic_estimate", "zh")
    assert "失败" in mode_badge("error", "zh")


def main() -> None:
    test_terms_have_both_languages()
    test_build_timeline_html()
    test_mode_badge()
    print("ui_helpers 测试通过")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行确认失败**

Run: `python tests/test_ui_helpers.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.utils.ui_helpers'`

- [ ] **Step 3: 实现** — 新建 `src/utils/ui_helpers.py`

```python
from __future__ import annotations

from typing import Any

# 动作 → 颜色（与 vision/actions.py 的 R/G/M/A/Wait 标签一致）
ACTION_COLORS: dict[str, str] = {
    "R_伸手": "#3b82f6",
    "G_抓取": "#f59e0b",
    "M_移动": "#10b981",
    "A_装配": "#8b5cf6",
    "Wait_等待": "#cbd5e1",
}

# 术语 → 人话（双语）。用于指标卡 help/小字与时间轴图例。
TERMS: dict[str, dict[str, str]] = {
    "cycle_time": {"zh": "完成一件产品的时间", "en": "time to finish one piece"},
    "lbr": {"zh": "各工位忙闲是否均衡，越高越好", "en": "how balanced station loads are; higher is better"},
    "tmu": {"zh": "标准工时单位（1 TMU = 0.036 秒）", "en": "standard time unit (1 = 0.036s)"},
    "bottleneck": {"zh": "最慢、限制整线产能的工位", "en": "slowest station, caps line output"},
    "efficiency": {"zh": "真正在干活的时间占比", "en": "share of time doing real work"},
    "wait": {"zh": "等待 / 无效时间", "en": "idle / non-value time"},
    "capacity": {"zh": "每小时能产出多少件", "en": "pieces produced per hour"},
}

_MODE_LABELS = {
    "vision_handsyolo": {"zh": "✅ 真实识别", "en": "✅ Real recognition"},
    "heuristic_estimate": {"zh": "⚠ 时长估算（非识别）", "en": "⚠ Duration estimate"},
    "error": {"zh": "⛔ 分析失败", "en": "⛔ Analysis failed"},
}


def term_help(key: str, lang: str = "zh") -> str:
    """术语对应的人话解释；找不到返回空串。"""
    return TERMS.get(key, {}).get(lang, "")


def mode_badge(mode: str | None, lang: str = "zh") -> str:
    fallback = {"zh": "⚠ 时长估算（非识别）", "en": "⚠ Duration estimate"}
    return _MODE_LABELS.get(mode or "", fallback)[lang]


def build_timeline_html(timeline: list[dict[str, Any]], total_seconds: float | None = None) -> str:
    """把动作分段渲染成等比宽度的彩色横条 HTML。空 timeline 返回空串。"""
    if not timeline:
        return ""
    if total_seconds is None:
        total_seconds = max((float(s["end_s"]) for s in timeline), default=0.0)
    if total_seconds <= 0:
        return ""
    spans = []
    for seg in timeline:
        width = max(0.0, (float(seg["end_s"]) - float(seg["start_s"])) / total_seconds * 100.0)
        color = ACTION_COLORS.get(seg["label"], "#9ca3af")
        title = f'{seg["label"]} {float(seg["start_s"]):.1f}-{float(seg["end_s"]):.1f}s'
        spans.append(
            f'<span title="{title}" '
            f'style="display:inline-block;width:{width:.2f}%;height:18px;background:{color}"></span>'
        )
    return (
        '<div style="white-space:nowrap;width:100%;border-radius:4px;overflow:hidden;'
        'border:1px solid #e6ebf2">' + "".join(spans) + "</div>"
    )


def timeline_legend_html() -> str:
    """动作配色图例。"""
    items = []
    for label, color in ACTION_COLORS.items():
        items.append(
            f'<span style="margin-right:12px;font-size:12px">'
            f'<span style="display:inline-block;width:10px;height:10px;background:{color};'
            f'border-radius:2px;margin-right:4px"></span>{label}</span>'
        )
    return '<div style="margin-top:4px">' + "".join(items) + "</div>"
```

- [ ] **Step 4: 运行确认通过**

Run: `python tests/test_ui_helpers.py`
Expected: PASS，打印 `ui_helpers 测试通过`

- [ ] **Step 5: 检查点** — `python -m py_compile src/utils/ui_helpers.py tests/test_ui_helpers.py` 无报错。

---

## Task 4: 重写 streamlit 为向导单页 + 高级折叠区

**Files:**
- Rewrite: `app/streamlit_project_app.py`
- 复用：`src/utils/ui_helpers.py`（Task 3）、结果里的 `action_timeline`（Task 2）

> 这是一个连贯的大改，按下面的"页面结构蓝图"逐段实现。保留文件顶部已有的 `os.environ.setdefault("KMP_DUPLICATE_LIB_OK","TRUE")`、`apply_theme()`、`TEXT` i18n（在其上**增补**新键，不删旧键，便于高级区复用）。

- [ ] **Step 1: 顶部条 + 项目自动管理**

- 保留语言切换、`apply_theme()`。
- 顶部用 `st.columns` 放：标题、`项目 [打开已有 ▾]`、`[+ 新建项目]`、`⚙ 高级设置`（用 `st.toggle("⚙ 高级设置")` 控制底部高级区显隐）。
- 若 `st.session_state` 无 `project_id`：不再 `st.stop()`，而是允许进入"① 上传"。在"② 开始分析"被点击且当前无项目时，调用 `manager.create_project("快速分析", "")` 自动建项目并存入 session（规格 3.1，`project_manager.py` 不改）。

- [ ] **Step 2: ① 上传区**

```python
st.subheader("① 上传工位视频")
uploads = st.file_uploader("拖入或选择视频（可多选，每个=一个工位）",
                           type=["mp4", "avi", "mov", "mkv"], accept_multiple_files=True)
if uploads and st.button("加入工位"):
    pid = ensure_project()              # 无项目则自动创建
    for up in uploads:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(up.name).suffix) as tmp:
            tmp.write(up.getbuffer()); tmp_path = Path(tmp.name)
        manager.import_video(pid, tmp_path, station_name=up.name)
        tmp_path.unlink(missing_ok=True)
    st.rerun()
```
（`ensure_project()` 为本文件内新增的小函数：返回 session 里的 project_id，没有就 `manager.create_project(...)`。）
下面用 `st.caption` 列出当前已加入的工位数。

- [ ] **Step 3: ② 一键分析**

```python
st.subheader("② 开始分析")
if st.button("▶ 开始分析", type="primary", disabled=not has_stations()):
    with st.spinner("正在分析（真实识别较慢，请稍候）..."):
        st.session_state["summary"] = analyzer.analyze_project(st.session_state["project_id"])
```

- [ ] **Step 4: ③ 结果区（含动作时间轴 + 指标卡 + 徽章 + 改善建议）**

```python
from src.utils.ui_helpers import build_timeline_html, timeline_legend_html, mode_badge, term_help
summary = st.session_state.get("summary") or (manager.load_summary(pid) if pid else None)
if summary and summary.get("stations"):
    st.subheader("③ 分析结果")
    for s in summary["stations"]:
        m = s.get("cycle_time_metrics", {}); mm = s.get("mtm_summary", {})
        st.markdown(f"**{s['station_name']}** &nbsp; {mode_badge(s.get('analysis_mode'), lang)}",
                    unsafe_allow_html=True)
        tl = s.get("action_timeline") or []
        html = build_timeline_html(tl, total_seconds=m.get("total_cycle_time"))
        if html:
            st.markdown("动作时间轴（手在每个时刻做什么）：", help="按 伸手/抓取/移动/装配/等待 着色")
            st.markdown(html + timeline_legend_html(), unsafe_allow_html=True)
        else:
            st.caption("估算模式：仅有时长，无动作时间轴。" if s.get("analysis_mode") != "error"
                       else f"分析失败：{s.get('error','')}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("节拍", f"{m.get('total_cycle_time',0)}s", help=term_help('cycle_time', lang))
        c2.metric("工时", f"{mm.get('total_tmus',0)} TMU", help=term_help('tmu', lang))
        c3.metric("效率", f"{m.get('efficiency',0)}%", help=term_help('efficiency', lang))
        c4.metric("动作数", mm.get('action_count',0))
        st.divider()
    line = summary.get("line_metrics", {})
    b1, b2, b3 = st.columns(3)
    b1.metric("LBR 线平衡率", f"{line.get('lbr',0)}%", help=term_help('lbr', lang))
    b2.metric("瓶颈工位", (line.get('bottleneck') or {}).get('station_name','-'), help=term_help('bottleneck', lang))
    b3.metric("小时产能", line.get('estimated_hourly_capacity',0), help=term_help('capacity', lang))
    # 改善建议（沿用现有 reporter / improvement 逻辑的展示，可直接 st.write 规则结果）
```

- [ ] **Step 5: ④ 导出区**

沿用现有 reporter：按钮触发 `reporter.generate(pid, use_ai=..., provider=...)`，再用 `st.download_button` 给 PDF/CSV/JSON（`use_ai`/`provider` 默认值放这里，详细选择在高级区）。

- [ ] **Step 6: ⚙ 高级设置（折叠区，搬入内部功能）**

`if st.session_state.get("show_advanced"):` 内放一个 `st.expander` 群组，把原 4 标签里的这些**原样搬入**（逻辑代码复用，不重写）：
- 工位参数修正（名称/节拍覆盖/等待覆盖/机位 view_type 下拉，已有代码）。
- 分析调参（concurrency / sample_rate / min_hand_confidence / tuning 各项）。
- 准确率验证整块（生成模板/上传 ground truth/跑验证/看误差，含 `cycle_time_note` 提示）。
- AI 提供商选择（deepseek/kimi/qwen）。

- [ ] **Step 7: 语法检查**

Run: `python -m py_compile app/streamlit_project_app.py`
Expected: 无输出（成功）

- [ ] **Step 8: 启动应用验证**

先停旧实例（若在跑）：找 `:8501` 监听 PID 用 `taskkill //PID <pid> //F`。
Run（后台）：`KMP_DUPLICATE_LIB_OK=TRUE python -m streamlit run app/streamlit_project_app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false`
验证：`curl -s -o /dev/null -w "%{http_code}" http://localhost:8501` → `200`，且启动日志无 traceback。

- [ ] **Step 9: 检查点** — 人工在浏览器确认：单页四步可见；上传→分析→出现彩色时间轴 + 指标卡（悬停有人话）；「⚙ 高级设置」里能找到调参/验证/机位/AI。

---

## Task 5: 全量回归与收尾

**Files:** 无新增，仅运行验证

- [ ] **Step 1: 后端回归**

Run: `KMP_DUPLICATE_LIB_OK=TRUE python tests/test_core_flow.py`
Expected: 打印"核心流程测试通过"、LBR、PDF 路径。

- [ ] **Step 2: 视觉 + helper 测试**

Run: `KMP_DUPLICATE_LIB_OK=TRUE python tests/test_vision.py` → "视觉测试通过"
Run: `python tests/test_ui_helpers.py` → "ui_helpers 测试通过"

- [ ] **Step 3: 端到端真实视觉一次**

用一个高清测试视频，确认结果里 `action_timeline` 非空、UI 时间轴能画出来（人眼看 :8501）。

- [ ] **Step 4: 检查点** — 三个测试套件全绿 + 应用 HTTP 200 + 时间轴可见。

---

## Self-Review（已执行）

- **Spec coverage：** 向导单页(Task4 S1-5)✓；高级区收纳(Task4 S6)✓；术语+人话(Task3 TERMS/term_help + Task4 help=)✓；动作时间轴(Task1+2 后端字段，Task3 build_timeline_html，Task4 S4 渲染)✓；估算模式不伪造时间轴(Task2 空列表 + Task4 caption)✓；不改算法/报告/验证逻辑(验证仅搬位置, Task4 S6)✓；不换技术栈✓。
- **Placeholder：** 无 TBD/TODO；Task4 为连贯重写，已给每段关键代码与结构蓝图（非占位）。
- **Type 一致：** `action_timeline` 元素 `{label,start_s,end_s}` 在 Task1 产出、Task2 写入、Task3 `build_timeline_html` 消费，键名一致；`mode_badge`/`term_help` 签名跨 Task3↔Task4 一致。
