"""Takt-time / capacity / manpower analysis (production economics).

Deterministic, None-safe pure functions. Given the project-info inputs (shift
length, break, demand, effective rate, allowance) plus the already-computed
line metrics and per-station results, derive demand-driven takt time, capacity
status, and required manpower.

The doc's task-3 was single-process; here it is adapted to a MULTI-STATION line:
- the binding cycle for capacity is the line bottleneck (max station cycle),
- required workers aggregate standard time across all stations.

If any required input is missing the result is ``skipped`` with a reason, so the
report/UI can honestly print "未提供必要参数，跳过节拍分析".
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import ceil
from typing import Any

# Inputs that MUST be present (and positive) to run takt analysis.
# break_minutes is intentionally NOT here: a line with no break (break=0) is valid;
# compute_takt defaults it to 0.
REQUIRED_FIELDS = ("shift_minutes", "demand_per_shift", "effective_rate")


@dataclass
class TaktResult:
    available_time_s: float | None = None       # (shift - break) * 60 * effective_rate
    takt_time_s: float | None = None            # available_time / demand
    bottleneck_cycle_s: float | None = None     # from line_metrics.max_cycle_time
    capacity_status: str = "unknown"            # ok | bottleneck_over_takt | unknown
    capacity_gap_s: float | None = None         # bottleneck_cycle - takt (signed)
    total_standard_time_s: float | None = None  # sum of per-station standard time (allowance applied)
    required_workers: int | None = None         # ceil(total_standard_time / takt)
    current_workers: int | None = None
    worker_gap: int | None = None               # required - current
    theoretical_capacity_per_shift: float | None = None  # available_time / bottleneck_cycle
    allowance_factor: float = 1.0
    skipped: bool = True
    skip_reason: str | None = None
    inputs_used: dict[str, Any] = field(default_factory=dict)


def _num(value: Any) -> float | None:
    """Coerce to a positive float, else None (treats 0/blank/garbage as missing)."""
    try:
        if value is None:
            return None
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None


def _normalize_rate(value: float | None) -> float | None:
    """Effective rate as a 0-1 fraction. Accept percent (e.g. 85) and normalize."""
    if value is None:
        return None
    return value / 100.0 if value > 1.0 else value


def _missing_fields(project_info: dict[str, Any]) -> list[str]:
    missing = []
    for key in REQUIRED_FIELDS:
        val = _num(project_info.get(key))
        if key == "effective_rate":
            val = _normalize_rate(val)
        if val is None:
            missing.append(key)
    return missing


def _station_standard_time(station: dict[str, Any]) -> float:
    """Per-station base standard time (pre project-allowance).

    Prefer mtm_summary.standard_time (== effective_time at factor 1.0); fall back
    to cycle_time_metrics.effective_time. Skip error stations (0).
    """
    mtm = station.get("mtm_summary", {}) or {}
    st = _num(mtm.get("standard_time"))
    if st is not None:
        return st
    eff = _num((station.get("cycle_time_metrics", {}) or {}).get("effective_time"))
    return eff or 0.0


def compute_takt(
    project_info: dict[str, Any] | None,
    line_metrics: dict[str, Any] | None,
    stations: list[dict[str, Any]] | None,
) -> TaktResult:
    """Compute takt / capacity / manpower. Returns a skipped result if inputs missing."""
    project_info = project_info or {}
    line_metrics = line_metrics or {}
    stations = stations or []

    missing = _missing_fields(project_info)
    if missing:
        return TaktResult(
            skipped=True,
            skip_reason="未提供必要参数（班次时长/休息/需求/有效作业率），跳过节拍分析。",
            inputs_used={"missing": missing},
        )

    shift = _num(project_info.get("shift_minutes"))
    brk = float(project_info.get("break_minutes") or 0.0)  # break may legitimately be 0
    demand = _num(project_info.get("demand_per_shift"))
    rate = _normalize_rate(_num(project_info.get("effective_rate")))
    allowance = _num(project_info.get("allowance_factor")) or 1.0

    net_minutes = max(0.0, shift - brk)
    available_time_s = net_minutes * 60.0 * rate
    if available_time_s <= 0 or demand <= 0:
        return TaktResult(
            skipped=True,
            skip_reason="班次净工时或需求量无效，无法计算节拍。",
            inputs_used={"shift_minutes": shift, "break_minutes": brk,
                         "effective_rate": rate, "demand_per_shift": demand},
        )

    takt_time_s = available_time_s / demand

    bottleneck_cycle_s = _num(line_metrics.get("max_cycle_time"))
    capacity_status = "unknown"
    capacity_gap_s = None
    theoretical_capacity = None
    if bottleneck_cycle_s is not None:
        capacity_status = "bottleneck_over_takt" if bottleneck_cycle_s > takt_time_s else "ok"
        capacity_gap_s = round(bottleneck_cycle_s - takt_time_s, 2)
        theoretical_capacity = round(available_time_s / bottleneck_cycle_s, 1)

    total_standard = round(sum(_station_standard_time(s) for s in stations) * allowance, 2)
    required_workers = ceil(total_standard / takt_time_s) if total_standard > 0 else None

    current_workers_raw = _num(project_info.get("operator_count"))
    current_workers = int(current_workers_raw) if current_workers_raw is not None else None
    worker_gap = (
        required_workers - current_workers
        if (required_workers is not None and current_workers is not None)
        else None
    )

    return TaktResult(
        available_time_s=round(available_time_s, 1),
        takt_time_s=round(takt_time_s, 2),
        bottleneck_cycle_s=round(bottleneck_cycle_s, 2) if bottleneck_cycle_s is not None else None,
        capacity_status=capacity_status,
        capacity_gap_s=capacity_gap_s,
        total_standard_time_s=total_standard,
        required_workers=required_workers,
        current_workers=current_workers,
        worker_gap=worker_gap,
        theoretical_capacity_per_shift=theoretical_capacity,
        allowance_factor=round(allowance, 3),
        skipped=False,
        skip_reason=None,
        inputs_used={
            "shift_minutes": shift,
            "break_minutes": brk,
            "demand_per_shift": demand,
            "effective_rate": rate,
            "allowance_factor": allowance,
        },
    )


def takt_to_dict(result: TaktResult) -> dict[str, Any]:
    """JSON-serializable dict for the summary / report."""
    return asdict(result)


# ---------------------------------------------------------------------------
# Action verdicts — the whole point: tell the factory 加人 / 换人 / 拆分工序.
# Deterministic decisions derived from real numbers; DeepSeek only explains why.
# ---------------------------------------------------------------------------

ACTION_ADD = "add_worker"     # 加人：产能不足，需增加人手 / 并行
ACTION_SWAP = "swap_worker"   # 换人/调岗：工位效率低(人/方法问题)，或人力冗余需调岗
ACTION_SPLIT = "split_task"   # 拆分工序：瓶颈节拍过长 / 产线不平衡，拆分或重排
ACTION_OK = "ok"              # 暂无明显问题

LOW_EFFICIENCY_PCT = 60.0     # 工位效率低于此 → 疑似人/方法问题（换人/培训）


def recommend_line_actions(
    line_metrics: dict[str, Any] | None,
    takt_analysis: dict[str, Any] | None,
    stations: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Turn metrics into concrete 加人/换人/拆分工序 verdicts (numbers in the reason).

    Each item: {action, target, severity, reason}. Returns an ``ok`` item if no
    issue is found. Headline = the first (highest-severity) item.
    """
    line_metrics = line_metrics or {}
    takt = takt_analysis or {}
    stations = stations or []
    actions: list[dict[str, Any]] = []

    bottleneck = line_metrics.get("bottleneck") or {}
    bn_name = bottleneck.get("station_name") or "瓶颈工位"
    bn_cycle = bottleneck.get("cycle_time")
    lbr = line_metrics.get("lbr")
    lbr_target = line_metrics.get("lbr_target")

    takt_ok = not takt.get("skipped", True)
    takt_time = takt.get("takt_time_s")
    worker_gap = takt.get("worker_gap")
    required = takt.get("required_workers")
    current = takt.get("current_workers")

    # 1) Capacity shortage → 加人 and/or 拆分瓶颈
    if takt_ok and takt.get("capacity_status") == "bottleneck_over_takt" and bn_cycle and takt_time:
        actions.append({
            "action": ACTION_SPLIT,
            "target": bn_name,
            "severity": "high",
            "reason": f"瓶颈工位「{bn_name}」节拍 {bn_cycle}s 超过客户节拍 Takt {takt_time}s，"
                      f"单工位无法满足需求，应拆分/重排其工序或并行作业。",
        })
    if takt_ok and isinstance(worker_gap, (int, float)) and worker_gap > 0:
        actions.append({
            "action": ACTION_ADD,
            "target": "产线",
            "severity": "high",
            "reason": f"按 Takt 需求人数 {required} 人 > 现有 {current} 人，缺口 {worker_gap} 人，"
                      f"产能不足，需增加 {worker_gap} 名工人（或对瓶颈并行）。",
        })
    elif takt_ok and isinstance(worker_gap, (int, float)) and worker_gap < 0:
        actions.append({
            "action": ACTION_SWAP,
            "target": "产线",
            "severity": "medium",
            "reason": f"按 Takt 需求人数 {required} 人 < 现有 {current} 人，富余 {abs(worker_gap)} 人，"
                      f"建议调岗/减人或承接更多工序，降低人工成本。",
        })

    # 2) Line imbalance → 拆分/重排（若上面没因产能已建议拆分）
    if (
        isinstance(lbr, (int, float)) and isinstance(lbr_target, (int, float))
        and lbr < lbr_target
        and not any(a["action"] == ACTION_SPLIT for a in actions)
    ):
        actions.append({
            "action": ACTION_SPLIT,
            "target": bn_name,
            "severity": "medium",
            "reason": f"产线平衡率 LBR {lbr}% 低于目标 {lbr_target}%，各工位忙闲不均，"
                      f"应把瓶颈「{bn_name}」的部分工序拆分/重排到负荷较轻的工位。",
        })

    # 3) Per-station low efficiency (not the bottleneck) → 换人/培训
    bn_id = bottleneck.get("station_id")
    for s in stations:
        if s.get("analysis_mode") == "error" or s.get("station_id") == bn_id:
            continue
        eff = (s.get("cycle_time_metrics", {}) or {}).get("efficiency")
        if isinstance(eff, (int, float)) and 0 < eff < LOW_EFFICIENCY_PCT:
            actions.append({
                "action": ACTION_SWAP,
                "target": s.get("station_name"),
                "severity": "medium",
                "reason": f"工位「{s.get('station_name')}」有效作业效率仅 {eff}%（等待/无效动作偏高），"
                          f"疑似操作熟练度或方法问题，建议换人/再培训或优化作业方法。",
            })

    if not actions:
        actions.append({
            "action": ACTION_OK,
            "target": "产线",
            "severity": "low",
            "reason": "当前产能、平衡率与各工位效率未见明显问题，维持现状并持续改善。",
        })

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda a: severity_rank.get(a.get("severity"), 9))
    return actions

