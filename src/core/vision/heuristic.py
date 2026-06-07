from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from .base import VisionPipeline


def _stable_ratio(seed_text: str, start: float, end: float) -> float:
    """Deterministic pseudo-value in [start, end] from a seed string.

    Used only by the heuristic estimate. It is intentionally deterministic so a
    given station always yields the same estimate, but note: the result depends
    on the station id, NOT on what happens in the video.
    """
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    number = int(digest[:8], 16) / 0xFFFFFFFF
    return start + (end - start) * number


class HeuristicEstimatePipeline(VisionPipeline):
    """Deterministic estimate from video duration / manual input only.

    IMPORTANT: this is NOT real action recognition. Cycle time comes from the
    real video duration (or a manual override), but action count, wait time and
    the action breakdown are estimated by formula. It is the honest fallback
    used when no vision pipeline is available for a station.

    Unlike the old MVP, it never fabricates a cycle time from file size: if the
    duration cannot be read and no manual cycle time is given, it returns an
    explicit error instead of inventing a number.
    """

    analysis_mode = "heuristic_estimate"

    def __init__(self, mtm_standard: str = "MTM-1", fallback_reason: str | None = None) -> None:
        super().__init__(mtm_standard)
        self.fallback_reason = fallback_reason

    def analyze(
        self,
        station: dict[str, Any],
        video_path: Path | None,
        tuning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        tuning = tuning or {}

        manual_cycle = station.get("cycle_time")
        duration = self.read_video_duration(video_path) if video_path else None

        if manual_cycle:
            total_cycle_time = max(1.0, float(manual_cycle))
            estimate_basis = "manual_cycle"
        elif duration:
            min_cycle = float(tuning.get("min_cycle_time", 5.0))
            max_cycle = float(tuning.get("max_cycle_time", 180.0))
            total_cycle_time = min(max_cycle, max(min_cycle, duration))
            estimate_basis = "video_duration"
        else:
            # No real signal. Be honest instead of fabricating from file size.
            if station.get("video_file"):
                return self.error_result(
                    station,
                    "无法读取视频时长(文件损坏或 OpenCV 不可用)；请在工位参数里手填节拍。",
                )
            return self.error_result(
                station,
                "该工位既无视频也无手填节拍；请提供其一。",
            )

        wait_time = self._resolve_wait_time(station, total_cycle_time, tuning)
        effective_time = max(0.1, total_cycle_time - wait_time)

        action_seconds_min = float(tuning.get("action_seconds_min", 2.5))
        action_seconds_max = float(tuning.get("action_seconds_max", 5.0))
        action_count = max(
            4,
            int(total_cycle_time / _stable_ratio(station["id"], action_seconds_min, action_seconds_max)),
        )

        extra = {
            "estimate_basis": estimate_basis,
            "estimate_warning": "动作数/动作分解为按时长估算的合成值，非视频识别结果。",
        }
        if self.fallback_reason:
            extra["fallback_reason"] = self.fallback_reason

        return self.assemble_result(
            station,
            total_cycle_time=total_cycle_time,
            wait_time=wait_time,
            action_count=action_count,
            action_breakdown=self._build_action_breakdown(effective_time, wait_time),
            runtime_seconds=time.perf_counter() - started,
            extra=extra,
        )

    def _resolve_wait_time(
        self,
        station: dict[str, Any],
        cycle_time: float,
        tuning: dict[str, Any],
    ) -> float:
        if "manual_wait_time" in station:
            return min(cycle_time * 0.6, max(0.0, float(station["manual_wait_time"])))
        wait_ratio_min = float(tuning.get("wait_ratio_min", 0.06))
        wait_ratio_max = float(tuning.get("wait_ratio_max", 0.22))
        wait_ratio = _stable_ratio(station["id"] + station["name"], wait_ratio_min, wait_ratio_max)
        return round(cycle_time * wait_ratio, 2)

    def _build_action_breakdown(self, effective_time: float, wait_time: float) -> dict[str, float]:
        reach = effective_time * 0.22
        grasp = effective_time * 0.14
        move = effective_time * 0.31
        release = effective_time * 0.13
        inspect = effective_time - reach - grasp - move - release
        return {
            "R_伸手": reach,
            "G_抓取": grasp,
            "M_移动": move,
            "RL_放手": release,
            "I_检查": inspect,
            "Wait_等待": wait_time,
        }
