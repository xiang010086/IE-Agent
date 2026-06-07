from __future__ import annotations

import abc
from datetime import datetime
from pathlib import Path
from typing import Any

# 1 TMU (Time Measurement Unit) = 0.036 seconds (MTM-1 standard).
SECONDS_PER_TMU = 0.036


class VisionPipeline(abc.ABC):
    """A single-station analyzer.

    Every concrete pipeline turns one video into the SAME station-result dict,
    so the downstream line metrics / report / validation / UI never change.
    """

    #: Value written to result["analysis_mode"]. Tells the UI whether numbers
    #: are real recognition or a deterministic estimate.
    analysis_mode: str = "unknown"

    def __init__(self, mtm_standard: str = "MTM-1") -> None:
        self.mtm_standard = mtm_standard

    @abc.abstractmethod
    def analyze(
        self,
        station: dict[str, Any],
        video_path: Path | None,
        tuning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return the station-result dict (schema below)."""

    # -- shared helpers -------------------------------------------------

    def read_video_duration(self, video_path: Path | None) -> float | None:
        """Read real duration via OpenCV. Returns None if it cannot be read.

        Unlike the old MVP, this never fabricates a duration from file size.
        """
        if video_path is None or not Path(video_path).exists():
            return None
        try:
            import cv2  # type: ignore
        except Exception:
            return None
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            return None
        fps = capture.get(cv2.CAP_PROP_FPS) or 0
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        capture.release()
        if fps <= 0 or frame_count <= 0:
            return None
        return frame_count / fps

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
        allowance_factor: float = 1.0,
    ) -> dict[str, Any]:
        """Build the canonical station-result dict shared by all pipelines.

        ``standard_time`` = effective_time x allowance_factor (宽放). Pipelines
        do not know the project-level allowance, so the default factor is 1.0
        (standard_time == effective_time); the Takt module re-applies the real
        project allowance when comparing against takt time.
        """
        effective_time = max(0.1, total_cycle_time - wait_time)
        efficiency = effective_time / total_cycle_time * 100 if total_cycle_time else 0.0
        total_tmus = int(effective_time / SECONDS_PER_TMU)
        standard_time = round(effective_time * float(allowance_factor), 2)
        result: dict[str, Any] = {
            "station_id": station["id"],
            "station_name": station["name"],
            "video_file": station.get("video_file"),
            "analysis_time": datetime.now().isoformat(timespec="seconds"),
            "cycle_time_metrics": {
                "total_cycle_time": round(total_cycle_time, 2),
                "effective_time": round(effective_time, 2),
                "wait_time": round(wait_time, 2),
                "efficiency": round(efficiency, 1),
            },
            "mtm_summary": {
                "total_tmus": total_tmus,
                "action_count": int(action_count),
                "mtm_standard": self.mtm_standard,
                "standard_time": standard_time,
                "allowance_factor": round(float(allowance_factor), 3),
            },
            "action_breakdown": {k: round(v, 2) for k, v in action_breakdown.items()},
            "runtime_seconds": round(runtime_seconds, 3),
            "analysis_mode": self.analysis_mode,
            "action_timeline": action_timeline or [],
        }
        if extra:
            result.update(extra)
        return result

    @staticmethod
    def error_result(
        station: dict[str, Any],
        message: str,
    ) -> dict[str, Any]:
        """Honest failure result instead of fabricated numbers."""
        return {
            "station_id": station["id"],
            "station_name": station["name"],
            "video_file": station.get("video_file"),
            "analysis_time": datetime.now().isoformat(timespec="seconds"),
            "cycle_time_metrics": {
                "total_cycle_time": 0.0,
                "effective_time": 0.0,
                "wait_time": 0.0,
                "efficiency": 0.0,
            },
            "mtm_summary": {
                "total_tmus": 0,
                "action_count": 0,
                "mtm_standard": "N/A",
                "standard_time": 0.0,
                "allowance_factor": 1.0,
            },
            "action_breakdown": {},
            "runtime_seconds": 0.0,
            "analysis_mode": "error",
            "error": message,
        }
