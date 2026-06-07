from __future__ import annotations

from pathlib import Path
from typing import Any

# action-label prefix -> English (matplotlib lacks a CJK font by default, so the
# PNG uses ASCII labels; Chinese captions are added by ReportLab in the PDF).
_EN_LABEL = {
    "R": "Reach", "G": "Grasp", "M": "Move", "A": "Assemble",
    "Wait": "Wait", "RL": "Release", "I": "Inspect",
}


def station_bar_data(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for station in summary.get("stations", []):
        metrics = station.get("cycle_time_metrics", {})
        rows.append(
            {
                "工位": station.get("station_name"),
                "节拍时间": metrics.get("total_cycle_time", 0),
                "有效时间": metrics.get("effective_time", 0),
                "等待时间": metrics.get("wait_time", 0),
            }
        )
    return rows


def render_timeline_png(
    timeline: list[dict[str, Any]],
    out_path: str | Path,
    total_seconds: float | None = None,
    title: str | None = None,
    width_px: int = 900,
    height_px: int = 140,
) -> Path | None:
    """Render the action timeline to a horizontal bar PNG.

    Returns the path on success; ``None`` if the timeline is empty (heuristic /
    estimate stations) or matplotlib is unavailable — caller then prints a
    placeholder. Uses ASCII labels to avoid missing-CJK-glyph boxes.
    """
    if not timeline:
        return None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch
    except Exception:
        return None

    from .ui_helpers import ACTION_COLORS

    if total_seconds is None:
        total_seconds = max((float(s["end_s"]) for s in timeline), default=0.0)
    if not total_seconds or total_seconds <= 0:
        return None

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(width_px / 100.0, height_px / 100.0), dpi=100)
    used: dict[str, str] = {}
    for seg in timeline:
        start = float(seg["start_s"])
        end = float(seg["end_s"])
        label = seg.get("label", "")
        color = ACTION_COLORS.get(label, "#9ca3af")
        ax.broken_barh([(start, max(0.0, end - start))], (0, 1), facecolors=color)
        used[_EN_LABEL.get(str(label).split("_")[0], str(label))] = color

    ax.set_xlim(0, total_seconds)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("seconds")
    if title:
        ax.set_title(title, fontsize=9)
    handles = [Patch(facecolor=c, label=lbl) for lbl, c in used.items()]
    if handles:
        ax.legend(handles=handles, ncol=min(len(handles), 5), loc="upper center",
                  bbox_to_anchor=(0.5, -0.45), fontsize=7, frameon=False)
    try:
        fig.savefig(out_path, bbox_inches="tight")
    finally:
        plt.close(fig)
    return out_path
