"""Tests for the built-in IE methodology knowledge base + signal selector."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.knowledge import (
    build_knowledge_context,
    detect_signals,
    load_knowledge,
    select_entries,
)


def test_load_knowledge():
    kb = load_knowledge()
    assert len(kb) >= 6, len(kb)
    for e in kb:
        for key in ("id", "name_zh", "name_en", "summary_zh", "applies_to", "citation"):
            assert key in e, (e.get("id"), key)
    ids = {e["id"] for e in kb}
    assert {"mtm", "line_balancing", "ecrs", "takt_theory"} <= ids, ids
    print("load_knowledge OK")


def test_detect_signals():
    line = {"bottleneck": {"station_name": "S2", "cycle_time": 90},
            "lbr": 70.0, "lbr_target": 85.0, "total_wait_time": 40.0}
    stations = [
        {"analysis_mode": "heuristic_estimate",
         "cycle_time_metrics": {"total_cycle_time": 60, "efficiency": 95.0}},
        {"analysis_mode": "heuristic_estimate",
         "cycle_time_metrics": {"total_cycle_time": 90, "efficiency": 45.0}},  # low eff
    ]
    takt = {"skipped": False, "capacity_status": "bottleneck_over_takt", "worker_gap": 2}
    sig = detect_signals(line, takt, stations)
    assert "bottleneck" in sig
    assert "lbr_below_target" in sig
    assert "low_efficiency" in sig
    assert "capacity_shortage" in sig
    print("detect_signals OK:", sig)


def test_select_and_context():
    kb = load_knowledge()
    entries = select_entries(["capacity_shortage", "bottleneck"], kb, max_entries=4)
    assert len(entries) <= 4
    ids = {e["id"] for e in entries}
    # baseline always present
    assert "mtm" in ids and "line_balancing" in ids, ids
    # capacity signal pulls in takt theory
    assert "takt_theory" in ids, ids
    ctx = build_knowledge_context(entries)
    assert isinstance(ctx, str) and len(ctx) > 20
    assert "MTM" in ctx or "Takt" in ctx
    # empty entries -> empty context
    assert build_knowledge_context([]) == ""
    print("select+context OK")


def main() -> None:
    test_load_knowledge()
    test_detect_signals()
    test_select_and_context()
    print("知识库测试通过")


if __name__ == "__main__":
    main()
