from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .storage import read_json, read_structured, write_json, write_structured


VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    config: Path
    videos: Path
    results: Path
    exports: Path
    summary: Path


class ProjectManager:
    """File-system project manager for the MVP.

    One project is one folder. Each project contains config, videos, results, and
    exports, matching the architecture in the V4.0 proposal.
    """

    #: Optional project-info fields (socio-economic / production-economics inputs).
    #: All numeric fields default to None ("未提供") so the Takt module can skip
    #: cleanly. Stored under config["project_info"], separate from the identity
    #: block config["project"] (id/name/status never disturbed).
    DEFAULT_PROJECT_INFO: dict[str, Any] = {
        "industry": "",            # 行业
        "product": "",             # 产品
        "line_name": "",           # 产线/工序
        "analyst": "",             # 分析人员
        "report_date": "",         # 报告日期
        "shift_minutes": None,     # 班次时长(分钟)
        "break_minutes": None,     # 休息/停线(分钟)
        "demand_per_shift": None,  # 班次需求量(件)
        "effective_rate": None,    # 有效作业率 0-1
        "allowance_factor": None,  # 宽放系数, 如 1.13
        "operator_count": None,    # 现有工人数
        "labor_cost_per_hour": None,  # 人工成本(元/小时), 经济分析用, 可空
    }

    def __init__(self, data_root: str | Path = "data/projects") -> None:
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)

    def create_project(
        self,
        name: str,
        client: str = "",
        lbr_target: float = 85.0,
        cycle_time_target: float | None = None,
        concurrency: int = 2,
    ) -> dict[str, Any]:
        project_id = datetime.now().strftime("proj_%Y%m%d_%H%M%S")
        paths = self.get_paths(project_id)
        for folder in (paths.root, paths.videos, paths.results, paths.exports):
            folder.mkdir(parents=True, exist_ok=True)

        config = {
            "project": {
                "id": project_id,
                "name": name.strip() or "未命名项目",
                "client": client.strip(),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "active",
            },
            "target": {
                "lbr_target": float(lbr_target),
                "cycle_time_target": cycle_time_target,
            },
            "stations": [],
            "analysis": {
                "concurrency": max(1, int(concurrency)),
                "sample_rate": 5,  # 视觉抽帧步长：每隔 N 帧跑一次推理
                "mtm_standard": "MTM-1",
                "vision": {
                    "enabled": True,
                    "hand_model": "data/models/hand_landmarker.task",
                    "yolo_model": "data/models/yolov8n.pt",
                    "min_action_frames": 4,
                },
                "tuning": {
                    "min_cycle_time": 5.0,
                    "max_cycle_time": 180.0,
                    "wait_ratio_min": 0.06,
                    "wait_ratio_max": 0.22,
                    "action_seconds_min": 2.5,
                    "action_seconds_max": 5.0,
                },
            },
        }
        write_structured(paths.config, config)
        write_json(paths.summary, {"project_id": project_id, "status": "created"})
        return config

    def list_projects(self) -> list[dict[str, Any]]:
        projects: list[dict[str, Any]] = []
        for project_dir in sorted(self.data_root.glob("proj_*"), reverse=True):
            config_path = project_dir / "config.yaml"
            if not config_path.exists():
                continue
            try:
                config = read_structured(config_path, {})
                projects.append(config)
            except Exception:
                continue
        return projects

    def get_paths(self, project_id: str) -> ProjectPaths:
        root = self.data_root / project_id
        return ProjectPaths(
            root=root,
            config=root / "config.yaml",
            videos=root / "videos",
            results=root / "results",
            exports=root / "exports",
            summary=root / "project_summary.json",
        )

    def load_config(self, project_id: str) -> dict[str, Any]:
        paths = self.get_paths(project_id)
        config = read_structured(paths.config)
        if not isinstance(config, dict):
            raise ValueError(f"Invalid config for project {project_id}")
        return config

    def save_config(self, project_id: str, config: dict[str, Any]) -> None:
        write_structured(self.get_paths(project_id).config, config)

    def load_project_info(self, project_id: str) -> dict[str, Any]:
        """Return the project-info block merged over defaults (always complete)."""
        config = self.load_config(project_id)
        return {**self.DEFAULT_PROJECT_INFO, **(config.get("project_info") or {})}

    def save_project_info(self, project_id: str, info: dict[str, Any]) -> None:
        """Merge and persist project-info into config["project_info"]."""
        config = self.load_config(project_id)
        merged = {
            **self.DEFAULT_PROJECT_INFO,
            **(config.get("project_info") or {}),
            **(info or {}),
        }
        config["project_info"] = merged
        self.save_config(project_id, config)

    def import_video(
        self,
        project_id: str,
        source_path: str | Path,
        station_name: str | None = None,
        cycle_time: float | None = None,
    ) -> dict[str, Any]:
        source = Path(source_path)
        if source.suffix.lower() not in VIDEO_EXTENSIONS:
            raise ValueError(f"Unsupported video format: {source.suffix}")
        if not source.exists():
            raise FileNotFoundError(source)

        config = self.load_config(project_id)
        stations = config.setdefault("stations", [])
        station_id = f"station_{len(stations) + 1:02d}"
        target_name = f"{station_id}{source.suffix.lower()}"
        paths = self.get_paths(project_id)
        paths.videos.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, paths.videos / target_name)

        station = {
            "id": station_id,
            "name": station_name or f"工位{len(stations) + 1}",
            "video_file": target_name,
            "cycle_time": cycle_time,
            # 默认按俯视工位处理 → 走 Hands+YOLO 真实识别；可在界面改。
            "view_type": "top_down",
            "status": "pending",
        }
        stations.append(station)
        self.save_config(project_id, config)
        return station

    def add_manual_station(
        self,
        project_id: str,
        station_name: str,
        cycle_time: float,
        wait_time: float = 0.0,
    ) -> dict[str, Any]:
        """Add a station without a video, useful for early IE estimates."""
        config = self.load_config(project_id)
        stations = config.setdefault("stations", [])
        station_id = f"station_{len(stations) + 1:02d}"
        station = {
            "id": station_id,
            "name": station_name,
            "video_file": None,
            "cycle_time": float(cycle_time),
            "manual_wait_time": max(0.0, float(wait_time)),
            "status": "pending",
        }
        stations.append(station)
        self.save_config(project_id, config)
        return station

    def load_station_results(self, project_id: str) -> list[dict[str, Any]]:
        paths = self.get_paths(project_id)
        results = []
        for result_file in sorted(paths.results.glob("station_*.json")):
            result = read_json(result_file, {})
            if result:
                results.append(result)
        return results

    def update_summary(self, project_id: str, summary: dict[str, Any]) -> None:
        write_json(self.get_paths(project_id).summary, summary)

    def load_summary(self, project_id: str) -> dict[str, Any]:
        return read_json(self.get_paths(project_id).summary, {})
