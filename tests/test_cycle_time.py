"""Tests for the Takt / capacity / manpower module and the action verdicts.

Deterministic, no heavy deps. Proves: missing inputs -> skipped; full inputs ->
known Takt math; and that metrics map to the 加人/换人/拆分工序 decisions.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.cycle_time_calculator import (
    ACTION_ADD,
    ACTION_OK,
    ACTION_SPLIT,
    ACTION_SWAP,
    compute_takt,
    recommend_line_actions,
    takt_to_dict,
)


def _stations(*specs):
    """specs: (name, cycle, effective, efficiency) -> station-result dicts."""
    out = []
    for i, (name, cyc, eff, effi) in enumerate(specs, 1):
        out.append({
            "station_id": f"station_{i:02d}",
            "station_name": name,
            "analysis_mode": "heuristic_estimate",
            "cycle_time_metrics": {"total_cycle_time": cyc, "effective_time": eff,
                                   "wait_time": round(cyc - eff, 2), "efficiency": effi},
            "mtm_summary": {"total_tmus": int(eff / 0.036), "action_count": 8,
                            "standard_time": eff, "allowance_factor": 1.0},
        })
    return out


def test_skipped_when_missing():
    r = compute_takt({}, {"max_cycle_time": 50}, [])
    assert r.skipped is True
    assert "未提供" in (r.skip_reason or "")
    # missing just one required field still skips
    r2 = compute_takt({"shift_minutes": 480, "demand_per_shift": 420}, {}, [])
    assert r2.skipped is True
    print("skipped-on-missing OK")


def test_takt_math():
    info = {"shift_minutes": 480, "break_minutes": 60, "demand_per_shift": 420,
            "effective_rate": 1.0, "operator_count": 3}
    stations = _stations(("S1", 50, 45, 90.0), ("S2", 90, 80, 88.0))  # bottleneck 90
    line = {"max_cycle_time": 90, "bottleneck": {"station_id": "station_02",
            "station_name": "S2", "cycle_time": 90}, "lbr": 77.8, "lbr_target": 85}
    r = compute_takt(info, line, stations)
    assert r.skipped is False
    assert abs(r.available_time_s - 25200.0) < 0.5, r.available_time_s   # (480-60)*60*1.0
    assert abs(r.takt_time_s - 60.0) < 0.01, r.takt_time_s               # 25200/420
    assert r.capacity_status == "bottleneck_over_takt"                   # 90 > 60
    # required = ceil((45+80)/60) = ceil(2.083) = 3
    assert r.required_workers == 3, r.required_workers
    assert r.worker_gap == 0, r.worker_gap
    assert takt_to_dict(r)["takt_time_s"] == r.takt_time_s
    print("takt-math OK")


def test_effective_rate_percent_normalized():
    # rate given as percent (85) should normalize to 0.85
    info = {"shift_minutes": 600, "break_minutes": 0, "demand_per_shift": 100, "effective_rate": 85}
    r = compute_takt(info, {"max_cycle_time": 10}, _stations(("S1", 10, 9, 90.0)))
    assert r.skipped is False
    assert abs(r.available_time_s - 30600.0) < 1.0, r.available_time_s   # 600*60*0.85
    print("rate-normalize OK")


def test_break_zero_is_valid():
    info = {"shift_minutes": 480, "break_minutes": 0, "demand_per_shift": 480, "effective_rate": 1.0}
    r = compute_takt(info, {"max_cycle_time": 30}, _stations(("S1", 30, 28, 93.0)))
    assert r.skipped is False
    assert abs(r.takt_time_s - 60.0) < 0.01   # 480*60/480
    print("break-zero OK")


def test_actions_add_and_split():
    line = {"max_cycle_time": 90, "lbr": 70.0, "lbr_target": 85.0,
            "bottleneck": {"station_id": "station_02", "station_name": "S2", "cycle_time": 90}}
    takt = takt_to_dict(compute_takt(
        {"shift_minutes": 480, "break_minutes": 60, "demand_per_shift": 600,
         "effective_rate": 1.0, "operator_count": 2},
        line, _stations(("S1", 50, 45, 90.0), ("S2", 90, 80, 88.0))))
    acts = recommend_line_actions(line, takt, _stations(("S1", 50, 45, 90.0), ("S2", 90, 80, 88.0)))
    kinds = {a["action"] for a in acts}
    assert ACTION_SPLIT in kinds, kinds        # bottleneck cycle > takt -> split
    assert ACTION_ADD in kinds, kinds          # required > current -> add worker
    print("actions add+split OK")


def test_actions_swap_low_efficiency():
    # capacity fine (takt skipped), but one non-bottleneck station has low efficiency
    line = {"max_cycle_time": 60, "lbr": 95.0, "lbr_target": 85.0,
            "bottleneck": {"station_id": "station_01", "station_name": "S1", "cycle_time": 60}}
    stations = _stations(("S1", 60, 58, 96.0), ("S2", 58, 25, 43.0))  # S2 low efficiency
    acts = recommend_line_actions(line, {"skipped": True}, stations)
    assert any(a["action"] == ACTION_SWAP and "S2" in (a.get("target") or "") for a in acts), acts
    print("actions swap OK")


def test_actions_ok():
    line = {"max_cycle_time": 60, "lbr": 96.0, "lbr_target": 85.0,
            "bottleneck": {"station_id": "station_01", "station_name": "S1", "cycle_time": 60}}
    stations = _stations(("S1", 60, 58, 96.0), ("S2", 59, 57, 96.0))
    acts = recommend_line_actions(line, {"skipped": True}, stations)
    assert acts and acts[0]["action"] == ACTION_OK, acts
    print("actions ok OK")


def main() -> None:
    test_skipped_when_missing()
    test_takt_math()
    test_effective_rate_percent_normalized()
    test_break_zero_is_valid()
    test_actions_add_and_split()
    test_actions_swap_low_efficiency()
    test_actions_ok()
    print("节拍/决策测试通过")


if __name__ == "__main__":
    main()
