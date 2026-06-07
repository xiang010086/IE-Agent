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
    if not total_seconds or total_seconds <= 0:
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
