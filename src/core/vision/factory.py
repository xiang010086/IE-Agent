from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import VisionPipeline
from .heuristic import HeuristicEstimatePipeline

# view_type values that the Hands+YOLO pipeline is designed for.
_TOP_DOWN = "top_down"


def get_vision_pipeline(station: dict[str, Any], config: dict[str, Any]) -> VisionPipeline:
    """Pick the analyzer for a station, with honest fallback.

    Config drives the choice (deterministic, no auto-magic):
      - station.view_type == "top_down" + analysis.vision.enabled + deps/models
        present  ->  HandsYoloPipeline (real recognition)
      - otherwise -> HeuristicEstimatePipeline (estimate, clearly labelled)

    This is also the extension point for future PoseYoloPipeline /
    YoloTrackPipeline (front / far view types).
    """
    analysis = config.get("analysis", {}) or {}
    mtm_standard = analysis.get("mtm_standard", "MTM-1")
    vision_cfg = analysis.get("vision", {}) or {}
    sample_rate = int(analysis.get("sample_rate", vision_cfg.get("sample_rate", 5)) or 5)

    view_type = (station.get("view_type") or "").strip().lower()
    wants_vision = (
        bool(vision_cfg.get("enabled", False))
        and view_type == _TOP_DOWN
        and bool(station.get("video_file"))
    )

    if not wants_vision:
        return HeuristicEstimatePipeline(mtm_standard)

    reason = _vision_blocker(vision_cfg)
    if reason:
        return HeuristicEstimatePipeline(mtm_standard, fallback_reason=reason)

    from .hands_yolo import HandsYoloPipeline

    return HandsYoloPipeline(
        hand_model=vision_cfg["hand_model"],
        yolo_model=vision_cfg["yolo_model"],
        mtm_standard=mtm_standard,
        sample_rate=sample_rate,
        min_hand_confidence=float(vision_cfg.get("min_hand_confidence", 0.3)),
    )


def _vision_blocker(vision_cfg: dict[str, Any]) -> str | None:
    """Return a human reason if the vision pipeline cannot run, else None."""
    from .hands_yolo import dependencies_available

    ok, dep_reason = dependencies_available()
    if not ok:
        return dep_reason

    hand_model = vision_cfg.get("hand_model")
    yolo_model = vision_cfg.get("yolo_model")
    if not hand_model or not Path(hand_model).exists():
        return f"缺少手部模型文件: {hand_model}（请先运行 scripts/download_models.py）"
    if not yolo_model or not Path(yolo_model).exists():
        return f"缺少 YOLO 模型文件: {yolo_model}（请先运行 scripts/download_models.py）"
    return None
