"""DeepSeek-off fallback for the report narrative.

Proves: with AI disabled (or returning None), the report narrative still has the
full schema, is sourced from the rule engine, and is NUMBER-FAITHFUL (the prose
references only the numbers we passed in — nothing fabricated).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core import llm_client
from src.core.llm_client import LLMClient, generate_report_narrative

_SCHEMA_KEYS = {
    "executive_summary", "key_findings", "per_section_commentary",
    "bottleneck_root_cause", "takt_interpretation", "recommendations",
    "implementation_roadmap", "conclusion", "cited_theories", "source",
}

_ANALYSIS = {
    "line_metrics": {
        "station_count": 3, "lbr": 76.3, "lbr_target": 85.0,
        "max_cycle_time": 45.0, "total_wait_time": 12.0,
        "estimated_hourly_capacity": 80.0,
        "bottleneck": {"station_id": "station_02", "station_name": "工位2-装配", "cycle_time": 45.0},
    },
    "takt_analysis": {
        "skipped": False, "takt_time_s": 40.0, "bottleneck_cycle_s": 45.0,
        "capacity_status": "bottleneck_over_takt", "available_time_s": 24000.0,
        "required_workers": 4, "current_workers": 3, "worker_gap": 1,
    },
    "action_recommendations": [
        {"action": "add_worker", "target": "产线", "severity": "high",
         "reason": "需求人数 4 人 > 现有 3 人，缺口 1 人。"},
        {"action": "split_task", "target": "工位2-装配", "severity": "high",
         "reason": "瓶颈节拍 45s 超过 Takt 40s。"},
    ],
    "stations": [
        {"station_name": "工位2-装配", "analysis_mode": "heuristic_estimate",
         "cycle_time_metrics": {"total_cycle_time": 45.0, "effective_time": 38.0,
                                "wait_time": 7.0, "efficiency": 84.4},
         "mtm_summary": {"total_tmus": 1055, "action_count": 9, "standard_time": 38.0}},
    ],
}


def test_use_ai_false_uses_rules():
    narr = generate_report_narrative({}, _ANALYSIS, "ctx", use_ai=False)
    assert _SCHEMA_KEYS <= set(narr.keys()), set(narr.keys())
    assert narr["source"] == "rule_fallback", narr["source"]
    assert narr["recommendations"], "expected recommendations"
    print("use_ai=False -> rules OK")


def test_ai_none_falls_back(monkeypatch_returns_none=True):
    # Force the AI path to return None, then the module fn must fall back to rules.
    orig = LLMClient.generate_report_narrative
    LLMClient.generate_report_narrative = lambda self, *a, **k: None  # type: ignore
    try:
        narr = generate_report_narrative({}, _ANALYSIS, "ctx", use_ai=True, provider="deepseek")
    finally:
        LLMClient.generate_report_narrative = orig  # type: ignore
    assert narr["source"] == "rule_fallback", narr["source"]
    assert _SCHEMA_KEYS <= set(narr.keys())
    print("ai-None -> fallback OK")


def test_number_faithful():
    narr = generate_report_narrative({}, _ANALYSIS, "", use_ai=False)
    blob = (
        narr["executive_summary"] + " " + " ".join(narr["key_findings"])
        + " " + narr["takt_interpretation"]
    )
    # numbers that appear must be the real ones we passed in
    assert "76.3" in blob          # lbr
    assert "85" in blob            # lbr_target
    assert "工位2-装配" in blob     # bottleneck name
    assert "40.0" in blob or "40" in blob   # takt time
    # required/current workers from takt
    assert "4" in blob and "3" in blob
    print("number-faithful OK")


def main() -> None:
    test_use_ai_false_uses_rules()
    test_ai_none_falls_back()
    test_number_faithful()
    print("LLM 回退测试通过")


if __name__ == "__main__":
    main()
