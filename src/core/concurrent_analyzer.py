from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

from .cycle_time_calculator import compute_takt, recommend_line_actions, takt_to_dict
from .project_manager import ProjectManager
from .storage import write_json
from .vision import get_vision_pipeline
from .vision.heuristic import HeuristicEstimatePipeline

# Backwards-compatible alias: the old MVP exposed SingleVideoAnalyzer here.
# Its hash-based estimate now lives in the honestly named heuristic pipeline.
SingleVideoAnalyzer = HeuristicEstimatePipeline


class ProductionLineCalculator:
    @staticmethod
    def calculate(results: list[dict[str, Any]], lbr_target: float = 85.0) -> dict[str, Any]:
        if not results:
            return {
                "station_count": 0,
                "lbr": 0.0,
                "lbr_target": lbr_target,
                "bottleneck": None,
                "total_wait_time": 0.0,
                "max_cycle_time": 0.0,
                "estimated_hourly_capacity": 0.0,
            }

        cycle_times = [r["cycle_time_metrics"]["total_cycle_time"] for r in results]
        wait_times = [r["cycle_time_metrics"]["wait_time"] for r in results]
        max_cycle_time = max(cycle_times)
        station_count = len(results)
        lbr = sum(cycle_times) / (max_cycle_time * station_count) * 100 if max_cycle_time else 0.0
        bottleneck = max(results, key=lambda r: r["cycle_time_metrics"]["total_cycle_time"])
        hourly_capacity = 3600 / max_cycle_time if max_cycle_time else 0.0

        return {
            "station_count": station_count,
            "lbr": round(lbr, 1),
            "lbr_target": float(lbr_target),
            "lbr_gap": round(float(lbr_target) - lbr, 1),
            "bottleneck": {
                "station_id": bottleneck["station_id"],
                "station_name": bottleneck["station_name"],
                "cycle_time": bottleneck["cycle_time_metrics"]["total_cycle_time"],
                "wait_time": bottleneck["cycle_time_metrics"]["wait_time"],
            },
            "total_wait_time": round(sum(wait_times), 2),
            "max_cycle_time": round(max_cycle_time, 2),
            "average_cycle_time": round(sum(cycle_times) / station_count, 2),
            "estimated_hourly_capacity": round(hourly_capacity, 1),
        }


class ConcurrentAnalyzer:
    """Analyze all stations in a project.

    Each station gets a pipeline from ``get_vision_pipeline`` (real Hands+YOLO
    for top-down stations, heuristic estimate otherwise). Light heuristic
    stations run concurrently; heavy vision stations run serially because
    MediaPipe/torch are not thread-safe and are CPU intensive.
    """

    def __init__(self, project_manager: ProjectManager | None = None) -> None:
        self.project_manager = project_manager or ProjectManager()

    def analyze_project(self, project_id: str) -> dict[str, Any]:
        config = self.project_manager.load_config(project_id)
        paths = self.project_manager.get_paths(project_id)
        stations = config.get("stations", [])
        analysis_config = config.get("analysis", {})
        concurrency = int(analysis_config.get("concurrency", 2))
        tuning = analysis_config.get("tuning", {})
        lbr_target = float(config.get("target", {}).get("lbr_target", 85.0))

        jobs = []
        for station in stations:
            pipeline = get_vision_pipeline(station, config)
            video_path = (
                paths.videos / station["video_file"] if station.get("video_file") else None
            )
            jobs.append((station, pipeline, video_path))

        vision_jobs = [j for j in jobs if j[1].analysis_mode == "vision_handsyolo"]
        light_jobs = [j for j in jobs if j[1].analysis_mode != "vision_handsyolo"]

        results: list[dict[str, Any]] = []

        def _record(result: dict[str, Any]) -> None:
            write_json(paths.results / f"{result['station_id']}.json", result)
            results.append(result)

        # Light heuristic stations: concurrent.
        if light_jobs:
            with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
                future_map = {
                    executor.submit(pipeline.analyze, station, video_path, tuning): station
                    for (station, pipeline, video_path) in light_jobs
                }
                for future in as_completed(future_map):
                    _record(future.result())

        # Heavy vision stations: serial.
        for station, pipeline, video_path in vision_jobs:
            _record(pipeline.analyze(station, video_path, tuning))

        results.sort(key=lambda item: item["station_id"])
        # Degenerate (error) stations are kept for display but excluded from
        # line metrics so they do not distort LBR / bottleneck.
        valid_results = [r for r in results if r.get("analysis_mode") != "error"]
        line_metrics = ProductionLineCalculator.calculate(valid_results, lbr_target=lbr_target)
        takt_analysis = takt_to_dict(
            compute_takt(config.get("project_info"), line_metrics, valid_results)
        )
        action_recommendations = recommend_line_actions(
            line_metrics, takt_analysis, valid_results
        )
        summary = {
            "project": config["project"],
            "project_info": config.get("project_info", {}),
            "target": config.get("target", {}),
            "line_metrics": line_metrics,
            "takt_analysis": takt_analysis,
            "action_recommendations": action_recommendations,
            "stations": results,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.project_manager.update_summary(project_id, summary)
        return summary
