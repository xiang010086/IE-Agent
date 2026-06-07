"""Built-in IE methodology knowledge base (phase 1) + signal-based selector.

The report layer detects analysis signals (bottleneck / high_wait / ...), selects
the relevant theory entries, and injects a compact text block into the DeepSeek
prompt so the narrative is grounded in real IE/production-economics theory rather
than free-styling.

Extension point for future RAG: ``select_entries`` accepts an injectable
``knowledge`` list — a future vector retriever can satisfy the same
``(signals) -> entries`` contract without changing callers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.storage import read_structured

# data/knowledge/ie_methodology.yaml relative to repo root (this file: src/core/knowledge/)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_KB_PATH = _REPO_ROOT / "data" / "knowledge" / "ie_methodology.yaml"

# Entries always included so the narrative has a baseline theoretical frame.
_BASELINE_IDS = ("mtm", "line_balancing")

# Efficiency below this (%) flags a likely operator/method problem (换人/培训).
_LOW_EFFICIENCY_PCT = 60.0
# Wait share of total cycle above this flags 等待浪费.
_HIGH_WAIT_RATIO = 0.15


def load_knowledge(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load the curated knowledge entries. Returns [] if the file is missing."""
    kb_path = Path(path) if path else _DEFAULT_KB_PATH
    data = read_structured(kb_path, [])
    if not isinstance(data, list):
        return []
    return [e for e in data if isinstance(e, dict) and e.get("id")]


def detect_signals(
    line_metrics: dict[str, Any] | None,
    takt_analysis: dict[str, Any] | None,
    stations: list[dict[str, Any]] | None,
) -> list[str]:
    """Map computed metrics to discrete analysis signals (deterministic)."""
    line_metrics = line_metrics or {}
    takt = takt_analysis or {}
    stations = stations or []
    signals: list[str] = ["baseline"]

    if line_metrics.get("bottleneck"):
        signals.append("bottleneck")

    lbr = line_metrics.get("lbr")
    lbr_target = line_metrics.get("lbr_target")
    if isinstance(lbr, (int, float)) and isinstance(lbr_target, (int, float)) and lbr < lbr_target:
        signals.append("lbr_below_target")

    # high wait: total wait as a share of summed cycle time
    cycle_sum = 0.0
    for s in stations:
        cyc = (s.get("cycle_time_metrics", {}) or {}).get("total_cycle_time")
        if isinstance(cyc, (int, float)):
            cycle_sum += cyc
    total_wait = line_metrics.get("total_wait_time")
    if isinstance(total_wait, (int, float)) and cycle_sum > 0 and total_wait / cycle_sum > _HIGH_WAIT_RATIO:
        signals.append("high_wait")

    # low efficiency: any non-error station below threshold
    for s in stations:
        if s.get("analysis_mode") == "error":
            continue
        eff = (s.get("cycle_time_metrics", {}) or {}).get("efficiency")
        if isinstance(eff, (int, float)) and 0 < eff < _LOW_EFFICIENCY_PCT:
            signals.append("low_efficiency")
            break

    # capacity shortage from takt analysis
    if not takt.get("skipped", True):
        gap = takt.get("worker_gap")
        if takt.get("capacity_status") == "bottleneck_over_takt" or (isinstance(gap, (int, float)) and gap > 0):
            signals.append("capacity_shortage")

    # de-dup, preserve order
    seen: set[str] = set()
    return [s for s in signals if not (s in seen or seen.add(s))]


def select_entries(
    signals: list[str],
    knowledge: list[dict[str, Any]] | None = None,
    max_entries: int = 5,
) -> list[dict[str, Any]]:
    """Pick relevant entries, guaranteeing every active signal gets representation.

    Order: (1) baseline entries; (2) one best entry per active signal, rarest
    signal first (so a specific signal like capacity_shortage still pulls in its
    theory, e.g. takt_theory, even under a small cap); (3) fill the rest by score.

    ``knowledge`` is injectable so a future RAG retriever can supply candidates.
    """
    entries = knowledge if knowledge is not None else load_knowledge()
    if not entries:
        return []
    by_id = {e["id"]: e for e in entries}
    active = [s for s in (signals or []) if s != "baseline"]
    signal_set = set(active) | {"baseline"}

    def score(entry: dict[str, Any]) -> int:
        return len(set(entry.get("applies_to", []) or []) & signal_set)

    def matches(sig: str) -> list[dict[str, Any]]:
        return [e for e in entries if sig in (e.get("applies_to", []) or [])]

    chosen: list[str] = []
    # 1) baseline
    for bid in _BASELINE_IDS:
        if bid in by_id and bid not in chosen:
            chosen.append(bid)
    # 2) coverage: rarest active signal first -> add its best (highest-score) entry
    for sig in sorted(active, key=lambda s: len(matches(s))):
        cands = sorted(matches(sig), key=score, reverse=True)
        for e in cands:
            if e["id"] not in chosen:
                chosen.append(e["id"])
                break
    # 3) fill the rest by score (then file order)
    rest = sorted(
        (i for i, e in enumerate(entries) if e["id"] not in chosen),
        key=lambda i: (-score(entries[i]), i),
    )
    for i in rest:
        chosen.append(entries[i]["id"])

    return [by_id[i] for i in chosen][:max_entries]


def build_knowledge_context(entries: list[dict[str, Any]]) -> str:
    """Compact text block injected into the prompt (name + key points + citation)."""
    if not entries:
        return ""
    blocks = []
    for e in entries:
        pts = "；".join(e.get("key_points_zh", []) or [])
        blocks.append(
            f"【{e.get('name_zh', e.get('id'))}】{e.get('summary_zh', '')}"
            + (f" 要点：{pts}。" if pts else "")
            + (f"（依据：{e.get('citation', '')}）" if e.get("citation") else "")
        )
    return "\n".join(blocks)
