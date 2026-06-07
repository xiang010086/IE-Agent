from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .project_manager import ProjectManager
from .storage import write_json


@dataclass(frozen=True)
class ValidationThresholds:
    action_count_tolerance: int = 2
    cycle_time_tolerance_pct: float = 10.0
    wait_time_tolerance_pct: float = 20.0


GROUND_TRUTH_COLUMNS = [
    "station_id",
    "station_name",
    "video_file",
    "predicted_cycle_time",
    "ground_truth_cycle_time",
    "predicted_wait_time",
    "ground_truth_wait_time",
    "predicted_action_count",
    "ground_truth_action_count",
    "labeler",
    "notes",
]


class AccuracyValidator:
    """Create ground-truth templates and compare labels against analyzer output."""

    def __init__(self, project_manager: ProjectManager | None = None) -> None:
        self.project_manager = project_manager or ProjectManager()

    def create_ground_truth_template(self, project_id: str) -> Path:
        paths = self.project_manager.get_paths(project_id)
        results = self.project_manager.load_station_results(project_id)
        if not results:
            summary = self.project_manager.load_summary(project_id)
            results = summary.get("stations", [])

        template_path = paths.exports / "ground_truth_template.csv"
        template_path.parent.mkdir(parents=True, exist_ok=True)

        with template_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=GROUND_TRUTH_COLUMNS)
            writer.writeheader()
            for result in sorted(results, key=lambda item: item.get("station_id", "")):
                metrics = result.get("cycle_time_metrics", {})
                mtm = result.get("mtm_summary", {})
                writer.writerow(
                    {
                        "station_id": result.get("station_id", ""),
                        "station_name": result.get("station_name", ""),
                        "video_file": result.get("video_file", ""),
                        "predicted_cycle_time": metrics.get("total_cycle_time", ""),
                        "ground_truth_cycle_time": "",
                        "predicted_wait_time": metrics.get("wait_time", ""),
                        "ground_truth_wait_time": "",
                        "predicted_action_count": mtm.get("action_count", ""),
                        "ground_truth_action_count": "",
                        "labeler": "",
                        "notes": "",
                    }
                )
        return template_path

    def validate(
        self,
        project_id: str,
        ground_truth_csv: str | Path,
        thresholds: ValidationThresholds | None = None,
    ) -> dict[str, Any]:
        thresholds = thresholds or ValidationThresholds()
        paths = self.project_manager.get_paths(project_id)
        predicted = {
            result["station_id"]: result
            for result in self.project_manager.load_station_results(project_id)
        }
        if not predicted:
            predicted = {
                result["station_id"]: result
                for result in self.project_manager.load_summary(project_id).get("stations", [])
            }

        rows = self._read_ground_truth(ground_truth_csv)
        station_reports = []
        for row in rows:
            station_id = row.get("station_id", "").strip()
            if not station_id:
                continue
            result = predicted.get(station_id)
            station_reports.append(self._compare_row(row, result, thresholds))

        summary = self._summarize(station_reports)
        report = {
            "project_id": project_id,
            "validated_at": datetime.now().isoformat(timespec="seconds"),
            "thresholds": {
                "action_count_tolerance": thresholds.action_count_tolerance,
                "cycle_time_tolerance_pct": thresholds.cycle_time_tolerance_pct,
                "wait_time_tolerance_pct": thresholds.wait_time_tolerance_pct,
            },
            "summary": summary,
            "stations": station_reports,
        }

        write_json(paths.exports / "validation_report.json", report)
        self._write_validation_csv(paths.exports / "validation_report.csv", station_reports)
        return report

    def _read_ground_truth(self, path: str | Path) -> list[dict[str, str]]:
        with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
            return list(csv.DictReader(file))

    def _compare_row(
        self,
        row: dict[str, str],
        result: dict[str, Any] | None,
        thresholds: ValidationThresholds,
    ) -> dict[str, Any]:
        station_id = row.get("station_id", "")
        station_name = row.get("station_name", "")
        if result is None:
            return {
                "station_id": station_id,
                "station_name": station_name,
                "status": "missing_prediction",
                "passed": False,
                "message": "No analyzer result found for this station.",
            }

        metrics = result.get("cycle_time_metrics", {})
        mtm = result.get("mtm_summary", {})
        predicted_cycle = _to_float(metrics.get("total_cycle_time"))
        predicted_wait = _to_float(metrics.get("wait_time"))
        predicted_actions = _to_float(mtm.get("action_count"))
        truth_cycle = _to_float(row.get("ground_truth_cycle_time"))
        truth_wait = _to_float(row.get("ground_truth_wait_time"))
        truth_actions = _to_float(row.get("ground_truth_action_count"))

        cycle = _metric_report(predicted_cycle, truth_cycle, thresholds.cycle_time_tolerance_pct, "pct")
        wait = _metric_report(predicted_wait, truth_wait, thresholds.wait_time_tolerance_pct, "pct")
        actions = _metric_report(predicted_actions, truth_actions, thresholds.action_count_tolerance, "abs")

        available_checks = [item for item in (cycle, wait, actions) if item["labeled"]]
        passed = bool(available_checks) and all(item["passed"] for item in available_checks)
        return {
            "station_id": station_id,
            "station_name": station_name,
            "status": "validated" if available_checks else "no_ground_truth",
            "passed": passed,
            "cycle_time": cycle,
            "wait_time": wait,
            "action_count": actions,
            "labeler": row.get("labeler", ""),
            "notes": row.get("notes", ""),
        }

    def _summarize(self, station_reports: list[dict[str, Any]]) -> dict[str, Any]:
        validated = [row for row in station_reports if row.get("status") == "validated"]
        passed = [row for row in validated if row.get("passed")]

        def avg_accuracy(metric_name: str) -> float | None:
            values = [
                row[metric_name]["accuracy_pct"]
                for row in validated
                if row.get(metric_name, {}).get("labeled")
            ]
            if not values:
                return None
            return round(sum(values) / len(values), 1)

        return {
            "station_count": len(station_reports),
            "validated_station_count": len(validated),
            "pass_rate_pct": round(len(passed) / len(validated) * 100, 1) if validated else 0.0,
            # 动作数是判断"是否真识别"的核心指标，放在最前。
            "action_count_accuracy_pct": avg_accuracy("action_count"),
            "wait_time_accuracy_pct": avg_accuracy("wait_time"),
            "cycle_time_accuracy_pct": avg_accuracy("cycle_time"),
            "cycle_time_note": (
                "节拍准确率为弱证据：系统节拍≈视频时长，人工秒表也按同一段时长测，"
                "天然偏高。判断是否真识别请以动作数准确率为准。"
            ),
        }

    def _write_validation_csv(self, path: Path, station_reports: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "station_id",
            "station_name",
            "status",
            "passed",
            "cycle_error",
            "cycle_accuracy_pct",
            "wait_error",
            "wait_accuracy_pct",
            "action_error",
            "action_accuracy_pct",
        ]
        with path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in station_reports:
                writer.writerow(
                    {
                        "station_id": row.get("station_id"),
                        "station_name": row.get("station_name"),
                        "status": row.get("status"),
                        "passed": row.get("passed"),
                        "cycle_error": row.get("cycle_time", {}).get("error"),
                        "cycle_accuracy_pct": row.get("cycle_time", {}).get("accuracy_pct"),
                        "wait_error": row.get("wait_time", {}).get("error"),
                        "wait_accuracy_pct": row.get("wait_time", {}).get("accuracy_pct"),
                        "action_error": row.get("action_count", {}).get("error"),
                        "action_accuracy_pct": row.get("action_count", {}).get("accuracy_pct"),
                    }
                )


def _to_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _metric_report(
    predicted: float | None,
    truth: float | None,
    tolerance: float,
    tolerance_mode: str,
) -> dict[str, Any]:
    if predicted is None or truth is None:
        return {
            "labeled": False,
            "predicted": predicted,
            "ground_truth": truth,
            "error": None,
            "accuracy_pct": None,
            "passed": False,
        }
    error = abs(predicted - truth)
    if tolerance_mode == "pct":
        tolerance_value = abs(truth) * tolerance / 100 if truth else tolerance
    else:
        tolerance_value = tolerance
    accuracy = 100.0 if truth == 0 and predicted == 0 else max(0.0, 100.0 * (1 - error / max(abs(truth), 1e-9)))
    return {
        "labeled": True,
        "predicted": round(predicted, 2),
        "ground_truth": round(truth, 2),
        "error": round(error, 2),
        "accuracy_pct": round(accuracy, 1),
        "passed": error <= tolerance_value,
    }
